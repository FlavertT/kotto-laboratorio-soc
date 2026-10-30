"""Se ejecuta exclusivamente desde run-isolated.sh dentro del namespace de red."""
import argparse
import json
import os
import secrets
import signal
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.utils import timezone
from lab.client import Client
from datetime import timedelta
from soc.models import ChangeAuthorization, Case, Experiment, Refrigerator, TimelineEvent
from soc.services import ingest
from django.core.management import call_command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--within-range', action='store_true')
    parser.add_argument('--no-defense', action='store_true')
    args = parser.parse_args()
    # Refuse host networking: namespace must have loopback only and no default route.
    links = json.loads(subprocess.check_output(['ip', '-j', 'link']))
    if {entry['ifname'] for entry in links} != {'lo'} or subprocess.check_output(['ip', 'route', 'show', 'default']).strip():
        raise RuntimeError('Este experimento requiere una red aislada con solo loopback')
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    credentials = {name: dict(password=secrets.token_urlsafe(24), role=role) for name, role in [('admin', 'operator'), ('maintenance', 'operator'), ('soc', 'soc')]}
    credentials_path = output / 'credentials.json'
    credentials_path.write_text(json.dumps(credentials))
    credentials_path.chmod(0o600)
    actor, created = get_user_model().objects.get_or_create(username='soc-monitor', defaults=dict(is_staff=False))
    if created:
        actor.set_unusable_password()
        actor.save()
    call_command('setup_soc_roles')
    from django.contrib.auth.models import Group
    actor.groups.add(Group.objects.get(name='SOC · Respuesta'))
    case = Case.objects.create(title=f'Experimento seed={args.seed}, defensa={not args.no_defense}')
    refrigerator = Refrigerator.objects.create(code=f'LAB-{case.pk}', name='PLC simulado', location='Namespace aislado')
    experiment = Experiment.objects.create(case=case, refrigerator=refrigerator, seed=args.seed, defense=not args.no_defense)
    approver, new = get_user_model().objects.get_or_create(username='lab-approver')
    if new:
        approver.set_unusable_password()
        approver.save()
    approver.groups.add(Group.objects.get(name='SOC · Aprobación'))
    ChangeAuthorization.objects.create(experiment=experiment, username='admin', setpoint=4, defrost_minutes=20, valid_from=timezone.now(), valid_until=timezone.now()+timedelta(minutes=5), approved_by=approver)
    python = sys.executable
    processes = []
    handles = []
    capture = None
    monitor = None
    experiment.status = 'failed'  # Solo se marca completo tras preservar y generar informe.
    experiment.save(update_fields=['status'])
    try:
        errors = (output / 'tcpdump.log').open('w')
        handles.append(errors)
        capture = subprocess.Popen(['tcpdump', '-Z', 'root', '-i', 'lo', '-G', '15', '-W', '1', '-U', '-s', '0', '-w', str(output / 'traffic.pcap'), 'host', '127.0.0.20', 'and', 'tcp', 'port', '8001'], stdout=errors, stderr=errors)
        processes.append(capture)
        for _ in range(30):
            if capture.poll() is not None:
                raise RuntimeError('Falló tcpdump; revisar tcpdump.log')
            if 'listening on' in (output / 'tcpdump.log').read_text():
                break
            time.sleep(.1)
        else:
            raise RuntimeError('La captura no inició')
        plc_log = (output / 'plc-process.log').open('w')
        handles.append(plc_log)
        plc = subprocess.Popen([python, '-m', 'lab.plc', '--credentials', str(credentials_path), '--journal', str(output / 'controller.jsonl')], stdout=plc_log, stderr=plc_log)
        processes.append(plc)
        for _ in range(30):
            try:
                Client().call('/state')
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('PLC no disponible')
        monitor_log = (output / 'monitor.log').open('w')
        handles.append(monitor_log)
        monitor = subprocess.Popen([python, 'manage.py', 'monitor_plc', '--experiment', str(experiment.pk), '--credentials', str(credentials_path), '--actor', actor.username, '--seconds', '18'], stdout=monitor_log, stderr=monitor_log)
        processes.append(monitor)
        time.sleep(2)
        results = {}
        for role in ('admin', 'attacker'):
            raw = subprocess.check_output([python, '-m', 'lab.station', role, '--credentials', str(credentials_path), '--seed', str(args.seed)] + (['--within-range'] if args.within_range else []), text=True)
            results[role] = json.loads(raw)
            time.sleep(2)
        monitor.wait(timeout=25)
        if monitor.returncode:
            raise RuntimeError('Monitor falló; revisar monitor.log')
        client = Client()
        client.login('soc', credentials['soc']['password'])
        results['final_state'] = client.call('/state')[1]
        results['experiment'] = experiment.pk
        results['case'] = case.pk
        results['seed'] = args.seed
        results['defense'] = not args.no_defense
        results['network'] = {'plc': '127.0.0.20', 'admin': '127.0.0.11', 'attacker': '127.0.0.30', 'soc': '127.0.0.10', 'isolation': 'network namespace, loopback only'}
        (output / 'results.json').write_text(json.dumps(results, indent=2))
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                if process is capture:
                    process.wait(timeout=25)
                    continue
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        for handle in handles:
            handle.close()
    for name in ('controller.jsonl', 'traffic.pcap', 'results.json', 'tcpdump.log'):
        evidence = ingest(path=output / name, case=case, actor=actor, source='Laboratorio aislado: ' + name, collected_at=timezone.now())
        category = 'parameter_change' if name == 'controller.jsonl' else 'captura'
        if name == 'controller.jsonl':
            TimelineEvent.objects.filter(case=case, category=category).update(evidence=evidence)
        TimelineEvent.objects.create(case=case, occurred_at=timezone.now(), category='evidencia', description=f'Incorporado {name}; SHA-256 {evidence.sha256}', evidence=evidence)
    call_command('experiment_report', experiment=experiment.pk, output=str(output / 'report.md'))
    experiment.status = 'completed'
    experiment.save(update_fields=['status'])
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()

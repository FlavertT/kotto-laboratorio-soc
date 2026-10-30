from pathlib import Path
from django.core.management.base import BaseCommand
from soc.models import ChangeAuthorization, Experiment, Alert, Evidence, ResponseAction, Measurement, TimelineEvent
from soc.services import verify
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--experiment', required=True, type=int)
        parser.add_argument('--output', required=True)
    def handle(self, *args, **options):
        experiment = Experiment.objects.get(pk=options['experiment'])
        case = experiment.case
        measurements = Measurement.objects.filter(refrigerator=experiment.refrigerator).order_by('occurred_at')
        lines = [f'# Informe del experimento {experiment.pk}', '', f'Caso: {case.title}', f'Semilla: {experiment.seed}. Defensa automática: {experiment.defense}.', '', '## Alertas']
        for alert in Alert.objects.filter(case=case):
            from django.utils.dateparse import parse_datetime
            observed = parse_datetime(alert.details['observed']['timestamp'])
            latency = (alert.occurred_at - observed).total_seconds()
            lines.append(f'- {alert.occurred_at.isoformat()} · {alert.rule} · demora {latency:.3f} s')
        lines += ['', '## Autorizaciones de cambio']
        for approval in ChangeAuthorization.objects.filter(experiment=experiment):
            lines.append(f'- Cuenta {approval.username}; consigna {approval.setpoint}; minutos {approval.defrost_minutes}; ventana {approval.valid_from.isoformat()} a {approval.valid_until.isoformat()}; creada {approval.created_at.isoformat()}; aprobador {approval.approved_by}; evento consumido {approval.consumed_by_id}')
        lines += ['', '## Respuesta']
        for action in ResponseAction.objects.filter(event__experiment=experiment):
            lines.append(f'- {action.occurred_at.isoformat()} · {action.action} · éxito={action.success} · actor={action.actor.username}')
        lines += ['', '## Telemetría', '', '| UTC | Temperatura °C | Consigna °C |', '|---|---:|---:|']
        for measurement in measurements:
            lines.append(f'| {measurement.occurred_at.isoformat()} | {measurement.temperature} | {measurement.setpoint} |')
        lines += ['', '## Evidencias']
        for evidence in Evidence.objects.filter(case=case):
            try:
                intact = verify(evidence)
            except OSError:
                intact = False
            lines.append(f'- {evidence.original_name}: SHA-256 `{evidence.sha256}`; íntegra={intact}')
        lines += ['', '## Línea temporal']
        for event in TimelineEvent.objects.filter(case=case):
            lines.append(f'- {event.occurred_at.isoformat()} · {event.category} · {event.description}')
        lines += ['', '## Límites', 'PLC y modelo térmico simulados. La regla compara cuenta, valores y hora con una aprobación previa de un solo uso, y comprueba rangos operativos. No identifica a la persona detrás de una cuenta comprometida. HTTP en red aislada: el PCAP contiene credenciales efímeras y no debe publicarse sin anonimizar. Semilla reproduce parámetros, no tiempos de ejecución ni paquetes idénticos. Restaurar parámetros no demuestra por sí solo recuperación térmica; revisar mediciones.']
        Path(options['output']).write_text('\n'.join(lines) + '\n')
        self.stdout.write(options['output'])

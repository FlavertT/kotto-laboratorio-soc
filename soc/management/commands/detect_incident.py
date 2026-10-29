import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware
from soc.models import Case, Alert, TimelineEvent
class Command(BaseCommand):
    help = 'Registra alertas SOC desde cambios no autorizados de la simulación'
    def add_arguments(self, parser):
        parser.add_argument('path')
        parser.add_argument('--case', required=True, type=int)
    @transaction.atomic
    def handle(self, *args, **options):
        try:
            case = Case.objects.get(pk=options['case'])
            count = 0
            with open(options['path']) as stream:
                for line in stream:
                    event = json.loads(line)
                    if event.get('event') == 'parameter_change' and event.get('authorized') is False:
                        timestamp = parse_datetime(event['timestamp'])
                        if timestamp is None or not is_aware(timestamp):
                            raise ValueError('Fecha sin zona horaria')
                        alert, created = Alert.objects.get_or_create(case=case, occurred_at=timestamp, rule='Cambio no autorizado de parámetros', details=event)
                        if created:
                            TimelineEvent.objects.create(case=case, occurred_at=timestamp, category='detección', description=json.dumps(event, ensure_ascii=False))
                            count += 1
        except (OSError, ValueError, KeyError, Case.DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'{count} alertas nuevas')

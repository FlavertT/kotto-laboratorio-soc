import json
import time
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from lab.client import Client
from soc.models import Experiment
from soc.monitor import poll
class Command(BaseCommand):
    help = 'Monitorea el PLC cada segundo; Ctrl+C detiene el monitor'
    def add_arguments(self, parser):
        parser.add_argument('--experiment', type=int, required=True)
        parser.add_argument('--credentials', required=True)
        parser.add_argument('--actor', required=True)
        parser.add_argument('--seconds', type=int, default=0)
    def handle(self, *args, **options):
        credentials = json.loads(Path(options['credentials']).read_text())
        client = Client()
        client.login('soc', credentials['soc']['password'])
        experiment = Experiment.objects.get(pk=options['experiment'])
        actor = get_user_model().objects.get(username=options['actor'])
        if not actor.has_perm('soc.add_responseaction'):
            raise PermissionError('El actor no tiene permisos de respuesta SOC')
        deadline = time.monotonic() + options['seconds'] if options['seconds'] else float('inf')
        while time.monotonic() < deadline:
            poll(client, experiment, actor)
            time.sleep(1)

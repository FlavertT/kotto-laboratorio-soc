import tempfile
from pathlib import Path
from io import StringIO
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from soc.models import Case, Alert, CustodyEvent, TimelineEvent
from soc.services import ingest, verify
from simulator.controller import run

class LabTests(TestCase):
    def setUp(self):
        self.case = Case.objects.create(title='KOTTO')
        self.user = get_user_model().objects.create_user(username='analista')

    def test_evidence_copy_and_tampering(self):
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder + '/media'):
            source = Path(folder) / 'log.txt'
            source.write_bytes(b'original')
            evidence = ingest(path=source, case=self.case, actor=self.user, source='controlador', collected_at=timezone.now())
            source.write_bytes(b'changed source')
            self.assertTrue(verify(evidence))
            self.assertEqual(CustodyEvent.objects.filter(evidence=evidence).count(), 1)
            Path(evidence.file.path).write_bytes(b'tampered')
            self.assertFalse(verify(evidence))

    def test_normal_and_incident_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            for incident in (False, True):
                output = Path(folder) / str(incident)
                run(output, incident)
                for _ in range(2):
                    call_command('detect_incident', str(output / 'controller.jsonl'), case=self.case.pk, stdout=StringIO())
                self.assertEqual(Alert.objects.count(), int(incident))
            self.assertEqual(TimelineEvent.objects.count(), 1)

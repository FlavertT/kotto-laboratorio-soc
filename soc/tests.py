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

class MonitorTests(TestCase):
    def test_policy_detection_is_not_attack_flag(self):
        from soc.models import Experiment, Refrigerator, ResponseAction
        from soc.monitor import poll
        actor = get_user_model().objects.create_superuser(username='monitor-test', password='test-only')
        experiment = Experiment.objects.create(case=Case.objects.create(title='Prueba'), refrigerator=Refrigerator.objects.create(code='T', name='Test', location='Test'), seed=42)
        class FakeClient:
            def __init__(self): self.routes = []
            def call(self, route, data=None):
                self.routes.append(route)
                if route == '/events':
                    return 200, {'events': [{'id': 1, 'timestamp': timezone.now().isoformat(), 'kind': 'parameter_change', 'before': {'setpoint': 3, 'defrost_minutes': 20}, 'after': {'setpoint': 12, 'defrost_minutes': 60}, 'session': 'test-session'}]}
                if route == '/state':
                    return 200, {'timestamp': timezone.now().isoformat(), 'temperature': 3.2, 'setpoint': 3}
                return 200, {'result': 'OK'}
        client = FakeClient()
        poll(client, experiment, actor)
        poll(client, experiment, actor)
        self.assertEqual(Alert.objects.count(), 1)
        self.assertEqual(ResponseAction.objects.count(), 2)
        self.assertEqual(client.routes.count('/contain'), 1)
        self.assertEqual(client.routes.count('/recover'), 1)

    def test_report_requires_permissions(self):
        from soc.models import Experiment, Refrigerator
        from django.contrib.auth.models import Group
        experiment = Experiment.objects.create(case=Case.objects.create(title='Prueba'), refrigerator=Refrigerator.objects.create(code='T', name='Test', location='Test'), seed=42)
        user = get_user_model().objects.create_user(username='viewer')
        self.client.force_login(user)
        url = f'/experiments/{experiment.pk}/report/'
        self.assertEqual(self.client.get(url).status_code, 403)
        call_command('setup_soc_roles', stdout=StringIO())
        user.groups.add(Group.objects.get(name='SOC · Consulta'))
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(user.has_perm('soc.add_responseaction'))

class AuthorizationTests(TestCase):
    def setUp(self):
        from soc.models import Experiment, Refrigerator, ChangeAuthorization
        from datetime import timedelta
        self.actor = get_user_model().objects.create_superuser(username='approval-test', password='test-only')
        self.exp = Experiment.objects.create(case=Case.objects.create(title='Autorizaciones'), refrigerator=Refrigerator.objects.create(code='AUTH', name='Test', location='Test'), seed=42)
        self.approval = ChangeAuthorization.objects.create(experiment=self.exp, username='admin', setpoint=4, defrost_minutes=20, valid_from=timezone.now()-timedelta(minutes=1), valid_until=timezone.now()+timedelta(minutes=1), approved_by=self.actor)

    def event(self, sequence=1, username='admin', setpoint=4):
        from soc.models import ControllerEvent
        return ControllerEvent.objects.create(experiment=self.exp, sequence=sequence, occurred_at=timezone.now(), kind='parameter_change', payload={'username': username, 'after': {'setpoint': setpoint, 'defrost_minutes': 20}})

    def test_valid_then_reused(self):
        from soc.authorization import authorize_event
        self.assertEqual(authorize_event(self.event()), self.approval.pk)
        self.assertIsNone(authorize_event(self.event(2)))

    def test_wrong_identity_or_value(self):
        from soc.authorization import authorize_event
        self.assertIsNone(authorize_event(self.event(username='maintenance')))
        self.assertIsNone(authorize_event(self.event(2, setpoint=5)))
        self.approval.refresh_from_db()
        self.assertIsNone(self.approval.consumed_by)

    def test_expired_and_future(self):
        from soc.authorization import authorize_event
        from datetime import timedelta
        event = self.event()
        event.occurred_at = self.approval.valid_until + timedelta(seconds=1)
        self.assertIsNone(authorize_event(event))
        event.occurred_at = self.approval.valid_from - timedelta(seconds=1)
        self.assertIsNone(authorize_event(event))

    def test_retroactive_approval_rejected(self):
        from soc.authorization import authorize_event
        from datetime import timedelta
        event = self.event()
        event.occurred_at = self.approval.created_at - timedelta(seconds=1)
        self.assertIsNone(authorize_event(event))

    def test_monitor_legitimate_and_in_range_unauthorized(self):
        from soc.monitor import poll
        from soc.models import ResponseAction, ParameterChange
        experiment = self.exp
        class Fake:
            def __init__(self): self.events = []; self.responses = []
            def call(self, route, data=None):
                if route == '/events': return 200, {'events': self.events}
                if route == '/state': return 200, {'timestamp': timezone.now().isoformat(), 'temperature': 3, 'setpoint': 3}
                self.responses.append(route)
                return 200, {'result': 'OK'}
        fake = Fake()
        fake.events = [{'id':1, 'timestamp':timezone.now().isoformat(), 'kind':'parameter_change', 'username':'admin', 'session':'a', 'before':{'setpoint':3,'defrost_minutes':20}, 'after':{'setpoint':4,'defrost_minutes':20}}]
        poll(fake, experiment, self.actor)
        self.assertEqual(Alert.objects.count(), 0)
        self.assertEqual(ParameterChange.objects.get().authorization, 'authorized')
        fake.events.append({'id':2, 'timestamp':timezone.now().isoformat(), 'kind':'parameter_change', 'username':'maintenance', 'session':'b', 'before':{'setpoint':4,'defrost_minutes':20}, 'after':{'setpoint':5,'defrost_minutes':20}})
        poll(fake, experiment, self.actor)
        self.assertEqual(Alert.objects.get().rule, 'Cambio sin autorización')
        self.assertFalse(Alert.objects.get().details['outside_policy'])
        self.assertEqual(ResponseAction.objects.count(), 2)

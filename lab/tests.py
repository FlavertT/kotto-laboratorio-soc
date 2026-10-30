import tempfile
import time
from pathlib import Path
from django.test import SimpleTestCase
from lab.plc import PLC

class ControllerTests(SimpleTestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.plc = PLC({'operator': {'password': 'example-test-only', 'role': 'operator'}, 'soc': {'password': 'soc-test-only', 'role': 'soc'}}, Path(self.folder.name) / 'log.jsonl')
        self.operator = self.plc.request('/login', {'username': 'operator', 'password': 'example-test-only'}, '', '127.0.0.30')[1]
        self.soc = self.plc.request('/login', {'username': 'soc', 'password': 'soc-test-only'}, '', '127.0.0.10')[1]

    def request(self, route, data, role='operator'):
        return self.plc.request(route, data, getattr(self, role)['token'], '127.0.0.30')

    def test_authentication_and_roles(self):
        self.assertEqual(self.plc.request('/state', {}, '', '127.0.0.1')[0], 401)
        self.assertEqual(self.request('/contain', {'session': self.operator['session']})[0], 403)
        self.assertEqual(self.request('/parameters', {'setpoint': 4}, 'soc')[0], 403)
        for session in self.plc.sessions.values(): session['expires'] = time.time() - 1
        self.assertEqual(self.request('/state', {})[0], 401)

    def test_containment_revokes_and_recovery_preserves_lock(self):
        self.assertEqual(self.request('/parameters', {'setpoint': 12, 'defrost_minutes': 60})[0], 200)
        self.assertEqual(self.request('/contain', {'session': self.operator['session']}, 'soc')[0], 200)
        self.assertEqual(self.request('/parameters', {'setpoint': 15})[0], 401)
        self.assertEqual(self.plc.request('/login', {'username': 'operator', 'password': 'example-test-only'}, '', '127.0.0.30')[0], 403)
        self.assertEqual(self.request('/recover', {}, 'soc')[0], 200)
        self.assertEqual(self.plc.setpoint, 3)
        self.assertTrue(self.plc.remote_locked)

    def test_reject_invalid_values_without_partial_write(self):
        for data in ({'setpoint': float('nan')}, {'setpoint': 4, 'defrost_minutes': -1}, {'setpoint': True}):
            self.assertEqual(self.request('/parameters', data)[0], 400)
            self.assertEqual(self.plc.setpoint, 3)

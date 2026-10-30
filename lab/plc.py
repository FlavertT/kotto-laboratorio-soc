"""PLC de maqueta. HTTP solamente dentro de una red de laboratorio aislada."""
import argparse
import hashlib
import hmac
import json
import math
import secrets
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def utc():
    return datetime.now(timezone.utc).isoformat()


class PLC:
    def __init__(self, credentials, journal):
        self.credentials = credentials
        self.journal = Path(journal)
        self.lock = threading.RLock()
        self.sessions = {}
        self.blocked_users = set()
        self.events = []
        self.setpoint = 3.0
        self.defrost_minutes = 20
        self.temperature = 3.0
        self.remote_locked = False
        self.last_tick = time.monotonic()

    def record(self, kind, **data):
        event = dict(id=len(self.events) + 1, timestamp=utc(), kind=kind, **data)
        self.events.append(event)
        with self.journal.open('a') as stream:
            stream.write(json.dumps(event) + '\n')
        return event

    def tick(self):
        elapsed = time.monotonic() - self.last_tick
        target = self.setpoint + max(0, self.defrost_minutes - 20) * 0.05
        self.temperature += (target - self.temperature) * (1 - math.exp(-elapsed / 10))
        self.last_tick = time.monotonic()

    def request(self, route, data, token, ip):
        with self.lock:
            self.tick()
            if route == '/login':
                username = data.get('username', '')
                account = self.credentials.get(username)
                password = data.get('password', '')
                if not isinstance(password, str) or not account or not hmac.compare_digest(account['password'], password) or username in self.blocked_users:
                    self.record('login_denied', username=username, ip=ip)
                    return 403, {'error': 'Acceso rechazado'}
                token = secrets.token_urlsafe(32)
                session = dict(id=secrets.token_hex(8), username=username, role=account['role'], expires=time.time() + 900)
                self.sessions[hashlib.sha256(token.encode()).hexdigest()] = session
                self.record('login', session=session['id'], username=username, role=session['role'], ip=ip)
                return 200, {'token': token, 'session': session['id']}
            session = self.sessions.get(hashlib.sha256(token.encode()).hexdigest())
            if not session or session['expires'] <= time.time() or session['username'] in self.blocked_users:
                self.record('access_denied', ip=ip, route=route)
                return 401, {'error': 'Sesión inválida, expirada o revocada'}
            context = dict(session=session['id'], username=session['username'], ip=ip)
            if route == '/state':
                return 200, dict(timestamp=utc(), temperature=round(self.temperature, 3), setpoint=self.setpoint, defrost_minutes=self.defrost_minutes, remote_locked=self.remote_locked)
            if route == '/events':
                if session['role'] != 'soc':
                    return 403, {'error': 'Requiere rol SOC'}
                return 200, {'events': self.events}
            if route == '/parameters':
                if session['role'] != 'operator' or self.remote_locked:
                    self.record('change_denied', **context)
                    return 403, {'error': 'Modificación bloqueada'}
                if not data or set(data) - {'setpoint', 'defrost_minutes'}:
                    return 400, {'error': 'Parámetros inválidos'}
                for key, value in data.items():
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                        return 400, {'error': 'Valor numérico finito requerido'}
                    if key == 'setpoint' and not -30 <= value <= 30:
                        return 400, {'error': 'Fuera de límites de la maqueta'}
                    if key == 'defrost_minutes' and (not 0 <= value <= 120 or int(value) != value):
                        return 400, {'error': 'Minutos enteros entre 0 y 120'}
                before = dict(setpoint=self.setpoint, defrost_minutes=self.defrost_minutes)
                for key, value in data.items():
                    setattr(self, key, value)
                self.record('parameter_change', before=before, after=dict(setpoint=self.setpoint, defrost_minutes=self.defrost_minutes), **context)
                return 200, {'result': 'Cambio aplicado'}
            if route in ('/contain', '/recover'):
                if session['role'] != 'soc':
                    return 403, {'error': 'Requiere rol SOC'}
                if route == '/contain':
                    target = data.get('session')
                    victims = [s for s in self.sessions.values() if s['id'] == target and s['role'] == 'operator']
                    if not victims:
                        return 400, {'error': 'Sesión operativa inexistente'}
                    self.blocked_users.update(s['username'] for s in victims)
                    self.remote_locked = True
                    self.record('containment', target_session=target, **context)
                else:
                    before = dict(setpoint=self.setpoint, defrost_minutes=self.defrost_minutes)
                    self.setpoint, self.defrost_minutes = 3.0, 20
                    self.record('recovery', before=before, after=dict(setpoint=3.0, defrost_minutes=20), **context)
                return 200, {'result': 'OK', 'remote_locked': self.remote_locked}
            return 404, {'error': 'Ruta inexistente'}


def serve(host, port, credentials, journal):
    plc = PLC(credentials, journal)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 <= size <= 4096:
                    raise ValueError('Tamaño inválido')
                data = json.loads(self.rfile.read(size) or b'{}')
                if not isinstance(data, dict):
                    raise ValueError('Objeto requerido')
                code, result = plc.request(self.path, data, self.headers.get('Authorization', '').removeprefix('Bearer '), self.client_address[0])
            except (ValueError, TypeError):
                code, result = 400, {'error': 'Solicitud inválida'}
            body = json.dumps(result).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.20')
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--credentials', required=True)
    parser.add_argument('--journal', required=True)
    args = parser.parse_args()
    serve(args.host, args.port, json.loads(Path(args.credentials).read_text()), args.journal)

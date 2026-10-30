import http.client
import json

class Client:
    def __init__(self, source='127.0.0.10', host='127.0.0.20', port=8001):
        self.source, self.host, self.port = source, host, port
        self.token = ''

    def call(self, route, data=None):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5, source_address=(self.source, 0))
        try:
            connection.request('POST', route, json.dumps(data or {}), {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token})
            response = connection.getresponse()
            result = json.loads(response.read())
            return response.status, result
        finally:
            connection.close()

    def login(self, username, password):
        status, result = self.call('/login', dict(username=username, password=password))
        if status != 200:
            raise RuntimeError(f'Acceso rechazado: {status}')
        self.token = result['token']
        return result['session']

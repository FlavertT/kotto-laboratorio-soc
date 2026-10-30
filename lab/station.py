import argparse
import json
import random
import time
from pathlib import Path
from .client import Client

def run(role, credentials, seed, within_range=False):
    client = Client(source='127.0.0.30' if role == 'attacker' else '127.0.0.11')
    username = 'maintenance' if role == 'attacker' else 'admin'
    session = client.login(username, credentials[username]['password'])
    randomizer = random.Random(seed)
    parameters = dict(setpoint=randomizer.choice([10, 12, 15]), defrost_minutes=randomizer.choice([45, 60, 90])) if role == 'attacker' else dict(setpoint=4, defrost_minutes=20)
    if role == 'attacker' and within_range:
        parameters = dict(setpoint=5, defrost_minutes=25)
    code, result = client.call('/parameters', parameters)
    output = dict(role=role, session=session, first_status=code, parameters=parameters, result=result)
    if role == 'attacker':
        time.sleep(3)
        output['retry_status'] = client.call('/parameters', parameters)[0]
        output['relogin_status'] = client.call('/login', dict(username=username, password=credentials[username]['password']))[0]
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('role', choices=['admin', 'attacker'])
    parser.add_argument('--credentials', required=True)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--within-range', action='store_true')
    options = parser.parse_args()
    print(json.dumps(run(options.role, json.loads(Path(options.credentials).read_text()), options.seed, options.within_range)))

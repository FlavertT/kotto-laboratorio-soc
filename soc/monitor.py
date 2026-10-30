from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .authorization import authorize_event
from .models import Alert, ControllerEvent, Measurement, ParameterChange, ResponseAction, TimelineEvent

def poll(client, experiment, actor):
    if experiment.defense and not actor.has_perm('soc.add_responseaction'):
        raise PermissionError('Actor sin permiso de respuesta SOC')
    status, result = client.call('/events')
    if status != 200:
        raise RuntimeError('No se pudieron leer eventos del PLC')
    for payload in result['events']:
        event, created = ControllerEvent.objects.get_or_create(experiment=experiment, sequence=payload['id'], defaults=dict(occurred_at=parse_datetime(payload['timestamp']), kind=payload['kind'], payload=payload))
        if not created:
            continue
        TimelineEvent.objects.create(case=experiment.case, occurred_at=event.occurred_at, category=event.kind, description=str(payload))
        if event.kind != 'parameter_change':
            continue
        after = payload['after']
        approval = authorize_event(event)
        outside_policy = not (2 <= after['setpoint'] <= 5 and 0 <= after['defrost_minutes'] <= 30)
        suspicious = approval is None or outside_policy
        for parameter in ('setpoint', 'defrost_minutes'):
            if payload['before'][parameter] != after[parameter]:
                ParameterChange.objects.create(refrigerator=experiment.refrigerator, occurred_at=event.occurred_at, parameter=parameter, previous_value=payload['before'][parameter], new_value=after[parameter], session=payload['session'], recorded_by=actor, authorization='authorized' if approval else 'unauthorized', notes=f'Autorización: {approval}; fuera de política: {outside_policy}')
        if suspicious:
            Alert.objects.create(case=experiment.case, occurred_at=timezone.now(), rule='Cambio sin autorización' if approval is None else 'Cambio fuera de política operativa', details=dict(authorization=approval, outside_policy=outside_policy, controller_event=event.pk, observed=payload, policy={'setpoint': [2, 5], 'defrost_minutes': [0, 30]}))
            if experiment.defense:
                for route in ('/contain', '/recover'):
                    code, response = client.call(route, {'session': payload['session']})
                    ResponseAction.objects.create(event=event, actor=actor, action=route[1:], success=code == 200, details=dict(status=code, response=response))
                    TimelineEvent.objects.create(case=experiment.case, occurred_at=timezone.now(), category='respuesta', description=f'{route}: HTTP {code}, {response}')
                    if code != 200:
                        break
                    if route == '/contain':
                        experiment.case.status = 'contained'
                        experiment.case.save(update_fields=['status'])
    code, state = client.call('/state')
    if code != 200:
        raise RuntimeError('Sin telemetría del PLC')
    Measurement.objects.create(refrigerator=experiment.refrigerator, occurred_at=parse_datetime(state['timestamp']), temperature=state['temperature'], setpoint=state['setpoint'], defrost_active=False)
    return state

from django.db import transaction
from .models import ChangeAuthorization

@transaction.atomic
def authorize_event(event):
    payload = event.payload
    after = payload['after']
    candidate = ChangeAuthorization.objects.filter(
        experiment=event.experiment, username=payload.get('username', ''),
        setpoint=after['setpoint'], defrost_minutes=after['defrost_minutes'],
        valid_from__lte=event.occurred_at, valid_until__gte=event.occurred_at,
        created_at__lte=event.occurred_at, consumed_by__isnull=True,
    ).order_by('valid_until', 'pk').first()
    if candidate and ChangeAuthorization.objects.filter(pk=candidate.pk, consumed_by__isnull=True).update(consumed_by=event):
        return candidate.pk
    return None

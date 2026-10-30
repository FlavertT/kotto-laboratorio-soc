from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
class Command(BaseCommand):
    help = 'Configura roles de consulta y respuesta sin crear contraseñas'
    def handle(self, *args, **options):
        views = Permission.objects.filter(content_type__app_label='soc', codename__startswith='view_')
        reader, _ = Group.objects.get_or_create(name='SOC · Consulta')
        reader.permissions.set(views)
        analyst, _ = Group.objects.get_or_create(name='SOC · Respuesta')
        analyst.permissions.set(views)
        analyst.permissions.add(*Permission.objects.filter(content_type__app_label='soc', codename__in=['add_responseaction', 'add_case', 'change_case', 'add_custodyevent', 'add_timelineevent']))
        approver, _ = Group.objects.get_or_create(name='SOC · Aprobación')
        approver.permissions.set(views)
        approver.permissions.add(Permission.objects.get(content_type__app_label='soc', codename='add_changeauthorization'))
        self.stdout.write('Roles SOC configurados. Asignar usuarios desde el administrador.')

from django.core.management.base import BaseCommand, CommandError
from soc.models import Evidence
from soc.services import verify
class Command(BaseCommand):
    help = "Verifica todas las copias preservadas"
    def handle(self, *args, **options):
        failed = 0
        for evidence in Evidence.objects.all():
            try:
                valid = verify(evidence)
            except OSError:
                valid = False
            self.stdout.write(f"{'OK' if valid else 'ERROR'} {evidence.pk} {evidence.original_name}")
            failed += not valid
        if failed: raise CommandError(f"{failed} evidencias fallaron")

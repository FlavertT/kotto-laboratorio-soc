from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware
from soc.models import Case
from soc.services import ingest
class Command(BaseCommand):
    help = "Preserva un archivo y registra su SHA-256 y custodia inicial"
    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--case", type=int, required=True)
        parser.add_argument("--user", required=True)
        parser.add_argument("--source", required=True)
        parser.add_argument("--collected-at", required=True, help="ISO 8601 con zona horaria")
    def handle(self, *args, **options):
        date = parse_datetime(options["collected_at"])
        if date is None or not is_aware(date):
            raise CommandError("Usar fecha ISO 8601 con zona, por ejemplo 2026-10-28T16:00:00Z")
        try:
            evidence = ingest(path=options["path"], case=Case.objects.get(pk=options["case"]), actor=get_user_model().objects.get(username=options["user"]), source=options["source"], collected_at=date)
        except (OSError, Case.DoesNotExist, get_user_model().DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f"{evidence.pk} SHA-256={evidence.sha256}")

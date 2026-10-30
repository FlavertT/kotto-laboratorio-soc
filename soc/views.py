from pathlib import Path
from tempfile import TemporaryDirectory
from django.contrib.auth.decorators import permission_required
from django.core.management import call_command
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Experiment

@permission_required(('soc.view_experiment', 'soc.view_evidence', 'soc.view_controllerevent', 'soc.view_responseaction', 'soc.view_measurement'), raise_exception=True)
def experiment_report(request, pk):
    get_object_or_404(Experiment, pk=pk)
    with TemporaryDirectory() as folder:
        path = Path(folder) / 'report.md'
        call_command('experiment_report', experiment=pk, output=str(path))
        response = HttpResponse(path.read_text(), content_type='text/markdown; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="experimento-{pk}.md"'
    return response

import hashlib
from pathlib import Path
from django.core.files import File
from django.db import transaction
from .models import Evidence, CustodyEvent

def digest(stream):
    value = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        value.update(chunk)
    return value.hexdigest()

def ingest(*, path, case, actor, source, collected_at):
    path = Path(path)
    evidence = Evidence(case=case, original_name=path.name, source=source,
                        collected_by=actor, collected_at=collected_at)
    try:
        with path.open("rb") as stream:
            evidence.file.save(path.name, File(stream), save=False)
        with evidence.file.open("rb") as stored:
            evidence.sha256 = digest(stored)
        evidence.size = evidence.file.size
        with transaction.atomic():
            evidence.save()
            CustodyEvent.objects.create(evidence=evidence, actor=actor, action="Incorporación", notes="SHA-256 calculado sobre la copia preservada.")
    except Exception:
        if evidence.file.name:
            evidence.file.delete(save=False)
        raise
    return evidence

def verify(evidence):
    with evidence.file.open("rb") as stream:
        return digest(stream) == evidence.sha256

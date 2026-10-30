import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

class Case(models.Model):
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", blank=True)
    status = models.CharField(max_length=20, choices=[("open", "Abierto"), ("contained", "Contenido"), ("closed", "Cerrado")], default="open")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    def __str__(self): return f"{self.pk}: {self.title}"

class Alert(models.Model):
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    occurred_at = models.DateTimeField(default=timezone.now)
    rule = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    def __str__(self): return self.rule

class Evidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="evidence/%Y/%m/%d/")
    sha256 = models.CharField(max_length=64, editable=False)
    size = models.PositiveBigIntegerField(editable=False)
    source = models.CharField(max_length=255)
    collected_at = models.DateTimeField()
    collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    ingested_at = models.DateTimeField(default=timezone.now, editable=False)
    def __str__(self): return self.original_name

class CustodyEvent(models.Model):
    evidence = models.ForeignKey(Evidence, on_delete=models.PROTECT)
    recorded_at = models.DateTimeField(default=timezone.now, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=100)
    recipient = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

class TimelineEvent(models.Model):
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    occurred_at = models.DateTimeField()
    category = models.CharField(max_length=50)
    description = models.TextField()
    evidence = models.ForeignKey(Evidence, null=True, blank=True, on_delete=models.PROTECT)
    class Meta:
        ordering = ["occurred_at", "pk"]

class Refrigerator(models.Model):
    name = models.CharField('nombre', max_length=100)
    code = models.CharField('identificador', max_length=50, unique=True)
    location = models.CharField('ubicación', max_length=200)
    active = models.BooleanField('activa', default=True)

    class Meta:
        verbose_name = 'heladera'
        verbose_name_plural = 'heladeras'

    def __str__(self):
        return f'{self.code} · {self.name}'

class Measurement(models.Model):
    refrigerator = models.ForeignKey(Refrigerator, verbose_name='heladera', on_delete=models.PROTECT, related_name='measurements')
    occurred_at = models.DateTimeField('fecha y hora (UTC)', default=timezone.now)
    temperature = models.DecimalField('temperatura (°C)', max_digits=6, decimal_places=2)
    setpoint = models.DecimalField('consigna (°C)', max_digits=6, decimal_places=2)
    defrost_active = models.BooleanField('descongelamiento activo', default=False)

    class Meta:
        verbose_name = 'medición'
        verbose_name_plural = 'mediciones'
        ordering = ['-occurred_at', '-pk']
        indexes = [models.Index(fields=['refrigerator', 'occurred_at'])]

    def __str__(self):
        return f'{self.refrigerator} · {self.temperature} °C'

class ParameterChange(models.Model):
    refrigerator = models.ForeignKey(Refrigerator, verbose_name='heladera', on_delete=models.PROTECT, related_name='parameter_changes')
    occurred_at = models.DateTimeField('fecha y hora (UTC)', default=timezone.now)
    parameter = models.CharField('parámetro', max_length=30, choices=[('setpoint', 'Consigna (°C)'), ('defrost_minutes', 'Duración de descongelamiento (min)')])
    previous_value = models.DecimalField('valor anterior', max_digits=6, decimal_places=2)
    new_value = models.DecimalField('valor nuevo', max_digits=6, decimal_places=2)
    session = models.CharField('sesión de origen', max_length=200)
    authorization = models.CharField('autorización', max_length=15, default='unknown', choices=[('unknown', 'Por determinar'), ('authorized', 'Autorizado'), ('unauthorized', 'No autorizado')])
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='registrado por', on_delete=models.PROTECT)
    recorded_at = models.DateTimeField('fecha de registro', default=timezone.now, editable=False)
    notes = models.TextField('observaciones', blank=True)

    class Meta:
        verbose_name = 'cambio de parámetro'
        verbose_name_plural = 'cambios de parámetros'
        ordering = ['-occurred_at', '-pk']
        indexes = [models.Index(fields=['refrigerator', 'occurred_at'])]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.parameter == 'defrost_minutes':
            for field in ('previous_value', 'new_value'):
                value = getattr(self, field)
                if value is not None and (value < 0 or value != value.to_integral_value()):
                    raise ValidationError({field: 'La duración debe ser un número entero de minutos mayor o igual a cero.'})

    def __str__(self):
        return f'{self.refrigerator} · {self.get_parameter_display()}'

class Experiment(models.Model):
    status = models.CharField(max_length=16, default='running', choices=[('running', 'En curso'), ('completed', 'Completado'), ('failed', 'Fallido')])
    case = models.OneToOneField(Case, on_delete=models.PROTECT)
    refrigerator = models.ForeignKey(Refrigerator, on_delete=models.PROTECT)
    seed = models.PositiveIntegerField()
    defense = models.BooleanField(default=True)
    started_at = models.DateTimeField(default=timezone.now)
    class Meta:
        verbose_name = 'experimento'

class ControllerEvent(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.PROTECT)
    sequence = models.PositiveIntegerField()
    occurred_at = models.DateTimeField()
    kind = models.CharField(max_length=50)
    payload = models.JSONField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['experiment', 'sequence'], name='unique_experiment_sequence')]
        ordering = ['occurred_at', 'sequence']

class ResponseAction(models.Model):
    event = models.ForeignKey(ControllerEvent, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    occurred_at = models.DateTimeField(default=timezone.now)
    action = models.CharField(max_length=30)
    success = models.BooleanField()
    details = models.JSONField()
    class Meta:
        verbose_name = 'acción de respuesta'

class ChangeAuthorization(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.PROTECT)
    username = models.CharField('cuenta del PLC', max_length=100)
    setpoint = models.DecimalField('consigna aprobada', max_digits=6, decimal_places=2)
    defrost_minutes = models.PositiveIntegerField('minutos aprobados')
    valid_from = models.DateTimeField('válida desde')
    valid_until = models.DateTimeField('válida hasta')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    consumed_by = models.OneToOneField(ControllerEvent, null=True, blank=True, on_delete=models.PROTECT)
    class Meta:
        verbose_name = 'autorización de cambio'
        verbose_name_plural = 'autorizaciones de cambios'
        constraints = [models.CheckConstraint(condition=models.Q(valid_until__gt=models.F('valid_from')), name='authorization_valid_window')]
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValidationError('El vencimiento debe ser posterior al inicio.')

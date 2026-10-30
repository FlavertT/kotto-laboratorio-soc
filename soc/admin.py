from django.contrib import admin
from .models import Case, Alert, Evidence, CustodyEvent, TimelineEvent
admin.site.site_header = "KOTTO · SOC y laboratorio forense"
admin.site.register([Case, Alert, TimelineEvent])

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ["original_name", "case", "sha256", "ingested_at"]
    readonly_fields = [f.name for f in Evidence._meta.fields]
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(CustodyEvent)
class CustodyAdmin(admin.ModelAdmin):
    list_display = ["evidence", "recorded_at", "actor", "action"]
    readonly_fields = ["actor", "recorded_at"]
    def has_change_permission(self, request, obj=None): return obj is None
    def has_delete_permission(self, request, obj=None): return False
    def save_model(self, request, obj, form, change):
        obj.actor = request.user
        super().save_model(request, obj, form, change)

from .models import Refrigerator, Measurement, ParameterChange

@admin.register(Refrigerator)
class RefrigeratorAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'location', 'active']
    search_fields = ['code', 'name', 'location']
    list_filter = ['active']

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['refrigerator', 'occurred_at', 'temperature', 'setpoint', 'defrost_active']
    list_filter = ['refrigerator', 'defrost_active', 'occurred_at']
    search_fields = ['refrigerator__code', 'refrigerator__name']
    autocomplete_fields = ['refrigerator']
    date_hierarchy = 'occurred_at'

@admin.register(ParameterChange)
class ParameterChangeAdmin(admin.ModelAdmin):
    list_display = ['refrigerator', 'occurred_at', 'parameter', 'previous_value', 'new_value', 'authorization', 'recorded_by']
    list_filter = ['refrigerator', 'parameter', 'authorization', 'occurred_at']
    search_fields = ['refrigerator__code', 'session', 'notes']
    autocomplete_fields = ['refrigerator']
    readonly_fields = ['recorded_by', 'recorded_at']
    date_hierarchy = 'occurred_at'

    def has_change_permission(self, request, obj=None):
        return obj is None

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.recorded_by = request.user
        super().save_model(request, obj, form, change)

from .models import Experiment, ControllerEvent, ResponseAction

class ReadOnlyAuditAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(Experiment)
class ExperimentAdmin(ReadOnlyAuditAdmin):
    list_display = ['id', 'case', 'refrigerator', 'seed', 'defense', 'status', 'started_at', 'report_link']
    def report_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        return format_html('<a href="{}">Descargar informe</a>', reverse('experiment-report', args=[obj.pk]))
    report_link.short_description = 'Informe'

@admin.register(ControllerEvent)
class ControllerEventAdmin(ReadOnlyAuditAdmin):
    list_display = ['experiment', 'sequence', 'occurred_at', 'kind']
    list_filter = ['experiment', 'kind']

@admin.register(ResponseAction)
class ResponseActionAdmin(ReadOnlyAuditAdmin):
    list_display = ['event', 'occurred_at', 'actor', 'action', 'success']

from .models import ChangeAuthorization
@admin.register(ChangeAuthorization)
class ChangeAuthorizationAdmin(admin.ModelAdmin):
    list_display = ['experiment', 'username', 'setpoint', 'defrost_minutes', 'valid_until', 'approved_by', 'consumed_by']
    readonly_fields = ['approved_by', 'created_at', 'consumed_by']
    def has_change_permission(self, request, obj=None): return obj is None
    def has_delete_permission(self, request, obj=None): return False
    def save_model(self, request, obj, form, change):
        obj.approved_by = request.user
        super().save_model(request, obj, form, change)

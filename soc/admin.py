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

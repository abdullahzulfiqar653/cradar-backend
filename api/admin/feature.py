from django.contrib import admin
from api.models import Feature


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    ordering = ('name',)
    list_filter = ('unit',)
    readonly_fields = ['id']
    search_fields = ('id', 'name', 'code')
    list_display = ['name', 'unit', 'description', 'default']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


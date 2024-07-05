from django.contrib import admin
from api.models import ProductFeature


@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ('product', 'feature', 'value')
    search_fields = ('product__name', 'feature__name')
    list_filter = ('product', 'feature')
    autocomplete_fields = ('product', 'feature')

from django import forms
from django.contrib import admin
from api.models import ProductFeature


class ProductFeatureForm(forms.ModelForm):
    class Meta:
        model = ProductFeature
        fields = "__all__"
        widgets = {
            "value": forms.NumberInput(attrs={"required": False}),
        }


class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ("product", "feature", "value")
    search_fields = ("product__name", "feature__name")
    list_filter = ("product", "feature")
    autocomplete_fields = ("product", "feature")


admin.site.register(ProductFeature, ProductFeatureAdmin)

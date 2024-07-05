from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from api.models import StripeProduct
from api.stripe import stripe


@admin.register(StripeProduct)
class StripeProductAdmin(admin.ModelAdmin):
    readonly_fields = ["id", "name", "is_active", "created_at", "updated_at"]
    search_fields = ("id", "name")
    list_display = ["name", "usage_type", "is_active", "created_at", "updated_at"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync/",
                self.admin_site.admin_view(self.sync_now),
                name="stripeproduct_sync",
            ),
        ]
        return custom_urls + urls

    def sync_now(self, request):
        try:
            response = stripe.Product.list()
            for product_data in response.get("data", []):
                StripeProduct.update_or_create(product_data)
            messages.success(request, "Products have been synced with Stripe.")
        except Exception as e:
            messages.error(
                request, f"Something went wrong, please try again. Error: {e}"
            )
        return HttpResponseRedirect(reverse("admin:api_stripeproduct_changelist"))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        sync_url = reverse("admin:stripeproduct_sync")
        extra_context["sync_url"] = sync_url
        return super().changelist_view(request, extra_context=extra_context)

    change_list_template = "admin/stripe_product_changelist.html"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from api.models import StripePrice
from api.stripe import stripe


@admin.register(StripePrice)
class StripePriceAdmin(admin.ModelAdmin):
    search_fields = ("id", "product")
    list_display = ["id", "product", "is_active", "nickname", "recurring_interval"]
    readonly_fields = ["id", "product", "is_active", "nickname", "recurring_interval"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync/",
                self.admin_site.admin_view(self.sync_now),
                name="stripeprice_sync",
            ),
        ]
        return custom_urls + urls

    def sync_now(self, request):
        try:
            response = stripe.Price.list()
            for price_data in response.get("data", []):
                StripePrice.update_or_create(price_data)
            messages.success(request, "Prices have been synced with Stripe.")
        except Exception as e:
            messages.error(
                request, f"Something went wrong, please try again. Error: {e}"
            )
        return HttpResponseRedirect(reverse("admin:api_stripeprice_changelist"))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        sync_url = reverse("admin:stripeprice_sync")
        extra_context["sync_url"] = sync_url
        return super().changelist_view(request, extra_context=extra_context)

    change_list_template = "admin/stripe_price_changelist.html"

    def has_add_permission(self, request):
        return False

    def has_update_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

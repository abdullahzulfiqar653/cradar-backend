from django.contrib import admin

from api.models.workspace import Workspace
from api.stripe import stripe


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "get_owner_username",
        "get_subscription_product_name",
        "get_subscription_status",
    )
    search_fields = ("id", "name", "owned_by__username")
    readonly_fields = ["id"]
    ordering = ("-created_at",)
    actions = ["subscribe_to_free_trial"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("subscription__product", "owned_by")
        )

    @admin.display(description="Owner Username")
    def get_owner_username(self, obj):
        return obj.owned_by.username

    @admin.display(description="Subscription Product")
    def get_subscription_product_name(self, obj):
        return obj.subscription.product.name

    @admin.display(description="Subscription Status")
    def get_subscription_status(self, obj):
        return obj.subscription.status

    @admin.display(description="Subscription Free Trial", boolean=True)
    def get_subscription_is_free_trial(self, obj):
        return obj.subscription.is_free_trial

    @admin.action(description="Subscribe to Free Trial")
    def subscribe_to_free_trial(self, request, queryset):
        for workspace in queryset.filter(subscription__isnull=True):
            owner_user = workspace.workspace_users.filter(role="Owner").first().user
            workspace.usage_type = Workspace.UsageType.WORK
            workspace.save()
            stripe.Subscription.create(
                customer=workspace.get_stripe_customer_id(owner_user),
                items=[{"price": workspace.get_product_price_id()}],
                metadata={"workspace_id": workspace.id, "user_id": owner_user.id},
                trial_period_days=14,
            )
        self.message_user(request, "Successfully subscribed to free trial.")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

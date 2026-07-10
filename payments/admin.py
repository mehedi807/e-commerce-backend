from django.contrib import admin
from payments.models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'provider', 'transaction_id', 'status', 'created_at')
    list_filter = ('provider', 'status', 'created_at')
    search_fields = ('transaction_id', 'order__id', 'order__user__email')
    readonly_fields = ('created_at', 'updated_at')

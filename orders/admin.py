from django.contrib import admin
from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product',)
    readonly_fields = ('price', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'id')
    readonly_fields = ('total_amount',)
    inlines = [OrderItemInline]

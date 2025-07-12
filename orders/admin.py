from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_id', 'product_name', 'price', 'quantity', 'color', 'size', 'total_price', 'image1', 'image2')
    can_delete = False
    show_change_link = True  # Allows quick navigation to the OrderItem change page

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'phone', 'order_status', 'payment_status', 'payment_method', 'total', 'created_at')
    list_filter = ('order_status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'id')
    readonly_fields = ('created_at', 'updated_at', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'is_paid_online')
    inlines = [OrderItemInline]

    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'country_code', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('country', 'state', 'street', 'building', 'house', 'postal_code', 'zip_code')
        }),
        ('Delivery Details', {
            'fields': ('delivery_slot', 'express_delivery')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'order_status', 'coupon_code', 'subtotal', 'tax', 'delivery_charge', 'discount', 'total')
        }),
        ('Razorpay Payment Info', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'is_paid_online')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'order', 'price', 'quantity', 'color', 'size', 'total_price')
    list_filter = ('color', 'size')
    search_fields = ('product_name',)
    readonly_fields = ('order', 'product_id', 'product_name', 'price', 'quantity', 'color', 'size', 'total_price', 'image1', 'image2')

from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('sub_total', 'unit_price', 'total_price')
    fields = ('product', 'color', 'size', 'quantity', 'unit_price', 'sub_total', 'is_active')
    show_change_link = True

    def sub_total(self, obj):
        return obj.sub_total()
    sub_total.short_description = 'Subtotal'

    def unit_price(self, obj):
        return obj.unit_price()
    unit_price.short_description = 'Unit Price'

    def total_price(self, obj):
        return obj.total_price()
    total_price.short_description = 'Total Price'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'cart_id', 'date_added', 'total_items', 'total_price')
    list_filter = ('date_added', 'user')
    search_fields = ('user__username', 'user__email', 'cart_id')
    readonly_fields = ('cart_id', 'date_added', 'total_items', 'total_price')
    inlines = [CartItemInline]
    ordering = ('-date_added',)

    def total_items(self, obj):
        return obj.total_items()
    total_items.short_description = 'Total Items'

    def total_price(self, obj):
        return obj.total_price()
    total_price.short_description = 'Total Price'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'color', 'size', 'quantity', 'sub_total', 'is_active')
    list_filter = ('is_active', 'size', 'color', 'cart__user')
    search_fields = ('product__product_name', 'cart__cart_id', 'cart__user__username')
    readonly_fields = ('sub_total', 'unit_price', 'total_price')
    fieldsets = (
        (None, {
            'fields': ('cart', 'product', 'is_active')
        }),
        ('Item Details', {
            'fields': ('color', 'size', 'quantity')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'sub_total')
        }),
    )

    def sub_total(self, obj):
        return obj.sub_total()
    sub_total.short_description = 'Subtotal'

    def unit_price(self, obj):
        return obj.unit_price()
    unit_price.short_description = 'Unit Price'

    def total_price(self, obj):
        return obj.total_price()
    total_price.short_description = 'Total Price'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'cart', 'color')
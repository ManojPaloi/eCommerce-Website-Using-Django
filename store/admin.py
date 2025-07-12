from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Color, Review, ReviewInteraction, Wishlist

class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_name', 'slug', 'price', 'original_price',
        'discount_percentage', 'display_image1', 'display_image2',
        'display_image3', 'display_image4', 'stock', 'size',
        'display_colors', 'category', 'is_same_day_delivery_eligible',
        'is_available', 'created_date', 'modified_date',
    )
    prepopulated_fields = {'slug': ('product_name',)}
    list_filter = ('is_available', 'category', 'is_same_day_delivery_eligible', 'size')
    search_fields = ('product_name', 'description', 'slug')
    list_per_page = 20
    filter_horizontal = ('colors',)
    list_editable = ('price', 'original_price', 'stock', 'is_available', 'is_same_day_delivery_eligible')
    actions = ['mark_as_available', 'mark_as_unavailable']

    def display_image1(self, obj):
        return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image1.url) if obj.image1 else '-'
    display_image1.short_description = 'Image 1'

    def display_image2(self, obj):
        return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image2.url) if obj.image2 else '-'
    display_image2.short_description = 'Image 2'

    def display_image3(self, obj):
        return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image3.url) if obj.image3 else '-'
    display_image3.short_description = 'Image 3'

    def display_image4(self, obj):
        return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image4.url) if obj.image4 else '-'
    display_image4.short_description = 'Image 4'

    def display_colors(self, obj):
        return ", ".join([color.color_name for color in obj.colors.all()])
    display_colors.short_description = 'Colors'

    def discount_percentage(self, obj):
        return f"{obj.get_discount_percentage()}%" if obj.get_discount_percentage() > 0 else "No discount"
    discount_percentage.short_description = 'Discount'

    def mark_as_available(self, request, queryset):
        queryset.update(is_available=True)
    mark_as_available.short_description = "Mark selected products as available"

    def mark_as_unavailable(self, request, queryset):
        queryset.update(is_available=False)
    mark_as_unavailable.short_description = "Mark selected products as unavailable"

class ColorAdmin(admin.ModelAdmin):
    list_display = ('color_name', 'color_code', 'display_color', 'display_products')
    search_fields = ('color_name', 'color_code')
    list_filter = ('color_name',)
    list_per_page = 20

    def display_products(self, obj):
        return ", ".join(product.product_name for product in obj.products.all())
    display_products.short_description = 'Associated Products'

    def display_color(self, obj):
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color_code
        )
    display_color.short_description = 'Color Preview'

class ReviewInteractionInline(admin.TabularInline):
    model = ReviewInteraction
    extra = 1
    fields = ('user', 'interaction_type')
    raw_id_fields = ('user',)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'review_text_preview', 'created_at', 'total_likes', 'total_dislikes')
    search_fields = ('product__product_name', 'user__username', 'review_text')
    list_filter = ('rating', 'created_at', 'product')
    raw_id_fields = ('product', 'user')
    list_per_page = 20
    inlines = [ReviewInteractionInline]
    actions = ['delete_selected_reviews']

    def review_text_preview(self, obj):
        return obj.review_text[:50] + "..." if len(obj.review_text) > 50 else obj.review_text
    review_text_preview.short_description = 'Review Text'

    def total_likes(self, obj):
        return obj.total_likes()
    total_likes.short_description = 'Likes'

    def total_dislikes(self, obj):
        return obj.total_dislikes()
    total_dislikes.short_description = 'Dislikes'

    def delete_selected_reviews(self, request, queryset):
        queryset.delete()
    delete_selected_reviews.short_description = "Delete selected reviews"

class ReviewInteractionAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'interaction_type', 'review_product')
    search_fields = ('review__product__product_name', 'user__username')
    list_filter = ('interaction_type',)
    raw_id_fields = ('review', 'user')
    list_per_page = 20

    def review_product(self, obj):
        return obj.review.product.product_name
    review_product.short_description = 'Product'

class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__username', 'product__product_name')
    list_filter = ('added_at',)
    raw_id_fields = ('user', 'product')
    list_per_page = 20
    actions = ['clear_wishlist']

    def clear_wishlist(self, request, queryset):
        queryset.delete()
    clear_wishlist.short_description = "Clear selected wishlist items"

# Register models (without re-registering Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(ReviewInteraction, ReviewInteractionAdmin)
admin.site.register(Wishlist, WishlistAdmin)

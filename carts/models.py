import uuid
from django.db import models
from django.conf import settings
from store.models import Product, Color

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='carts'
    )
    cart_id = models.CharField(max_length=250, blank=True, unique=True)
    date_added = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.cart_id:
            self.cart_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        if self.cart_id and self.user:
            return f"Cart of {self.user.username} ({self.cart_id})"
        elif self.user:
            return f"Cart of {self.user.username}"
        else:
            return self.cart_id or "Anonymous Cart"

    def total_items(self):
        return sum(item.quantity for item in self.cartitem_set.all())

    def total_price(self):
        return sum(item.sub_total() for item in self.cartitem_set.all())

    class Meta:
        ordering = ['-date_added']

class CartItem(models.Model):
    SIZE_CHOICES = (
        ('XS', 'Extra Small'),
        ('SM', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
    )

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cartitem_set')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    color = models.ForeignKey(
        Color, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cart_items'
    )
    size = models.CharField(max_length=3, choices=SIZE_CHOICES, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price * self.quantity

    def image(self):
        return self.product.image1.url if self.product.image1 else 'https://via.placeholder.com/555x404.png?text=Product+Image'

    def name(self):
        return self.product.product_name

    def description(self):
        details = []
        if self.color:
            details.append(f"Color: {self.color.color_name}")
        if self.size:
            details.append(f"Size: {self.get_size_display()}")
        return ", ".join(details) or "No color or size selected"

    def unit_price(self):
        return self.product.price

    def total_price(self):
        return self.sub_total()

    def url(self):
        return self.product.get_url()

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity} ({self.description()})"

    class Meta:
        unique_together = ('cart', 'product', 'color', 'size')
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def save(self, *args, **kwargs):
        # Ensure we don't create duplicate items with same product, color and size
        if not self.pk:  # Only for new instances
            existing_item = CartItem.objects.filter(
                cart=self.cart,
                product=self.product,
                color=self.color,
                size=self.size
            ).first()
            
            if existing_item:
                existing_item.quantity += self.quantity
                existing_item.save()
                return existing_item
                
        super().save(*args, **kwargs)
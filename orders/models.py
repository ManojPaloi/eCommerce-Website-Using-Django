from django.db import models
from django.conf import settings

class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('credit', 'Credit/Debit Card'),
        ('cod', 'Cash on Delivery'),
    ]

    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Link order to user; can be null for guest checkout
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    # Customer contact info
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    country_code = models.CharField(max_length=5, default='+91')
    
    # Shipping address fields
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50, blank=True)
    street = models.CharField(max_length=100)
    building = models.CharField(max_length=100, blank=True)
    house = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)

    # Delivery details
    delivery_slot = models.CharField(max_length=50)
    express_delivery = models.BooleanField(default=False)

    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    coupon_code = models.CharField(max_length=20, blank=True)

    # Pricing info
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Razorpay payment integration fields (optional)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.TextField(blank=True, null=True)
    is_paid_online = models.BooleanField(default=False)

    # Automatic timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name}"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image1 = models.ImageField(upload_to='order_images', blank=True, null=True)
    image2 = models.ImageField(upload_to='order_images', blank=True, null=True)
    quantity = models.PositiveIntegerField()
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=10, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.quantity} × {self.product_name} (Order #{self.order.id})"

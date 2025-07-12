from django.db import models
from django.contrib.auth import get_user_model
from category.models import Category
from django.urls import reverse
from django.db.models import Count
from decimal import Decimal

User = get_user_model()

class Product(models.Model):
    SIZE_CHOICES = (
        ('XS', 'Extra Small'),
        ('SM', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
    )

    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image1 = models.ImageField(upload_to='photos/products', blank=True, null=True)
    image2 = models.ImageField(upload_to='photos/products', blank=True, null=True)
    image3 = models.ImageField(upload_to='photos/products', blank=True, null=True)
    image4 = models.ImageField(upload_to='photos/products', blank=True, null=True)
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    size = models.CharField(max_length=3, choices=SIZE_CHOICES, blank=True)
    colors = models.ManyToManyField('Color', related_name='products', blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_same_day_delivery_eligible = models.BooleanField(default=False)

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name

    def get_discount_percentage(self):
        try:
            if self.original_price <= 0 or self.price >= self.original_price or self.price <= 0:
                return 0
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return round(discount, 1)
        except Exception:
            return 0

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return 0

    def total_ratings(self):
        return self.reviews.count()

    def get_rating_count(self):
        ratings = self.reviews.values('rating').annotate(count=Count('rating')).order_by('-rating')
        total_reviews = self.reviews.count()
        return [
            {
                'rating': rating['rating'],
                'count': rating['count'],
                'percentage': (rating['count'] / total_reviews * 100) if total_reviews > 0 else 0
            }
            for rating in ratings
        ]

class Color(models.Model):
    color_name = models.CharField(max_length=50)
    color_code = models.CharField(max_length=7)  # e.g., #FFFFFF

    def __str__(self):
        return self.color_name

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.product_name}"

class ReviewInteraction(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='interactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=10, choices=(('like', 'Like'), ('dislike', 'Dislike')))

    class Meta:
        unique_together = ('review', 'user')

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def get_total(self):
        return sum(item.get_total() for item in self.cart_items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=10, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} in cart"

    def get_total(self):
        return self.product.price * self.quantity
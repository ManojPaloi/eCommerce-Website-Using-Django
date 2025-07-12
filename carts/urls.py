from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('cart-remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('increase-cart/<int:product_id>/', views.increase_cart, name='increase_cart'),
    path('decrease-cart/<int:product_id>/', views.decrease_cart, name='decrease_cart'),
    path('remove-cart-item/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('place-order/', views.place_order, name='place_order'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    # path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('search/', views.search, name='search'),
    path('submit-review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('review-interaction/', views.review_interaction, name='review_interaction'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
]
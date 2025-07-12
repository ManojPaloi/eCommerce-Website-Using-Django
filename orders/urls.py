from django.urls import path
from . import views
from .views import download_invoice_pdf

urlpatterns = [
    path('my-orders/', views.my_orders, name='my_orders'),
    path('invoice/download/<int:order_id>/', views.download_invoice, name='download_invoice'),
    path('track-order/<int:order_id>/', views.track_order, name='track_order'),
    # path('order-status/<int:order_id>/', views.order_status_api, name='order_status_api'),
    path('invoice/download/pdf/<int:order_id>/', download_invoice_pdf, name='download_invoice_pdf'),
]

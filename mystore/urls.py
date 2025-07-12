from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("store/", include("store.urls")),
    path("carts/", include("carts.urls")),
    path("accounts/", include("accounts.urls")),
    path('accounts/', include('allauth.urls')),
    path("orders/", include("orders.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

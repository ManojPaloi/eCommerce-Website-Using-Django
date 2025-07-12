from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomPasswordResetConfirmView  # ✅ Import your custom view

urlpatterns = [
    # User registration and login/logout
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('submit-contact/', views.submit_contact, name='submit_contact'),
    path('check-availability/', views.check_availability, name='check_availability'),
    # User account page
    path('my-account/', views.my_account, name='my_account'),
    path('customer-support/', views.customer_support, name='customer_support'),
    path('check-support-updates/', views.check_support_updates, name='check_support_updates'),
    path('fetch-new-replies/', views.fetch_new_replies, name='fetch_new_replies'),

    # Email activation
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    # Forgot password request
    path('forgotPassword/', views.forgot_password, name='forgot_password'),

    # ✅ Custom password reset confirm view (prevents reusing same password)
    path(
        'reset/<uidb64>/<token>/',
        CustomPasswordResetConfirmView.as_view(),  # ✅ Use your custom view here
        name='password_reset_confirm'
    ),

    # Password reset done page
    path(
        'forgotPassword/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    # Password reset complete page
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]

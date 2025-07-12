from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.urls import reverse

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.username:
            base_username = data.get('email', '').split('@')[0] or 'user'
            username = base_username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{get_random_string(4, '0123456789')}"
            user.username = username
        if not user.first_name:
            user.first_name = data.get('first_name', 'User')
        if not user.last_name:
            user.last_name = data.get('last_name', 'Account')
        if not user.phone_number:
            user.phone_number = '0000000000'  # Placeholder
        return user

    def get_login_redirect_url(self, request):
        provider = request.session.get('socialaccount_sociallogin', {}).get('account', {}).get('provider')
        if provider:
            return reverse('socialaccount_login') + f'?provider={provider}'
        return super().get_login_redirect_url(request)
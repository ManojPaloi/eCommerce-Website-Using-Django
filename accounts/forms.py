from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, UserChangeForm, PasswordResetForm, SetPasswordForm
)
from .models import Account
import re

# ✅ Custom Signup Form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Account
        fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.required = True  # Make all fields required
            classes = 'form-control'
            if field_name in self.errors:
                classes += ' is-invalid'
            field.widget.attrs.update({
                'class': classes,
                'placeholder': field.label,
                'autocomplete': 'off',
                'aria-required': 'true',
            })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required.')
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already taken.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise forms.ValidationError('Username is required.')
        if not re.match(r'^[a-z]+[0-9]+$', username):
            raise forms.ValidationError(
                'Username must contain only lowercase letters followed by numbers (e.g., manoj123).'
            )
        if Account.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError('First name is required.')
        if len(first_name) < 2:
            raise forms.ValidationError('First name must be at least 2 characters long.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError('Last name is required.')
        if len(last_name) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters long.')
        return last_name

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            raise forms.ValidationError('Phone number is required.')
        if not phone.isdigit():
            raise forms.ValidationError('Phone number must contain digits only.')
        if len(phone) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits.')
        if Account.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('This phone number is already taken.')
        return phone

# ✅ Custom User Update Form (Admin or Profile Edit)
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = Account
        fields = (
            'email', 'username', 'first_name', 'last_name',
            'phone_number', 'default_shipping_address',
            'is_active', 'is_staff', 'is_superuser'
        )

    def __init__(self, *args, **kwargs):
        super(CustomUserChangeForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label,
            })


# ✅ Custom Login Form (for username or email login)
class CustomLoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Username or Email",
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username or email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
        }),
    )


# ✅ Account Update Form (For "My Account" page)
class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [
            'first_name', 'last_name', 'username', 'email', 'phone_number',
            'date_of_birth', 'gender', 'city', 'country', 'address',
            'postal_code', 'bio', 'profile_picture'
        ]

    def __init__(self, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label,
            })


# ✅ Custom Password Reset Form
class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordResetForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control shadow-sm rounded-3 p-3',
                'placeholder': field.label,
                'style': 'border: 1.5px solid #007bff; font-size: 1.1rem;',
                'autocomplete': 'email',
                'aria-describedby': f'{field_name}-help',
            })


# ✅ Custom Set Password Form (for PasswordResetConfirmView)
class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(CustomSetPasswordForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control shadow-sm rounded-3 p-3',
            'placeholder': 'New Password',
            'style': 'border: 1.5px solid #007bff; font-size: 1.1rem;',
            'autocomplete': 'new-password',
            'aria-describedby': 'new-password1-help',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control shadow-sm rounded-3 p-3',
            'placeholder': 'Confirm New Password',
            'style': 'border: 1.5px solid #007bff; font-size: 1.1rem;',
            'autocomplete': 'new-password',
            'aria-describedby': 'new-password2-help',
        })

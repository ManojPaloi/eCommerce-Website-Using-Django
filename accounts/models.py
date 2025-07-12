from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta


class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
            
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30, blank=False, null=False)  # Required
    last_name = models.CharField(max_length=30, blank=False, null=False)   # Required
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)  # Changed to False for email activation
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=False, null=False, unique=True)  # Required
    default_shipping_address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'phone_number']  # Updated

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def get_full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

    def is_customer(self):
        return not (self.is_staff or self.is_superuser)

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save()

    def update_profile(self, **kwargs):
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
        self.save()
        return self
    
    
    
class SupportRequest(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Support - {self.user.email} - {self.subject[:30]}"
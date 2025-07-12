from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Account, SupportRequest


@admin.register(Account)
class AccountAdmin(BaseUserAdmin):
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'phone_number',
        'is_active', 'is_staff', 'is_superuser', 'is_admin', 'date_joined'
    )
    list_display_links = ('email', 'username', 'first_name', 'last_name')
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_admin', 'date_joined'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('date_joined', 'last_login')

    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'phone_number', 'date_of_birth',
                'gender', 'city', 'country', 'address', 'postal_code',
                'bio', 'profile_picture'
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'password1', 'password2',
                'first_name', 'last_name', 'phone_number', 'date_of_birth',
                'gender', 'city', 'country', 'address', 'postal_code',
                'bio', 'profile_picture',
                'is_active', 'is_staff', 'is_superuser', 'is_admin'
            ),
        }),
    )

    ordering = ('email',)
    filter_horizontal = ()


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'created_at', 'resolved')
    list_filter = ('resolved', 'created_at')
    search_fields = ('user__email', 'subject', 'message')
    readonly_fields = ('user', 'subject', 'message', 'created_at')
    ordering = ('-created_at',)

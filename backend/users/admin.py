import django.contrib.admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import Subscription, User


@django.contrib.admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'avatar_tag', 'is_staff', 'is_active'
    )
    list_display_links = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('id',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    def avatar_tag(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:30px; height:30px; border-radius:50%;" />',
                obj.avatar.url
            )
        return "-"

    avatar_tag.short_description = 'Аватар'


@django.contrib.admin.register(Subscription)
class SubscriptionAdmin(django.contrib.admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created')
    list_filter = ('created', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    ordering = ('-created',)
    readonly_fields = ('id', 'created')
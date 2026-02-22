from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Info', {'fields': ('is_booktoker', 'is_premium', 'bio', 'social_links')}),
    )

admin.site.register(User, CustomUserAdmin)

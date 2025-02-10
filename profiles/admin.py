from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'hash', 'is_trial']
    search_fields = ['name', 'hash', 'user__username']
    list_filter = ['is_trial']

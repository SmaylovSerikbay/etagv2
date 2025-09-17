from django.contrib import admin
from .models import Profile, NfcCard

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'hash', 'is_trial']
    search_fields = ['name', 'hash', 'user__username']
    list_filter = ['is_trial']

@admin.register(NfcCard)
class NfcCardAdmin(admin.ModelAdmin):
    list_display = ('uid', 'profile', 'tap_count', 'first_seen_at', 'last_seen_at', 'assigned_at')
    search_fields = ('uid', 'profile__name', 'profile__user__username', 'profile__email')
    list_filter = ('assigned_at',)

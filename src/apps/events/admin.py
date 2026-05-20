from django.contrib import admin
from .models import Event, EventRegistration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'organizer', 'created_at')
    list_filter = ('date', 'location')
    search_fields = ('title', 'description', 'location', 'organizer__email')
    ordering = ('date',)
    raw_id_fields = ('organizer',)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at')
    list_filter = ('event',)
    search_fields = ('user__email', 'event__title')
    raw_id_fields = ('user', 'event')

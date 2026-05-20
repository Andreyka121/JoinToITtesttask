from rest_framework import serializers
from django.utils import timezone
from .models import Event, EventRegistration
from apps.users.serializers import UserSerializer


class EventReadSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    participants_count = serializers.IntegerField(read_only=True)
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            'id', 'title', 'description', 'date', 'location',
            'organizer', 'participants_count', 'is_registered',
            'created_at', 'updated_at',
        )

    def get_is_registered(self, obj):
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            return False
        # Uses prefetched data when available to avoid N+1
        user_regs = getattr(obj, 'user_registrations', None)
        if user_regs is not None:
            return len(user_regs) > 0
        return obj.registrations.filter(user=request.user).exists()


class EventWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('title', 'description', 'date', 'location')

    def validate_date(self, value):
        if value < timezone.now():
            raise serializers.ValidationError('Event date must be in the future.')
        return value


class EventRegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventRegistration
        fields = ('id', 'user', 'registered_at')

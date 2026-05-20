from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Prefetch
from django_filters.rest_framework import DjangoFilterBackend

from .models import Event, EventRegistration
from .serializers import EventReadSerializer, EventWriteSerializer, EventRegistrationSerializer
from .filters import EventFilter
from .permissions import IsOrganizerOrReadOnly


class EventViewSet(viewsets.ModelViewSet):
    filterset_class = EventFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['date', 'title', 'created_at']
    ordering = ['date']
    search_fields = ['title', 'description', 'location']

    def get_queryset(self):
        qs = Event.objects.select_related('organizer').annotate(
            participants_count=Count('registrations')
        )
        # Prefetch current user's registrations to avoid N+1 in is_registered field
        if self.request.user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch(
                    'registrations',
                    queryset=EventRegistration.objects.filter(user=self.request.user),
                    to_attr='user_registrations',
                )
            )
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return EventWriteSerializer
        return EventReadSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsOrganizerOrReadOnly()]
        if self.action in ('create', 'register', 'unregister', 'participants'):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        event = self.get_object()
        if EventRegistration.objects.filter(user=request.user, event=event).exists():
            return Response(
                {'detail': 'You are already registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        EventRegistration.objects.create(user=request.user, event=event)
        return Response({'detail': 'Successfully registered.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unregister(self, request, pk=None):
        event = self.get_object()
        deleted, _ = EventRegistration.objects.filter(user=request.user, event=event).delete()
        if not deleted:
            return Response(
                {'detail': 'You are not registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def participants(self, request, pk=None):
        event = self.get_object()
        registrations = event.registrations.select_related('user').all()
        serializer = EventRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)

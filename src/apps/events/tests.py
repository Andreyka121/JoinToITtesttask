from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from .models import Event, EventRegistration


def future_date(days=30):
    return timezone.now() + timedelta(days=days)


class EventBaseTest(APITestCase):
    """Shared fixtures for all event tests."""

    def setUp(self):
        self.organizer = User.objects.create_user(
            email='organizer@example.com',
            password='pass123',
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='pass123',
        )
        self.event = Event.objects.create(
            title='Test Conference',
            description='A test event',
            date=future_date(30),
            location='Kyiv',
            organizer=self.organizer,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def event_url(self, action, pk=None):
        if pk is None:
            pk = self.event.pk
        return reverse(f'events-{action}', kwargs={'pk': pk})


# ── Auth & Event Creation ─────────────────────────────────────────────────────

class EventCreateTest(EventBaseTest):

    def test_unauthenticated_cannot_create_event(self):
        response = self.client.post(reverse('events-list'), {
            'title': 'Unauthorized Event',
            'date': future_date(10).isoformat(),
            'location': 'Lviv',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_event(self):
        self.authenticate(self.organizer)
        response = self.client.post(reverse('events-list'), {
            'title': 'New Conference',
            'date': future_date(10).isoformat(),
            'location': 'Lviv',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.filter(title='New Conference').count(), 1)

    def test_organizer_is_set_automatically(self):
        self.authenticate(self.organizer)
        response = self.client.post(reverse('events-list'), {
            'title': 'Auto Organizer Event',
            'date': future_date(10).isoformat(),
            'location': 'Odesa',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(title='Auto Organizer Event')
        self.assertEqual(event.organizer, self.organizer)

    def test_cannot_create_event_in_the_past(self):
        self.authenticate(self.organizer)
        response = self.client.post(reverse('events-list'), {
            'title': 'Past Event',
            'date': (timezone.now() - timedelta(days=1)).isoformat(),
            'location': 'Kyiv',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ── Event Update / Delete ─────────────────────────────────────────────────────

class EventUpdateTest(EventBaseTest):

    def test_organizer_can_update_own_event(self):
        self.authenticate(self.organizer)
        response = self.client.patch(
            self.event_url('detail'),
            {'title': 'Updated Title'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Updated Title')

    def test_other_user_cannot_update_event(self):
        self.authenticate(self.other_user)
        response = self.client.patch(
            self.event_url('detail'),
            {'title': 'Hacked Title'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Test Conference')

    def test_unauthenticated_cannot_update_event(self):
        response = self.client.patch(
            self.event_url('detail'),
            {'title': 'No Auth Title'},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_organizer_can_delete_own_event(self):
        self.authenticate(self.organizer)
        response = self.client.delete(self.event_url('detail'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())

    def test_other_user_cannot_delete_event(self):
        self.authenticate(self.other_user)
        response = self.client.delete(self.event_url('detail'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())


# ── Event Registration ────────────────────────────────────────────────────────

class EventRegistrationTest(EventBaseTest):

    def test_user_can_register_for_event(self):
        self.authenticate(self.other_user)
        response = self.client.post(self.event_url('register'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            EventRegistration.objects.filter(
                user=self.other_user, event=self.event
            ).exists()
        )

    def test_duplicate_registration_returns_400(self):
        self.authenticate(self.other_user)
        self.client.post(self.event_url('register'))
        response = self.client.post(self.event_url('register'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            EventRegistration.objects.filter(
                user=self.other_user, event=self.event
            ).count(),
            1,
        )

    def test_user_can_unregister_from_event(self):
        EventRegistration.objects.create(user=self.other_user, event=self.event)
        self.authenticate(self.other_user)
        response = self.client.delete(self.event_url('unregister'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            EventRegistration.objects.filter(
                user=self.other_user, event=self.event
            ).exists()
        )

    def test_unregister_when_not_registered_returns_400(self):
        self.authenticate(self.other_user)
        response = self.client.delete(self.event_url('unregister'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_register(self):
        response = self.client.post(self.event_url('register'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ── Filtering ─────────────────────────────────────────────────────────────────

class EventFilterTest(EventBaseTest):

    def setUp(self):
        super().setUp()
        self.event2 = Event.objects.create(
            title='Python Meetup',
            description='Python developers meetup',
            date=future_date(60),
            location='Lviv',
            organizer=self.organizer,
        )

    def get_results(self, params):
        response = self.client.get(reverse('events-list'), params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['results']

    def test_filter_by_title(self):
        results = self.get_results({'title': 'Conference'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Conference')

    def test_filter_by_title_case_insensitive(self):
        results = self.get_results({'title': 'conference'})
        self.assertEqual(len(results), 1)

    def test_filter_by_location(self):
        results = self.get_results({'location': 'Lviv'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Python Meetup')

    def test_filter_by_date_from(self):
        date_from = future_date(45).isoformat()
        results = self.get_results({'date_from': date_from})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Python Meetup')

    def test_filter_by_date_to(self):
        date_to = future_date(45).isoformat()
        results = self.get_results({'date_to': date_to})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Conference')

    def test_filter_by_date_range_returns_both(self):
        params = {
            'date_from': future_date(1).isoformat(),
            'date_to': future_date(90).isoformat(),
        }
        results = self.get_results(params)
        self.assertEqual(len(results), 2)

    def test_search_across_fields(self):
        results = self.get_results({'search': 'python'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Python Meetup')

    def test_no_match_returns_empty(self):
        results = self.get_results({'title': 'nonexistent'})
        self.assertEqual(len(results), 0)

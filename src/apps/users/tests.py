from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class UserRegistrationTest(APITestCase):
    url = reverse('register')

    def test_user_can_register(self):
        response = self.client.post(self.url, {
            'email': 'john@example.com',
            'password': 'securepass123',
            'first_name': 'John',
            'last_name': 'Doe',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'john@example.com')
        self.assertNotIn('password', response.data)
        self.assertTrue(User.objects.filter(email='john@example.com').exists())

    def test_registration_requires_email(self):
        response = self.client.post(self.url, {'password': 'securepass123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(email='existing@example.com', password='pass123')
        response = self.client.post(self.url, {
            'email': 'existing@example.com',
            'password': 'anotherpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_password_is_rejected(self):
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'password': '123',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

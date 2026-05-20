from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import EventRegistration


@receiver(post_save, sender=EventRegistration)
def send_registration_confirmation(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user
    event = instance.event

    send_mail(
        subject=f'Registration confirmed: {event.title}',
        message=(
            f'Hi {user.first_name or user.email},\n\n'
            f'You have successfully registered for "{event.title}".\n'
            f'Date: {event.date.strftime("%Y-%m-%d %H:%M")} UTC\n'
            f'Location: {event.location}\n\n'
            f'See you there!'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

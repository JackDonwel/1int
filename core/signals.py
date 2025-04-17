from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile  # Import the UserProfile model
from django.contrib.auth.models import User  # Import the User model

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()

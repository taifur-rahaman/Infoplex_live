from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.STUDENT
    )
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    current_level = models.CharField(max_length=50, blank=True)
    interest = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.get_username()} ({self.role})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)

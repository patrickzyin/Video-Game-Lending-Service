from django.db import models
from django.contrib.auth.models import User
from mysite.storage_backends import ProfileMediaStorage  # corrected

class UserProfile(models.Model):
    DoesNotExist = None
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mysite_profile')
    profile_picture = models.ImageField(
        upload_to='',  # empty because storage.location already points to 'profiles/'
        storage=ProfileMediaStorage(),
        blank=True,
        null=True,
        default='/static/default_avatar.png'
    )
    google_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        app_label = 'mysite'

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from allauth.socialaccount.signals import social_account_added
from .models import UserProfile


#Used this website as a reference
#https://docs.djangoproject.com/en/5.1/topics/auth/default/
#and
#https://docs.djangoproject.com/en/5.1/ref/signals/
@receiver(post_save, sender=User)
def Add_User(sender,instance,created, **kwargs):
    if created:
        instance.groups.add(Group.objects.get(name='Patron'))


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(social_account_added)
def populate_profile(request, sociallogin, **kwargs):
    user = sociallogin.user
    extra_data = sociallogin.account.extra_data

    profile = UserProfile.objects.get(user=user)
    profile.profile_picture = extra_data.get('picture', '')
    profile.google_id = extra_data.get('sub', '')
    user.save()
    profile.save()


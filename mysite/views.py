from urllib import request
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import UserProfile
from catalog.models import Game, BorrowRequest, Collection
from .forms import ProfilePictureForm



#Used this website, https://docs.djangoproject.com/en/5.1/topics/auth/default/

def HomePage(request):
    """
    Home page view that redirects based on user role.
    For anonymous users, redirect to login page.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.is_superuser:
        return render(request, 'mysite/home.html')
    elif request.user.groups.filter(name='Librarian').exists():
        return redirect('catalog:librarian_dashboard')
    elif request.user.groups.filter(name='Patron').exists():
        return redirect('catalog:patron_dashboard')
    else:
        # User has no role assigned yet, show them a message
        return render(request, 'mysite/other.html')

class LibrarianPage(LoginRequiredMixin, TemplateView):
    template_name = 'mysite/librarian.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add all the required context data
        patron_group = Group.objects.get(name='Patron')
        context.update({
            'user': self.request.user,
            'available_games': Game.objects.all(),
            'patrons': patron_group.user_set.all().order_by('username'),
            'borrow_requests': BorrowRequest.objects.filter(approved=False, denied=False)
        })
        return context
    

from django.views.generic import TemplateView
from catalog.models import Game

class PatronPage(LoginRequiredMixin, TemplateView):
    template_name = 'mysite/patron.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user': self.request.user,
            'user_collections': Collection.objects.filter(
                creator=self.request.user
            ).prefetch_related('games'),
            'public_collections': Collection.objects.filter(
                is_public=True
            ).exclude(
                creator=self.request.user
            ).prefetch_related('games'),
            'available_games': Game.objects.filter(available=True)
        })
        return context

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=profile)

        if 'profile_picture-clear' in request.POST:
            profile.profile_picture.delete(save=False)
            profile.profile_picture = None
            profile.save()
            return redirect('users-profile')

        if form.is_valid():
            form.save()
            return redirect('users-profile')
    else:
        form = ProfilePictureForm(instance=profile)

    return render(request, 'mysite/profile.html', {
        'profile': profile,
        'user': request.user,
        'form': form
    })





def get_or_create_user_profile(user):
    try:
        return user.userprofile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.create(user=user)
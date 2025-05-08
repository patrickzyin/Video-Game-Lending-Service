from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from catalog.views import upload_picture
from catalog.views import upload_item
from allauth.socialaccount.providers.google.views import oauth2_login

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='mysite/login.html'), name='login'),
    path('admin/', admin.site.urls),
    path('catalog/', include('catalog.urls')),
    path('librarian/', views.LibrarianPage.as_view(), name='librarian'),
    path('patron/', views.PatronPage.as_view(), name='patron'),
    path('upload_picture/', upload_picture, name='upload_picture'),
    path('upload_item/', upload_item, name='upload_item'),
    path('profile/', views.profile, name='users-profile'),
    path('accounts/', include('allauth.urls')),
    path('google/login/', oauth2_login, name='google_oauth2_login'),
]

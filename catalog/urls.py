from django.urls import path
from . import views
from .views import librarian_dashboard, add_game

app_name = 'catalog'  # Ensure namespacing for the catalog app

urlpatterns = [
    path('', views.game_list, name='game_list'),  # List available games
    path('borrowed_games/', views.borrowed_games, name='borrowed_games'),  # View borrowed games
    path('borrow_game/<int:game_id>/', views.borrow_game, name='borrow_game'),  # Borrow a game
    path('return_game/<int:borrowed_game_id>/', views.return_game, name='return_game'),  # Return a game
    path('librarian/', librarian_dashboard, name='librarian_dashboard'),  # Librarian dashboard
    path('add_game/', add_game, name='add_game'),  # Add a new game
    path('upgrade_patron/', views.upgrade_patron, name='upgrade_patron'),
    path('game/edit/<int:game_id>/', views.edit_game, name='edit_game'),
    path('game/delete/<int:game_id>/', views.delete_game, name='delete_game'),
    path('upload_picture/', views.upload_picture, name='upload_picture'),
    path('upload_item/', views.upload_item, name='upload_item'),
    path('approve/<int:borrow_request_id>/', views.approve_borrow_request, name='approve_borrow'),
    path('deny/<int:borrow_request_id>/', views.deny_borrow_request, name='deny_borrow'),
    path('borrow/delete/<int:request_id>/', views.delete_borrow_request, name='delete_borrow_request'),

    # Collection paths
    path('collections/add/', views.add_collection, name='add_collection'),
    path('collections/edit/<int:collection_id>/', views.edit_collection, name='edit_collection'),
    path('collections/delete/<int:collection_id>/', views.delete_collection, name='delete_collection'),
    path('collections/', views.view_collections, name='view_collections'),
    path('collections/<int:collection_id>/', views.view_collection_detail, name='collection_detail'),
    
    # Patron dashboard
    path('patron/', views.patron_dashboard, name='patron_dashboard'),
    path('game/<int:game_id>/', views.game_detail, name='game_detail'), 
   
    # Search functionality
    path('search/', views.search_items, name='search'),
]

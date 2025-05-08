from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Game, BorrowedGame, BorrowRequest, Collection
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef
from django.db.models import Avg  
from .models import Review
from .forms import ReviewForm  
from django.shortcuts import render, redirect  # Make sure redirect is imported
# ---------------------- Game Views ----------------------
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .forms import ProfilePictureForm
from django.db.models import Q
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .forms import ProfilePictureForm


def game_list(request):
    # Fetch available games for rent
    available_games = Game.objects.filter(available=True)

    # Fetch games borrowed by the logged-in user that are not yet returned
    borrowed_games = []
    if request.user.is_authenticated:
        borrowed_games = BorrowedGame.objects.filter(user=request.user, returned=False)

    return render(request, 'mysite/game_list.html', {
        'available_games': available_games,
        'borrowed_games': borrowed_games
    })


@login_required
def borrow_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if not game.available:
        return render(request, 'mysite/game_not_available.html', {'game': game})

    # Check if a pending request already exists
    existing_request = BorrowRequest.objects.filter(user=request.user, game=game, approved=False, denied=False).first()
    if existing_request:
        message = f"You already have a pending request for {game.title}."
    else:
        # Create a borrow request instead of borrowing directly
        BorrowRequest.objects.create(user=request.user, game=game)
        message = f"Borrow request for {game.title} submitted. Awaiting librarian approval."

    return render(request, 'mysite/game_action_result.html', {'message': message, 'game': game})


@login_required
def return_game(request, borrowed_game_id):
    borrowed_game = get_object_or_404(BorrowedGame, id=borrowed_game_id)
    game = borrowed_game.game

    if borrowed_game.user == request.user and not borrowed_game.returned:
        # Mark the game as returned
        borrowed_game.returned = True
        borrowed_game.save()

        # Mark the game as available again
        game.available = True
        game.save()

        return render(request, 'mysite/return_game_success.html', {'game': game})

    return render(request, 'mysite/game_not_rented.html', {'game': game})

@login_required
def borrowed_games(request):
    # Fetch all borrowed games for the logged-in user
    borrowed_games = BorrowedGame.objects.filter(user=request.user, returned=False)
    return render(request, 'mysite/borrowed_games.html', {'borrowed_games': borrowed_games})


# ---------------------- Librarian Views ----------------------

from django.shortcuts import render, redirect
from .models import Game  # Import your Game model
from django.contrib.auth.models import Group

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

@login_required
def librarian_dashboard(request):
    patron_group, _ = Group.objects.get_or_create(name='Patron')
    patrons = patron_group.user_set.all().order_by('username')

    # Librarian's own collections
    librarian_collections = Collection.objects.filter(creator=request.user).prefetch_related('games')

    # All public collections (can include their own too if public)
    public_collections = Collection.objects.filter(is_public=True).prefetch_related('games')

    return render(request, 'mysite/librarian.html', {
        'available_games': Game.objects.all(),
        'patrons': patrons,
        'borrow_requests': BorrowRequest.objects.filter(approved=False, denied=False),
        'librarian_collections': librarian_collections,
        'public_collections': public_collections,
    })


@login_required
def add_game(request):
    if request.method == "POST":
        title = request.POST["title"]
        platform = request.POST["platform"]
        genre = request.POST["genre"]
        description = request.POST.get("description", "")
        image = request.FILES.get("image")  # <- Optional image

        Game.objects.create(
            title=title,
            platform=platform,
            genre=genre,
            description=description,
            image=image,  # <- May be None, which is fine
            available=True
        )

        return redirect("catalog:librarian_dashboard") 

    return render(request, "mysite/librarian.html")



@login_required
def edit_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if request.method == "POST":
        game.title = request.POST["title"]
        game.platform = request.POST["platform"]
        game.genre = request.POST["genre"]
        game.description = request.POST.get("description", "")
        game.available = "available" in request.POST

        if "remove_image" in request.POST:
            game.image.delete(save=False)
            game.image = None
        elif "image" in request.FILES:
            game.image = request.FILES["image"]

        game.save()
        return redirect("catalog:librarian_dashboard")

    return render(request, "mysite/edit_game.html", {"game": game})


@login_required
def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    game.delete()
    return redirect("catalog:librarian_dashboard")


# ---------------------- Collection Views ----------------------

@login_required
def add_collection(request):
    # Allow both librarians and patrons to create collections
    if request.method == "POST":
        name = request.POST["name"]
        description = request.POST["description"]
        
        # Create collection with the current user as creator
        collection = Collection.objects.create(
            name=name, 
            description=description,
            creator=request.user,
            # For librarians, check if they want to make it private
            is_public=not (request.user.groups.filter(name='Librarian').exists() and 
                         request.POST.get('is_private', False))
        )
        
        # Add games to collection
        game_ids = request.POST.getlist("games")
        for game_id in game_ids:
            game = Game.objects.get(id=game_id)
            collection.games.add(game)
        
        # Redirect based on user type
        if request.user.groups.filter(name='Librarian').exists():
            return redirect("catalog:librarian_dashboard")
        else:
            return redirect("catalog:patron_dashboard")
    
    # games = Game.objects.all()
    games = Game.objects.annotate(
            in_private=Exists(Collection.objects.filter(is_public=False, games=OuterRef('pk'))),
            in_any=Exists(Collection.objects.filter(games=OuterRef('pk')))
    )
    is_librarian = request.user.groups.filter(name='Librarian').exists()
    return render(request, "mysite/add_collection.html", {
        "games": games,
        "is_librarian": is_librarian
    })


@login_required
def edit_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    
    # Check if user is authorized to edit this collection
    if collection.creator != request.user and not request.user.groups.filter(name='Librarian').exists():
        return render(request, "mysite/unauthorized.html", {"message": "You don't have permission to edit this collection"})
    
    if request.method == "POST":
        collection.name = request.POST["name"]
        collection.description = request.POST["description"]
        
        # Only librarians can set collections to private
        # if request.user.groups.filter(name='Librarian').exists():
        #     collection.is_public = not request.POST.get('is_private', False)
            
        collection.save()

        # Add new games to collection
        collection.games.clear()
        game_ids = request.POST.getlist("games")
        for game_id in game_ids:
            game = Game.objects.get(id=game_id)
            collection.games.add(game)
        
        # Redirect based on user type
        if request.user.groups.filter(name='Librarian').exists():
            return redirect("catalog:librarian_dashboard")
        else:
            return redirect("catalog:patron_dashboard")

    # games = Game.objects.all()
    games = Game.objects.annotate(
        in_private=Exists(Collection.objects.filter(is_public=False, games=OuterRef('pk'))),
        in_any=Exists(Collection.objects.filter(games=OuterRef('pk')))
    )
    games = games.exclude(pk__in=collection.games.values_list('pk', flat=True))
    if collection.is_public:
        games = games.filter(in_private=False)
    else:
        games = games.filter(in_any=False)
    
    is_librarian = request.user.groups.filter(name='Librarian').exists()
    return render(request, "mysite/edit_collection.html", {
        "collection": collection, 
        "games": games,
        "is_librarian": is_librarian
    })


@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    
    # Check if user is authorized to delete this collection
    if collection.creator != request.user and not request.user.groups.filter(name='Librarian').exists():
        return render(request, "mysite/unauthorized.html", {"message": "You don't have permission to delete this collection"})
    
    collection.delete()
    
    # Redirect based on user type
    if request.user.groups.filter(name='Librarian').exists():
        return redirect("catalog:librarian_dashboard")
    else:
        return redirect("catalog:patron_dashboard")


def view_collections(request):
    # View all public collections
    public_collections = Collection.objects.filter(is_public=True)
    
    # Add own private collections for authenticated users
    own_collections = []
    if request.user.is_authenticated:
        own_collections = Collection.objects.filter(creator=request.user, is_public=False)
    
    collections = list(public_collections)
    collections.extend(own_collections)
    
    return render(request, "mysite/view_collections.html", {
        "collections": collections
    })


@login_required
def view_collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    
    # Anonymous users can only view public collections
    if not collection.is_public and (not request.user.is_authenticated or 
                                     (collection.creator != request.user and 
                                      not request.user.groups.filter(name='Librarian').exists())):
        return render(request, "mysite/unauthorized.html", {"message": "You don't have permission to view this collection"})
    
    can_edit = request.user.is_authenticated and (collection.creator == request.user or 
                                                 request.user.groups.filter(name='Librarian').exists())
    
    return render(request, "mysite/collection_detail.html", {
        "collection": collection,
        "can_edit": can_edit
    })


@login_required
def patron_dashboard(request):
    user_collections = Collection.objects.filter(creator=request.user).prefetch_related('games')
    public_collections = Collection.objects.filter(is_public=True).exclude(creator=request.user).prefetch_related('games')
    available_games = Game.objects.filter(available=True).annotate(avg_rating=Avg('reviews__rating')).prefetch_related('reviews')
    borrowed_games = BorrowedGame.objects.filter(user=request.user, returned=False)
    borrow_requests = BorrowRequest.objects.filter(user=request.user)

    return render(request, "mysite/patron.html", {
        "user": request.user,
        "user_collections": user_collections,
        "public_collections": public_collections,
        "available_games": available_games,
        "borrowed_games": borrowed_games,  
        "borrow_requests": borrow_requests  
    })



# ---------------------- Borrow Request Views ----------------------

@login_required
def borrow_request_list(request):
    borrow_requests = BorrowRequest.objects.all()
    return render(request, 'mysite/borrow_request_list.html', {'borrow_requests': borrow_requests})


@login_required
def approve_borrow_request(request, borrow_request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=borrow_request_id)
    game = borrow_request.game
    user = borrow_request.user

    if not game.available:
        message = f"{game.title} is already borrowed."
        return render(request, 'mysite/borrow_request_result.html', {
            'message': message,
            'game': game,
            'user': user
        })

    # Mark request approved and game unavailable
    borrow_request.approved = True
    borrow_request.save()

    game.available = False
    game.save()

    BorrowedGame.objects.create(user=user, game=game)

    message = f"You approved {user.username}'s request for '{game.title}'."
    return render(request, 'mysite/borrow_request_result.html', {
        'message': message,
        'game': game,
        'user': user
    })

@login_required
def deny_borrow_request(request, borrow_request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=borrow_request_id)
    game = borrow_request.game
    user = borrow_request.user

    # Mark request as denied
    borrow_request.denied = True
    borrow_request.save()

    message = f"You denied {user.username}'s request for '{game.title}'."
    return render(request, 'mysite/borrow_request_result.html', {
        'message': message,
        'game': game,
        'user': user
    })

@login_required
def delete_borrow_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=request_id, user=request.user)

    # Only allow deletion of approved or denied requests (not pending)
    if borrow_request.approved or borrow_request.denied:
        borrow_request.delete()

    return redirect('catalog:patron_dashboard')


    


# ---------------------- User Role Management ----------------------

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect

@login_required
def upgrade_patron(request):
    if request.method == "POST":
        user_id = request.POST.get('user')
        if user_id:
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            # Add to Librarian group
            librarian_group, _ = Group.objects.get_or_create(name='Librarian')
            user.groups.add(librarian_group)
            
            # Remove from Patron group
            patron_group = Group.objects.get(name='Patron')
            user.groups.remove(patron_group)
            
    return redirect('catalog:librarian_dashboard')  # Refresh the page



@login_required
def demote_to_patron(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Remove the user from the Librarian group
    librarian_group = Group.objects.get(name="Librarian")
    user.groups.remove(librarian_group)

    return redirect('catalog:librarian_dashboard')
    return render(request, 'mysite/upload_picture.html', {'form': form})

@login_required
def upload_picture(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['profile_picture']
            file_name = f'profile_pictures/{request.user.username}/{file.name}'
            file_url = default_storage.save(file_name, ContentFile(file.read()))

            return render(request, 'mysite/upload_picture.html', {'form': form, 'file_url': default_storage.url(file_url), 'message': "Upload successful!"})
    else:
        form = ProfilePictureForm()

    return render(request, 'mysite/upload_picture.html', {'form': form})

@login_required
def upload_item(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            # Safely get the uploaded file if it exists
            uploaded_file = request.FILES.get('profile_picture')
            if uploaded_file:
                file_name = f'items/{request.user.username}/{uploaded_file.name}'
                file_url = default_storage.save(file_name, ContentFile(uploaded_file.read()))

                return render(request, 'mysite/upload_item.html', {
                    'form': form,
                    'file_url': default_storage.url(file_url),
                    'message': "Upload successful!"
                })
            else:
                return render(request, 'mysite/upload_item.html', {
                    'form': form,
                    'message': "No file was uploaded."
                })
    else:
        form = ProfilePictureForm()

    return render(request, 'mysite/upload_item.html', {'form': form})


@login_required
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    
    # Only authenticated users can leave reviews
    user_review = None
    can_review = False
    
    if request.user.is_authenticated:
        user_review = Review.objects.filter(game=game, user=request.user).first()
        can_review = True
        
        if request.method == 'POST':
            form = ReviewForm(request.POST, instance=user_review)
            if form.is_valid():
                review = form.save(commit=False)
                review.game = game
                review.user = request.user
                review.save()
                
                # Update average rating
                game.update_rating()
                return redirect('catalog:game_detail', game_id=game.id)
    
    # Get all reviews for this game
    reviews = Review.objects.filter(game=game)
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    # Create form for new review (if authenticated)
    form = ReviewForm(instance=user_review) if request.user.is_authenticated else None
    
    return render(request, 'mysite/game_detail.html', {
        'game': game,
        'reviews': reviews,
        'form': form,
        'avg_rating': avg_rating,
        'can_review': can_review,
        'has_reviewed': user_review is not None
    })
    

# ---------------------- Search Views ----------------------

def search_items(request):
    """Search functionality for games and collections with proper access control"""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    collection_id = request.GET.get('collection_id', None)
    
    results = {
        'games': [],
        'collections': [],
        'query': query,
        'search_type': search_type
    }
    
    if not query:
        return render(request, "mysite/search_results.html", results)
    
    # Search within a specific collection
    if collection_id:
        try:
            collection = Collection.objects.get(id=collection_id)
            
            # Check if user has access to this collection
            if not collection.is_public and request.user.is_authenticated:
                if collection.creator != request.user and not request.user.groups.filter(name='Librarian').exists():
                    return render(request, "mysite/unauthorized.html", 
                                 {"message": "You don't have permission to search this collection"})
            elif not collection.is_public and not request.user.is_authenticated:
                return render(request, "mysite/unauthorized.html", 
                             {"message": "You need to login to access this collection"})
                
            # Search for games within the collection
            games = collection.games.filter(
                Q(title__icontains=query) | 
                Q(platform__icontains=query) | 
                Q(genre__icontains=query)
            )
            
            results['games'] = games
            results['collection'] = collection
            return render(request, "mysite/search_results.html", results)
            
        except Collection.DoesNotExist:
            pass
    
    # General search across all accessible content
    if search_type in ['all', 'games']:
        if request.user.is_authenticated:
            # For authenticated users
            # Get all games not in any collection or in public collections
            games = Game.objects.filter(
                Q(title__icontains=query) | 
                Q(platform__icontains=query) | 
                Q(genre__icontains=query)
            )
            
            # Filter out games that are only in private collections
            # unless the user is the creator or a librarian
            filtered_games = []
            for game in games:
                # If game isn't in any collection, include it
                if not game.collections.exists():
                    filtered_games.append(game)
                    continue
                
                # If game is in at least one public collection, include it
                if game.collections.filter(is_public=True).exists():
                    filtered_games.append(game)
                    continue
                    
                # If game is only in private collections, check if user has access
                private_collections = game.collections.filter(is_public=False)
                if private_collections.filter(creator=request.user).exists() or request.user.groups.filter(name='Librarian').exists():
                    filtered_games.append(game)
                    
            results['games'] = filtered_games
        else:
            # For anonymous users - only show games not in collections or in public collections
            games_in_private = Game.objects.filter(collections__is_public=False).distinct()
            games = Game.objects.filter(
                Q(title__icontains=query) | 
                Q(platform__icontains=query) | 
                Q(genre__icontains=query)
            ).exclude(id__in=games_in_private.values_list('id', flat=True))
            
            results['games'] = games
    
    if search_type in ['all', 'collections']:
        if request.user.is_authenticated:
            # For authenticated users
            # Get all public collections and private collections the user owns
            collections = Collection.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query)
            ).filter(
                Q(is_public=True) | 
                Q(creator=request.user)
            )
            
            # If user is a librarian, also include all private collections
            if request.user.groups.filter(name='Librarian').exists():
                collections = Collection.objects.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query)
                )
                
            results['collections'] = collections
        else:
            # For anonymous users - only show public collections
            collections = Collection.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query)
            ).filter(is_public=True)
            
            results['collections'] = collections
    
    return render(request, "mysite/search_results.html", results)

    
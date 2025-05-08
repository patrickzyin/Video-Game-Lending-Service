from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg  
from django.core.validators import MinValueValidator, MaxValueValidator
from catalog.storage_backends import CatalogMediaStorage

class Game(models.Model):
    title = models.CharField(max_length=100)
    platform = models.CharField(max_length=50)
    genre = models.CharField(max_length=50)
    available = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='',
        storage=CatalogMediaStorage(),
        blank=True,
        null=True,
        default='items/default_game_image.png'  
    )

    def get_average_rating(self):
        """Calculate and return the average rating for this game"""
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    @property
    def cached_avg_rating(self):
        """Cached average rating for performance"""
        if hasattr(self, 'avg_rating'):
            return self.avg_rating
        return self.get_average_rating()
    
    def __str__(self):
        return f"{self.title} ({self.platform})"

class Collection(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    games = models.ManyToManyField(Game, related_name="collections")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="collections", null=True)
    is_public = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class BorrowedGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    borrowed_date = models.DateField(auto_now_add=True)
    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} borrowed {self.game.title}"

class BorrowRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    request_date = models.DateField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    denied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} requested {self.game.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
    google_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username

class Review(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('game', 'user')  # One review per user per game

    def __str__(self):
        return f"{self.user.username}'s {self.rating}★ review for {self.game.title}"

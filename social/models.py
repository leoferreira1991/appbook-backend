from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User
from books.models import Book

class Review(models.Model):
    user = models.ForeignKey(User, related_name='social_reviews', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='social_reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.user.username} - {self.book.title} ({self.rating}/5)'

class Highlight(models.Model):
    user = models.ForeignKey(User, related_name='social_highlights', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='social_highlights', on_delete=models.CASCADE, null=True, blank=True)
    # For OL books not in our DB
    ol_key = models.CharField(max_length=100, blank=True, null=True)
    ol_title = models.CharField(max_length=255, blank=True, null=True)
    
    text = models.TextField()
    chapter = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Highlight by {self.user.username} - "{self.text[:20]}..."'

class SocialInteraction(models.Model):
    TYPE_LIKE = 'like'
    TYPE_COMMENT = 'comment'
    CHOICES = [(TYPE_LIKE, 'Like'), (TYPE_COMMENT, 'Comment')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    interaction_type = models.CharField(max_length=10, choices=CHOICES)
    comment_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.interaction_type} on {self.content_object}'


class SocialProfile(models.Model):
    PLATFORM_CHOICES = [
        ('tiktok', 'TikTok'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
    ]
    PROFILE_TYPE_CHOICES = [
        ('booktoker', 'Booktoker'),
        ('publisher', 'Editorial'),
        ('author', 'Autor'),
    ]

    name = models.CharField(max_length=255)
    handle = models.CharField(max_length=100)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    profile_type = models.CharField(max_length=20, choices=PROFILE_TYPE_CHOICES)
    bio = models.TextField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    profile_url = models.URLField(help_text="Deep link or direct URL to the profile")
    featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} (@{self.handle}) on {self.platform}"

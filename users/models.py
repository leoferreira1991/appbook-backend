from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField

class User(AbstractUser):
    is_booktoker = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    avatar = CloudinaryField('avatar', blank=True, null=True)
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    avatar_url = models.URLField(blank=True, null=True, help_text="Fallback URL to profile photo")
    social_links = models.JSONField(default=dict, blank=True, help_text="Links to TikTok, Instagram, etc.")
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    # Reading preferences for AI recommendations
    favorite_authors = models.TextField(
        blank=True, null=True,
        help_text="Comma-separated list of favorite authors, e.g. 'George R.R. Martin, Stephen King'"
    )
    favorite_publishers = models.TextField(
        blank=True, null=True,
        help_text="Comma-separated list of favorite publishers, e.g. 'Planeta, Salamandra'"
    )

    def __str__(self):
        return self.username

class Achievement(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_name = models.CharField(max_length=50, help_text="Flutter Icon name or code")
    xp_reward = models.IntegerField(default=50)

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, related_name='achievements', on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

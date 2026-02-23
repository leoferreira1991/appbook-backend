from django.db import models
from cloudinary.models import CloudinaryField
from users.models import User

class Author(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Series(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, related_name='books', on_delete=models.CASCADE)
    series = models.ForeignKey(Series, related_name='books', on_delete=models.SET_NULL, null=True, blank=True)
    series_number = models.FloatField(null=True, blank=True)
    synopsis = models.TextField(blank=True, null=True)
    cover_image_url = models.URLField(blank=True, null=True)
    trivia = models.TextField(blank=True, null=True)
    purchase_links = models.JSONField(default=list, blank=True, help_text="List of dictionaries with store name and URL")
    
    # New detailed info fields
    publish_date = models.CharField(max_length=50, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    categories = models.CharField(max_length=255, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    page_count = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.title

class ReadingProgress(models.Model):
    user = models.ForeignKey(User, related_name='reading_progress', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='readers_progress', on_delete=models.CASCADE)
    current_chapter = models.IntegerField(default=0)
    total_chapters = models.IntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.user.username} - {self.book.title}'


class UserBook(models.Model):
    STATUS_READING = 'reading'
    STATUS_READ = 'read'
    STATUS_WANT = 'want_to_read'
    STATUS_SEARCHING = 'searching'

    STATUS_CHOICES = [
        (STATUS_READING, 'Leyendo ahora'),
        (STATUS_READ, 'Leído'),
        (STATUS_WANT, 'Quiero leer'),
        (STATUS_SEARCHING, 'Buscando conseguir'),
    ]

    user = models.ForeignKey(User, related_name='user_books', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='in_libraries', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WANT)
    notes = models.TextField(blank=True, null=True, help_text="Private notes about this book")
    rating = models.FloatField(null=True, blank=True, help_text="Rating 0-5 when finished")
    review = models.TextField(blank=True, null=True, help_text="Final review when finished")
    chapter_notes = models.JSONField(default=list, blank=True, help_text="List of {chapter, note, created_at} dicts")
    current_chapter = models.IntegerField(default=0)
    total_chapters = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Open Library data (for books not in our DB yet)
    ol_title = models.CharField(max_length=255, blank=True, null=True)
    ol_author = models.CharField(max_length=255, blank=True, null=True)
    ol_cover_url = models.URLField(blank=True, null=True)
    ol_key = models.CharField(max_length=100, blank=True, null=True)
    custom_cover = CloudinaryField('cover', blank=True, null=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f'{self.user.username} - {self.book.title} ({self.status})'


class UserBookExternal(models.Model):
    """For books found in Open Library but not yet in our DB."""
    STATUS_CHOICES = UserBook.STATUS_CHOICES

    user = models.ForeignKey(User, related_name='external_books', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=UserBook.STATUS_WANT)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    cover_url = models.URLField(blank=True, null=True)
    ol_key = models.CharField(max_length=100, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.FloatField(null=True, blank=True)
    review = models.TextField(blank=True, null=True)
    chapter_notes = models.JSONField(default=list, blank=True, help_text="List of {chapter, note, created_at} dicts")
    current_chapter = models.IntegerField(default=0)
    total_chapters = models.IntegerField(default=0)
    custom_cover = CloudinaryField('cover', blank=True, null=True)

    # New detailed info fields
    publish_date = models.CharField(max_length=50, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    categories = models.CharField(max_length=255, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    page_count = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'ol_key')

    def __str__(self):
        return f'{self.user.username} - {self.title} ({self.status})'


class BookCoverContribution(models.Model):
    """Community-uploaded book covers. Shared with all users of the same edition."""
    user = models.ForeignKey(User, related_name='cover_contributions', on_delete=models.CASCADE)
    ol_key = models.CharField(max_length=100, help_text='Open Library key e.g. /works/OL166894W')
    cover_url = models.URLField(help_text='Cloudinary URL of the uploaded cover')
    title = models.CharField(max_length=255, blank=True, help_text='Book title for display')
    votes = models.IntegerField(default=0, help_text='Community upvotes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'ol_key')
        ordering = ['-votes', '-created_at']

    def __str__(self):
        return f'{self.user.username} cover for {self.ol_key}'


class ReadingChallenge(models.Model):
    CHALLENGE_TYPE_CHOICES = [
        ('finish_by_date', 'Terminar para una fecha'),
        ('pages_per_day', 'Páginas por día'),
        ('chapters_per_day', 'Capítulos por día'),
        ('custom', 'Personalizado'),
    ]

    user = models.ForeignKey(User, related_name='reading_challenges', on_delete=models.CASCADE)
    book_title = models.CharField(max_length=255)
    book_author = models.CharField(max_length=255, blank=True)
    custom_cover = CloudinaryField('cover', blank=True, null=True)
    cover_url = models.URLField(blank=True, null=True)
    ol_key = models.CharField(max_length=100, blank=True, null=True)
    
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPE_CHOICES)
    total_pages = models.IntegerField(default=0)
    total_chapters = models.IntegerField(default=0)
    
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    
    daily_goal_pages = models.IntegerField(default=0)
    daily_goal_chapters = models.IntegerField(default=0)
    
    current_page = models.IntegerField(default=0)
    current_chapter = models.IntegerField(default=0)
    
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    reminder_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.book_title} ({self.challenge_type})"


class DailyReadingLog(models.Model):
    challenge = models.ForeignKey(ReadingChallenge, related_name='logs', on_delete=models.CASCADE)
    date = models.DateField()
    pages_read = models.IntegerField(default=0)
    chapters_read = models.IntegerField(default=0)
    end_page = models.IntegerField(default=0)
    end_chapter = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('challenge', 'date')

    def __str__(self):
        return f"{self.challenge.book_title} - {self.date}"


class CachedRecommendation(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='recommendation_cache')
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cache for {self.user.username}"

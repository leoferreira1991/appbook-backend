"""Auto-check and award achievements based on user activity."""
from users.models import Achievement, UserAchievement
from books.models import UserBookExternal


def check_achievements(user):
    """Check all achievements for a user and award any newly earned ones."""
    awarded = []
    
    # Get user's book stats
    total_books = UserBookExternal.objects.filter(user=user).count()
    read_books = UserBookExternal.objects.filter(user=user, status='read').count()
    
    # Get unique genres
    genres = set()
    cats = UserBookExternal.objects.filter(user=user).exclude(
        categories__isnull=True
    ).exclude(categories='').values_list('categories', flat=True)
    for c in cats:
        for g in c.split(','):
            g = g.strip()
            if g:
                genres.add(g)
    
    # Genre counts for genre_master
    from collections import Counter
    genre_counts = Counter()
    for c in cats:
        for g in c.split(','):
            g = g.strip()
            if g:
                genre_counts[g] += 1
    max_genre_count = max(genre_counts.values()) if genre_counts else 0
    
    # Book count achievements
    book_checks = [
        ('first_book', total_books >= 1),
        ('five_books', total_books >= 5),
        ('ten_books', total_books >= 10),
        ('twenty_books', total_books >= 20),
    ]
    
    # Read count achievements
    read_checks = [
        ('first_read', read_books >= 1),
        ('five_read', read_books >= 5),
        ('ten_read', read_books >= 10),
    ]
    
    # Genre achievements
    genre_checks = [
        ('diverse_reader', len(genres) >= 3),
        ('genre_master', max_genre_count >= 5),
    ]
    
    # Highlight check
    from books.models import BookHighlight
    has_highlight = BookHighlight.objects.filter(
        book__user=user
    ).exists() if hasattr(UserBookExternal, 'highlights') else False
    # Fallback: check if BookHighlight has any for user's books
    try:
        book_ids = UserBookExternal.objects.filter(user=user).values_list('id', flat=True)
        has_highlight = BookHighlight.objects.filter(book_id__in=book_ids).exists()
    except Exception:
        has_highlight = False
    
    highlight_checks = [
        ('first_highlight', has_highlight),
    ]
    
    # Challenge check
    from books.models import ReadingChallenge
    has_challenge = ReadingChallenge.objects.filter(user=user).exists()
    challenge_checks = [
        ('first_challenge', has_challenge),
    ]
    
    all_checks = book_checks + read_checks + genre_checks + highlight_checks + challenge_checks
    
    for code, condition in all_checks:
        if condition:
            try:
                achievement = Achievement.objects.get(code=code)
                _, created = UserAchievement.objects.get_or_create(
                    user=user, achievement=achievement
                )
                if created:
                    # Award XP
                    user.xp = (user.xp or 0) + achievement.xp_reward
                    user.save(update_fields=['xp'])
                    awarded.append({
                        'name': achievement.name,
                        'description': achievement.description,
                        'xp_reward': achievement.xp_reward,
                    })
            except Achievement.DoesNotExist:
                pass
    
    return awarded

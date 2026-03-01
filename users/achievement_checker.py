"""Auto-check and award achievements based on user activity."""
from users.models import Achievement, UserAchievement


def check_achievements(user):
    """Check all achievements for a user and award any newly earned ones."""
    from books.models import UserBookExternal, ReadingChallenge
    
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
    all_checks = [
        ('first_book', total_books >= 1),
        ('five_books', total_books >= 5),
        ('ten_books', total_books >= 10),
        ('twenty_books', total_books >= 20),
        ('first_read', read_books >= 1),
        ('five_read', read_books >= 5),
        ('ten_read', read_books >= 10),
        ('diverse_reader', len(genres) >= 3),
        ('genre_master', max_genre_count >= 5),
        ('first_challenge', ReadingChallenge.objects.filter(user=user).exists()),
    ]
    
    for code, condition in all_checks:
        if condition:
            try:
                achievement = Achievement.objects.get(code=code)
                _, created = UserAchievement.objects.get_or_create(
                    user=user, achievement=achievement
                )
                if created:
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

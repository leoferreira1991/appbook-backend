from rest_framework import views, permissions
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import ReadingChallenge, DailyReadingLog, UserBook, UserBookExternal
from users.models import UserAchievement
from django.utils import timezone
from datetime import timedelta
from .stats_utils import get_level_threshold

class StatsSummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # 1. Total Stats
        total_pages = DailyReadingLog.objects.filter(challenge__user=user).aggregate(Sum('pages_read'))['pages_read__sum'] or 0
        
        # Calculate chapters from both challenge logs AND direct user reading updates
        # To avoid double counting now that we sync challenge -> book:
        # We sum current_chapter from all books (which includes challenge progress)
        chapters_from_books = UserBook.objects.filter(user=user).aggregate(Sum('current_chapter'))['current_chapter__sum'] or 0
        chapters_from_ext = UserBookExternal.objects.filter(user=user).aggregate(Sum('current_chapter'))['current_chapter__sum'] or 0
        total_chapters = chapters_from_books + chapters_from_ext
        
        books_finished = UserBook.objects.filter(user=user, status='read').count()
        
        # 2. Streak Calculation (Simplistic)
        today = timezone.now().date()
        streak = 0
        current_date = today
        
        # Check if they read today or yesterday to continue the streak
        has_read_today = DailyReadingLog.objects.filter(challenge__user=user, date=today).exists()
        if not has_read_today:
            current_date = today - timedelta(days=1)
            
        while DailyReadingLog.objects.filter(challenge__user=user, date=current_date).exists():
            streak += 1
            current_date -= timedelta(days=1)

        # 3. Level Progress
        next_level_xp = get_level_threshold(user.level)
        xp_progress = (user.xp / next_level_xp) if next_level_xp > 0 else 0
        
        # 4. Earned Achievements
        earned = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')[:5]
        achievements_data = [
            {
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon_name': ua.achievement.icon_name,
                'earned_at': ua.earned_at
            } for ua in earned
        ]

        # 5. Genre breakdown (from finished books if we had genres, let's mock for now)
        genres = {
            'Fantasía': 45,
            'Romance': 25,
            'Ciencia Ficción': 15,
            'Otros': 15
        }

        return Response({
            'user': {
                'username': user.username,
                'level': user.level,
                'xp': user.xp,
                'next_level_xp': next_level_xp,
                'xp_progress': xp_progress,
            },
            'stats': {
                'total_pages': total_pages,
                'total_chapters': total_chapters,
                'books_finished': books_finished,
                'streak': streak,
            },
            'achievements': achievements_data,
            'genres': genres,
        })

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ReadingChallenge, DailyReadingLog
from .serializers import ReadingChallengeSerializer, DailyReadingLogSerializer
from .stats_utils import calculate_xp_for_reading, add_xp_to_user, check_reading_achievements
from django.utils import timezone
from datetime import timedelta
import json
from openai import OpenAI
from django.conf import settings

class ReadingChallengeViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingChallengeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReadingChallenge.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def log(self, request, pk=None):
        challenge = self.get_object()
        pages_read = int(request.data.get('pages_read', 0))
        chapters_read = int(request.data.get('chapters_read', 0))
        end_page = int(request.data.get('end_page', 0))
        end_chapter = int(request.data.get('end_chapter', 0))
        notes = request.data.get('notes', '')
        date = request.data.get('date', timezone.now().date())

        log, created = DailyReadingLog.objects.update_or_create(
            challenge=challenge,
            date=date,
            defaults={
                'pages_read': pages_read,
                'chapters_read': chapters_read,
                'end_page': end_page,
                'end_chapter': end_chapter,
                'notes': notes
            }
        )

        # Update challenge progress
        if end_page > challenge.current_page:
            challenge.current_page = end_page
        if end_chapter > challenge.current_chapter:
            challenge.current_chapter = end_chapter
        
        challenge.save()
        
        # Reward XP
        xp_earned = calculate_xp_for_reading(pages=pages_read, chapters=chapters_read)
        leveled_up, new_level = add_xp_to_user(request.user, xp_earned)
        
        # Sync progress with Library
        from .models import UserBook, UserBookExternal
        # Try finding the book in library using ol_key or title
        if challenge.ol_key:
            UserBookExternal.objects.filter(user=request.user, ol_key=challenge.ol_key).update(current_chapter=challenge.current_chapter)
        else:
            UserBook.objects.filter(user=request.user, book__title=challenge.book_title).update(current_chapter=challenge.current_chapter)

        # Check for achievements
        new_achievements = check_reading_achievements(request.user, log)
        
        data = DailyReadingLogSerializer(log).data
        data['xp_earned'] = xp_earned
        data['leveled_up'] = leveled_up
        data['new_level'] = new_level
        data['new_achievements'] = [a.name for a in new_achievements]
        
        return Response(data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        challenge = self.get_object()
        
        # Mark challenge as completed
        challenge.is_completed = True
        challenge.save()
        
        # Sync progress and status with Library
        from .models import UserBook, UserBookExternal
        
        # Mark as read (STATUS_READ is 'read')
        status_read = 'read'
        
        if challenge.ol_key:
            UserBookExternal.objects.filter(user=request.user, ol_key=challenge.ol_key).update(
                status=status_read,
                current_chapter=challenge.total_chapters if challenge.total_chapters > 0 else challenge.current_chapter
            )
        else:
            UserBook.objects.filter(user=request.user, book__title=challenge.book_title).update(
                status=status_read,
                current_chapter=challenge.total_chapters if challenge.total_chapters > 0 else challenge.current_chapter
            )
            
        return Response({'status': 'completed', 'message': 'Desafío y libro marcados como completados'})

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        challenge = self.get_object()
        
        if challenge.challenge_type != 'finish_by_date' or not challenge.end_date:
            # Fallback for other types or if end_date missing
            remaining_pages = max(0, challenge.total_pages - challenge.current_page)
            daily = challenge.daily_goal_pages or 20
            days = (remaining_pages // daily) + 1
            fallback = {'schedule': [{'day': i+1, 'pages_to_read': daily, 'description': 'Tu meta diaria'} for i in range(min(days, 30))]}
            return Response(fallback)

        # Use AI to generate a smart schedule
        days_left = (challenge.end_date - timezone.now().date()).days
        if days_left <= 0:
            days_left = 1
            
        remaining_pages = max(0, challenge.total_pages - challenge.current_page)
        
        prompt = (
            f"El usuario quiere terminar el libro '{challenge.book_title}' para el {challenge.end_date}. "
            f"Le faltan {remaining_pages} páginas. Genera un plan de lectura para los próximos {days_left} días. "
            "Responde con un JSON que tenga una lista 'schedule' con objetos {'day': 1, 'pages_to_read': X, 'description': '...'}. "
            "Hazlo motivador y variable (algunos días más, otros menos si es posible). "
            "Responde SOLO con el JSON."
        )

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': 'Eres un coach de lectura motivador. Responde solo con JSON válido.'},
                    {'role': 'user', 'content': prompt},
                ],
                response_format={'type': 'json_object'},
                max_tokens=1000,
            )
            data = json.loads(response.choices[0].message.content)
            return Response(data)
        except Exception as e:
            print(f"Error generating AI schedule: {e}")
            # Fallback simple logic
            avg = remaining_pages // days_left
            fallback = {'schedule': [{'day': i+1, 'pages_to_read': avg, 'description': 'Lectura regular'} for i in range(min(days_left, 30))]}
            return Response(fallback)

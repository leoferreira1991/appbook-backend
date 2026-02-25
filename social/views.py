from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .models import Review, Highlight, SocialInteraction, SocialProfile, DirectMessage
from .serializers import ReviewSerializer, HighlightSerializer, SocialInteractionSerializer, UserCompactSerializer, SocialProfileSerializer, DirectMessageSerializer
from users.models import User
import datetime

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().select_related('user').order_by('-created_at')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class HighlightViewSet(viewsets.ModelViewSet):
    queryset = Highlight.objects.all().select_related('user').order_by('-created_at')
    serializer_class = HighlightSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FeedView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        following_ids = list(user.following.values_list('id', flat=True))
        
        # 1. Get from Following
        reviews = Review.objects.filter(user_id__in=following_ids).select_related('user').order_by('-created_at')[:20]
        highlights = Highlight.objects.filter(user_id__in=following_ids).select_related('user').order_by('-created_at')[:20]
        
        # 2. Discovery: If feed is low, add global popular/recent items
        if reviews.count() + highlights.count() < 10:
            global_reviews = Review.objects.exclude(user_id__in=following_ids).exclude(user=user).select_related('user').order_by('-created_at')[:10]
            global_highlights = Highlight.objects.exclude(user_id__in=following_ids).exclude(user=user).select_related('user').order_by('-created_at')[:10]
            reviews = list(reviews) + list(global_reviews)
            highlights = list(highlights) + list(global_highlights)

        from books.models import ReadingChallenge
        from books.serializers import ReadingChallengeSerializer
        
        challenges = ReadingChallenge.objects.filter(user_id__in=following_ids, is_active=True).select_related('user').order_by('-created_at')[:20]

        # Aggregate into a single list
        activities = []
        serializer_context = {'request': request}
        
        for r in reviews:
            activities.append({
                'type': 'review',
                'id': r.id,
                'user': UserCompactSerializer(r.user, context=serializer_context).data,
                'created_at': r.created_at,
                'data': ReviewSerializer(r, context=serializer_context).data
            })
        for h in highlights:
            activities.append({
                'type': 'highlight',
                'id': h.id,
                'user': UserCompactSerializer(h.user, context=serializer_context).data,
                'created_at': h.created_at,
                'data': HighlightSerializer(h, context=serializer_context).data
            })
        for c in challenges:
            activities.append({
                'type': 'challenge',
                'id': c.id,
                'user': UserCompactSerializer(c.user, context=serializer_context).data,
                'created_at': c.created_at,
                'data': ReadingChallengeSerializer(c, context=serializer_context).data
            })
            
        # Sort by date
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Return slice
        result_slice = activities[:40] if len(activities) > 40 else activities
        return Response(result_slice)

class FollowUserView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        user_to_follow = get_object_or_404(User, id=user_id)
        if user_to_follow == request.user:
            return Response({'error': 'No podés seguirte a vos mismo'}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.following.add(user_to_follow)
        return Response({'status': 'follow_ok'})

    def delete(self, request, user_id):
        user_to_unfollow = get_object_or_404(User, id=user_id)
        request.user.following.remove(user_to_unfollow)
        return Response({'status': 'unfollow_ok'})

class InteractionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Expects: target_type ('review'|'highlight'), target_id, interaction_type ('like'|'comment'), comment_text (optional)
        target_type = request.data.get('target_type')
        target_id = request.data.get('target_id')
        
        if target_type == 'review':
            model = Review
        elif target_type == 'highlight':
            model = Highlight
        elif target_type == 'reading_progress':
            from books.models import ReadingProgress
            model = ReadingProgress
        else:
            return Response({'error': 'Target type inválido'}, status=status.HTTP_400_BAD_REQUEST)
            
        obj = get_object_or_404(model, id=target_id)
        content_type = ContentType.objects.get_for_model(obj)
        
        interaction, created = SocialInteraction.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=obj.id,
            interaction_type=request.data.get('interaction_type'),
            defaults={'comment_text': request.data.get('comment_text')}
        )
        
        if not created and request.data.get('interaction_type') == 'like':
            # Toggle like
            interaction.delete()
            return Response({'status': 'unliked'})
            
        return Response(SocialInteractionSerializer(interaction).data, status=status.HTTP_201_CREATED)


class SocialProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SocialProfile.objects.all()
    serializer_class = SocialProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = SocialProfile.objects.all()
        platform = self.request.query_params.get('platform')
        profile_type = self.request.query_params.get('type')
        if platform:
            queryset = queryset.filter(platform=platform)
        if profile_type:
            queryset = queryset.filter(profile_type=profile_type)
        return queryset

from django.db.models import Q

class DirectMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DirectMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return messages where user is sender or receiver
        user = self.request.user
        return DirectMessage.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-created_at')

    def perform_create(self, serializer):
        # receiver_id is passed in the request data, we assign sender as the current user
        receiver_id = self.request.data.get('receiver_id')
        receiver = get_object_or_404(User, id=receiver_id)
        serializer.save(sender=self.request.user, receiver=receiver)


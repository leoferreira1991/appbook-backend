from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.decorators.cache import cache_page
from .views import ReviewViewSet, HighlightViewSet, FeedView, FollowUserView, InteractionView, SocialProfileViewSet, DirectMessageViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='social_reviews')
router.register(r'highlights', HighlightViewSet, basename='social_highlights')
router.register(r'profiles', SocialProfileViewSet, basename='social_profiles')
router.register(r'messages', DirectMessageViewSet, basename='social_messages')

urlpatterns = [
    path('', include(router.urls)),
    path('feed/', cache_page(60 * 5)(FeedView.as_view()), name='social-feed'),
    path('follow/<int:user_id>/', FollowUserView.as_view(), name='follow-user'),
    path('interact/', InteractionView.as_view(), name='social-interact'),
]

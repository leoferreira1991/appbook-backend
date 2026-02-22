from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, HighlightViewSet, FeedView, FollowUserView, InteractionView, SocialProfileViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet)
router.register(r'highlights', HighlightViewSet)
router.register(r'profiles', SocialProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('feed/', FeedView.as_view(), name='social-feed'),
    path('follow/<int:user_id>/', FollowUserView.as_view(), name='follow-user'),
    path('interact/', InteractionView.as_view(), name='social-interact'),
]

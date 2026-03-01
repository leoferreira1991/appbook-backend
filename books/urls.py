from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, AuthorViewSet, SeriesViewSet, ReadingProgressViewSet, UserBookViewSet, UserBookExternalViewSet, BookCoverContributionViewSet
from .recommendations import BookRecommendationsView
from .suggest_similar import SuggestSimilarView
from .challenge_views import ReadingChallengeViewSet
from .stats_views import StatsSummaryView
from .ai_search import AISearchView
from .ai_enrichment import AIEnrichmentView, AIReviewView
from .author_dedup import AuthorDedupView, AutoMergeAuthorsView
from .bug_report_views import BugReportView
from .public_library_views import PublicLibraryView

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'series', SeriesViewSet)
router.register(r'books', BookViewSet)
router.register(r'my-progress', ReadingProgressViewSet, basename='readingprogress')
router.register(r'my-library', UserBookViewSet, basename='userbook')
router.register(r'my-library-external', UserBookExternalViewSet, basename='userbookexternal')
router.register(r'community-covers', BookCoverContributionViewSet, basename='communitycover')
router.register(r'challenges', ReadingChallengeViewSet, basename='readingchallenge')
router.register(r'suggest-similar', SuggestSimilarView, basename='suggestsimilar')

urlpatterns = [
    path('', include(router.urls)),
    path('recommendations/', BookRecommendationsView.as_view(), name='book-recommendations'),
    path('stats/summary/', StatsSummaryView.as_view(), name='stats-summary'),
    path('ai-search/', AISearchView.as_view(), name='ai-search'),
    path('ai-enrich/', AIEnrichmentView.as_view(), name='ai-enrich'),
    path('ai-review/', AIReviewView.as_view(), name='ai-review'),
    path('authors/dedup/', AuthorDedupView.as_view(), name='author-dedup'),
    path('authors/auto-merge/', AutoMergeAuthorsView.as_view(), name='author-auto-merge'),
    path('bug-report/', BugReportView.as_view(), name='bug-report'),
    path('public-library/<int:user_id>/', PublicLibraryView.as_view(), name='public-library'),
]


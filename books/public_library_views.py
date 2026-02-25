from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserBook, UserBookExternal
from django.contrib.auth import get_user_model

User = get_user_model()

class PublicLibraryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        # Get books from both models that are read or want_to_read
        internal_books = UserBook.objects.filter(
            user=target_user,
            status__in=[UserBook.STATUS_READ, UserBook.STATUS_WANT]
        ).select_related('book', 'book__author')

        external_books = UserBookExternal.objects.filter(
            user=target_user,
            status__in=[UserBookExternal.STATUS_READ, UserBookExternal.STATUS_WANT]
        )

        library = []

        # Format internal books
        for ub in internal_books:
            library.append({
                'id': ub.id,
                'source': 'internal',
                'title': ub.book.title,
                'author': ub.book.author.name if ub.book.author else 'Unknown',
                'category': ub.book.categories or 'Sin clasificar',
                'cover_url': ub.custom_cover.url if ub.custom_cover else ub.book.cover_image_url,
                'status': ub.status,
                'added_at': ub.added_at,
            })

        # Format external books
        for ube in external_books:
            library.append({
                'id': ube.id,
                'source': 'external',
                'title': ube.title,
                'author': ube.author,
                'category': ube.categories or 'Sin clasificar',
                'cover_url': ube.custom_cover.url if ube.custom_cover else ube.cover_url,
                'status': ube.status,
                'added_at': ube.added_at,
            })

        # Process and structure the data
        # Group by Author -> Category -> Oldest to Newest
        raw_list = sorted(library, key=lambda x: (
            x['author'].lower(),
            x['category'].lower(),
            x['added_at']
        ))

        return Response(raw_list)

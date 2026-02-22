from rest_framework import viewsets, permissions, parsers, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Book, Author, Series, ReadingProgress, UserBook, UserBookExternal, BookCoverContribution
from .serializers import (
    BookSerializer, AuthorSerializer, SeriesSerializer,
    ReadingProgressSerializer, UserBookSerializer, UserBookExternalSerializer,
    BookCoverContributionSerializer,
)
import cloudinary.uploader

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class SeriesViewSet(viewsets.ModelViewSet):
    queryset = Series.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ReadingProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReadingProgress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserBookViewSet(viewsets.ModelViewSet):
    """Manages books in user's library (books already in our DB)."""
    serializer_class = UserBookSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser]

    def get_queryset(self):
        qs = UserBook.objects.filter(user=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        # Clear recommendation cache to force refresh with new data
        from .models import CachedRecommendation
        CachedRecommendation.objects.filter(user=self.request.user).update(data={})
        serializer.save(user=self.request.user)


class UserBookExternalViewSet(viewsets.ModelViewSet):
    """Manages books from Open Library (not yet in our DB)."""
    serializer_class = UserBookExternalSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser]

    def get_queryset(self):
        qs = UserBookExternal.objects.filter(user=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        print(f"--- ADDING EXTERNAL BOOK ---")
        ol_key = serializer.validated_data.get('ol_key', '')
        # Clear recommendation cache to force refresh with new data
        from .models import CachedRecommendation
        CachedRecommendation.objects.filter(user=self.request.user).update(data={})
        
        try:
            if ol_key:
                obj, created = UserBookExternal.objects.update_or_create(
                    user=self.request.user,
                    ol_key=ol_key,
                    defaults={**serializer.validated_data, 'user': self.request.user}
                )
                serializer.instance = obj
                print(f"Success: {'Created' if created else 'Updated'} {obj}")
            else:
                obj = serializer.save(user=self.request.user)
                # Ensure the instance is attached for serialization
                serializer.instance = obj
                print(f"Success: Saved new {obj}")
        except Exception as e:
            print(f"ERROR adding book: {str(e)}")
            raise e


class BookCoverContributionViewSet(viewsets.ModelViewSet):
    """Community book covers — users upload covers, shared with everyone."""
    serializer_class = BookCoverContributionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    def get_queryset(self):
        qs = BookCoverContribution.objects.all()
        ol_key = self.request.query_params.get('ol_key')
        if ol_key:
            qs = qs.filter(ol_key=ol_key)
        return qs

    def create(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        ol_key = request.data.get('ol_key', '').strip()
        title = request.data.get('title', '').strip()

        if not image_file:
            return Response({'error': 'Se requiere una imagen.'}, status=status.HTTP_400_BAD_REQUEST)
        if not ol_key:
            return Response({'error': 'Se requiere ol_key.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder='book_covers',
                public_id=f'{ol_key.replace("/", "_")}_{request.user.id}',
                overwrite=True,
                resource_type='image',
            )
            cover_url = upload_result.get('secure_url', '')

            # Upsert: one cover per user per book
            obj, created = BookCoverContribution.objects.update_or_create(
                user=request.user,
                ol_key=ol_key,
                defaults={'cover_url': cover_url, 'title': title}
            )
            serializer = self.get_serializer(obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except Exception as e:
            print(f"Cloudinary upload error: {e}")
            return Response({'error': 'Error al subir la imagen. Verificá las credenciales de Cloudinary.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='vote')
    def vote(self, request, pk=None):
        """Upvote a community cover."""
        cover = self.get_object()
        cover.votes += 1
        cover.save()
        return Response({'votes': cover.votes})

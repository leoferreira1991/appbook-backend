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

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def manual_create(self, request):
        """Allows users to manually add a book to the catalog and their library."""
        title = request.data.get('title', '').strip()
        author_name = request.data.get('author_name', '').strip()
        isbn = request.data.get('isbn', '').strip()
        total_chapters = int(request.data.get('total_chapters', 10))
        status_val = request.data.get('status', UserBook.STATUS_WANT)
        image_file = request.FILES.get('cover')

        if not title or not author_name:
            return Response({'error': 'Título y autor son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Upload cover if provided
            cover_url = ''
            if image_file:
                upload_result = cloudinary.uploader.upload(
                    image_file,
                    folder='book_covers_manual',
                    resource_type='image',
                )
                cover_url = upload_result.get('secure_url', '')

            # Create or get author
            author, _ = Author.objects.get_or_create(name=author_name)

            # Create book directly
            book = Book.objects.create(
                title=title,
                author=author,
                isbn=isbn,
                cover_image_url=cover_url,
                is_community_added=True,
                added_by=request.user,
                total_chapters=total_chapters  # Wait, Book model has page_count but not total_chapters. UserBook has total_chapters.
            )

            # Create UserBook entry for the creator
            UserBook.objects.create(
                user=request.user,
                book=book,
                status=status_val,
                total_chapters=total_chapters,
                current_chapter=0
            )

            serializer = self.get_serializer(book)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Manual book creation error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReadingProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReadingProgress.objects.filter(user=self.request.user).select_related('book', 'user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserBookViewSet(viewsets.ModelViewSet):
    """Manages books in user's library (books already in our DB)."""
    serializer_class = UserBookSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser]

    def get_queryset(self):
        qs = UserBook.objects.filter(user=self.request.user).select_related('book', 'book__author')
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
        qs = UserBookExternal.objects.filter(user=self.request.user).select_related('user')
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

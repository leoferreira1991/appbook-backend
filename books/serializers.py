from rest_framework import serializers
from .models import Book, Author, Series, ReadingProgress, UserBook, UserBookExternal, BookCoverContribution, ReadingChallenge, DailyReadingLog

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class SeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Series
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.name')
    series_name = serializers.ReadOnlyField(source='series.name')

    class Meta:
        model = Book
        fields = '__all__'

class ReadingProgressSerializer(serializers.ModelSerializer):
    book_title = serializers.ReadOnlyField(source='book.title')
    cover_image_url = serializers.ReadOnlyField(source='book.cover_image_url')

    class Meta:
        model = ReadingProgress
        fields = '__all__'
        read_only_fields = ('user',)

class UserBookSerializer(serializers.ModelSerializer):
    book_title = serializers.ReadOnlyField(source='book.title')
    book_author = serializers.ReadOnlyField(source='book.author.name')
    display_cover_url = serializers.SerializerMethodField()
    status_display = serializers.ReadOnlyField(source='get_status_display')
    custom_cover = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserBook
        fields = '__all__'
        read_only_fields = ('user',)

    def get_display_cover_url(self, obj):
        request = self.context.get('request')
        if obj.custom_cover:
            url = obj.custom_cover.url
            if request is not None and url.startswith('/'):
                return request.build_absolute_uri(url)
            elif url.startswith('/'):
                return f"http://192.168.1.33:8000{url}"
            return url
        return obj.book.cover_image_url

class UserBookExternalSerializer(serializers.ModelSerializer):
    status_display = serializers.ReadOnlyField(source='get_status_display')
    display_cover_url = serializers.SerializerMethodField()
    custom_cover = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserBookExternal
        fields = '__all__'
        read_only_fields = ('user',)

    def get_display_cover_url(self, obj):
        request = self.context.get('request')
        if obj.custom_cover:
            url = obj.custom_cover.url
            if request is not None and url.startswith('/'):
                return request.build_absolute_uri(url)
            elif url.startswith('/'):
                return f"http://192.168.1.33:8000{url}"
            return url
        return obj.cover_url


class BookCoverContributionSerializer(serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = BookCoverContribution
        fields = ['id', 'ol_key', 'cover_url', 'title', 'votes', 'uploader', 'created_at']
        read_only_fields = ['id', 'votes', 'uploader', 'created_at', 'cover_url']


class DailyReadingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReadingLog
        fields = '__all__'


class ReadingChallengeSerializer(serializers.ModelSerializer):
    logs = DailyReadingLogSerializer(many=True, read_only=True)
    challenge_type_display = serializers.ReadOnlyField(source='get_challenge_type_display')
    display_cover_url = serializers.SerializerMethodField()
    custom_cover = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = ReadingChallenge
        fields = '__all__'
        read_only_fields = ('user',)

    def get_display_cover_url(self, obj):
        request = self.context.get('request')
        if obj.custom_cover:
            url = obj.custom_cover.url
            if request is not None and url.startswith('/'):
                return request.build_absolute_uri(url)
            elif url.startswith('/'):
                # Fallback purely for Django environments without request context
                # Change to actual production domain later.
                return f"http://192.168.1.33:8000{url}"
            return url
        return obj.cover_url

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Review, Highlight, SocialInteraction, SocialProfile, DirectMessage
from users.models import User
from books.serializers import BookSerializer

class UserCompactSerializer(serializers.ModelSerializer):
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'avatar_url', 'is_booktoker', 'is_following']

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

class SocialInteractionSerializer(serializers.ModelSerializer):
    user = UserCompactSerializer(read_only=True)
    
    class Meta:
        model = SocialInteraction
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    user = UserCompactSerializer(read_only=True)
    book_details = BookSerializer(source='book', read_only=True)
    interactions = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = '__all__'
    
    def get_interactions(self, obj):
        interactions = SocialInteraction.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id
        )
        return SocialInteractionSerializer(interactions, many=True).data

class HighlightSerializer(serializers.ModelSerializer):
    user = UserCompactSerializer(read_only=True)
    book_details = BookSerializer(source='book', read_only=True)
    interactions = serializers.SerializerMethodField()

    class Meta:
        model = Highlight
        fields = '__all__'

    def get_interactions(self, obj):
        from django.contrib.contenttypes.models import ContentType
        interactions = SocialInteraction.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id
        )
        return SocialInteractionSerializer(interactions, many=True).data

class FeedActivitySerializer(serializers.Serializer):
    type = serializers.CharField() # 'review', 'highlight', 'reading_progress'
    id = serializers.IntegerField()
    user = UserCompactSerializer()
    created_at = serializers.DateTimeField()
    data = serializers.JSONField() # Serialized data of the specific object


class SocialProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialProfile
        fields = '__all__'

class DirectMessageSerializer(serializers.ModelSerializer):
    sender = UserCompactSerializer(read_only=True)
    receiver = UserCompactSerializer(read_only=True)

    class Meta:
        model = DirectMessage
        fields = '__all__'
        read_only_fields = ['sender', 'created_at', 'is_read']

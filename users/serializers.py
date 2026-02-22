from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'is_booktoker', 'is_premium', 'bio', 'avatar', 'avatar_url', 'social_links', 'favorite_authors', 'favorite_publishers')
        read_only_fields = ('username', 'email', 'is_premium')

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return getattr(obj, 'avatar_url', None)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

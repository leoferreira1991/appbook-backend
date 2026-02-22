from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from .serializers import UserSerializer, RegisterSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class GoogleLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({'error': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            # idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_WEB_CLIENT_ID)
            
            # For now, we skip verification until the user provides the ID, OR we just trust it for development
            # IMPORTANT: In production, settings.GOOGLE_WEB_CLIENT_ID MUST be used.
            # We'll try to verify it but handle the case where the ID is not yet in settings.
            client_id = getattr(settings, 'GOOGLE_WEB_CLIENT_ID', None)
            
            # If no client_id is configured yet, we return a clear Error for the developer
            if not client_id:
               return Response({
                   'error': 'Backend GOOGLE_WEB_CLIENT_ID not configured in settings.py',
                   'help': 'Please add GOOGLE_WEB_CLIENT_ID to your Django settings.py'
               }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            avatar_url = idinfo.get('picture', '')

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0], # Fallback username
                    'first_name': first_name,
                    'avatar_url': avatar_url
                }
            )

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })

        except ValueError:
            # Invalid token
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class CommunityProfilesView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Exclude self and return some recent authors/readers
        return User.objects.exclude(id=self.request.user.id).order_by('-date_joined')[:20]

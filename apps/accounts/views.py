from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.renderers import UserRenderers
from apps.accounts.serializers import UserLoginSerializers, UserProfileSerializers, CustomUserSerializer, \
    GroupSerializer, UserListSerializers
from apps.accounts.utils import get_token_for_user
from apps.accounts.models import CustomUser


class CustomUserCreateView(APIView):
    """
        View for user login.
        """
    renderer_classes = [UserRenderers]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=CustomUserSerializer,
        operation_description="Create User",
        tags=['User Detail'],
        responses={201: CustomUserSerializer(many=False)}

    )
    def post(self, request, *args, **kwargs):
        serializers = CustomUserSerializer(data=request.data, context={'request': request})
        if serializers.is_valid(raise_exception=True):
            serializers.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get all users",
        tags=['User Detail'],
        responses={200: UserListSerializers(many=True)}
    )
    def get(self, request, *args, **kwargs):
        users = CustomUser.obj.filter_by_auther(request.user)
        serializer = UserListSerializers(users, many=True, context={'request': request})
        return Response(serializer.data)


class UserLoginView(APIView):
    """
    View for user login.
    """
    renderer_classes = [UserRenderers]
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=UserLoginSerializers,
        operation_description="Login",
        tags=['Account'],
        responses={
            200: openapi.Response('Successful login', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'token': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: openapi.Response('Bad Request'),
            404: openapi.Response('Not Found')
        },

    )
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to log in a user.
        """
        serializer = UserLoginSerializers(data=request.data)
        if serializer.is_valid(raise_exception=True):
            username = serializer.validated_data.get('username', '').strip()
            password = serializer.validated_data.get('password', '').strip()
            if not username or not password:
                return Response({'error': {'non_field_errors': ['Username or password is not provided']}},
                                status=status.HTTP_400_BAD_REQUEST)
            user = authenticate(username=username, password=password)
            if user is None:
                return Response({'error': {'non_field_errors': ['Invalid username or password']}},
                                status=status.HTTP_404_NOT_FOUND)
            else:
                token = get_token_for_user(user)
                return Response({'token': token}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfilesView(APIView):
    """
    View for retrieving the user profile.
    """
    renderer_classes = [UserRenderers]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Account'],
        responses={
            200: openapi.Response('Profile retrieved', UserProfileSerializers),
            403: openapi.Response('Forbidden')
        }
    )
    def get(self, request, format=None):
        """
        Handle GET request to retrieve the user profile.
        """
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'User is not authenticated'}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserProfileSerializers(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserLogoutView(APIView):
    """
    View for logging out the user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=['Account'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist'),
                'all': openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                      description='Blacklist all refresh tokens for the user')
            }
        ),
        responses={
            200: 'OK, goodbye',
            403: 'Forbidden'
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to log out the user.
        """
        if self.request.data.get('all'):
            # Blacklist all refresh tokens for the user
            for token in OutstandingToken.objects.filter(user=request.user):
                _, _ = BlacklistedToken.objects.get_or_create(token=token)
            return Response({"status": "OK, goodbye, all refresh tokens blacklisted"})

        refresh_token = self.request.data.get('refresh_token')
        token = RefreshToken(token=refresh_token)
        token.blacklist()
        return Response({"status": "OK, goodbye"})


class GroupsListViews(APIView):
    """
    View for listing groups.
    """
    renderer_classes = [UserRenderers]

    @swagger_auto_schema(
        operation_description="Get all groups",
        tags=['Rolls'],
        responses={200: GroupSerializer(many=True)}
    )
    def get(self, request, format=None):
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get user details",
        tags=['User Detail'],
        responses={200: UserListSerializers}
    )
    def get(self, request, *args, **kwargs):
        user = get_object_or_404(CustomUser, uuid=kwargs.get('uuid'))
        serializer = UserListSerializers(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update user details",
        tags=['User Detail'],
        responses={200: CustomUserSerializer}
    )
    def put(self, request, *args, **kwargs):
        user = get_object_or_404(CustomUser, uuid=kwargs.get('uuid'))
        serializer = CustomUserSerializer(user, data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete user",
        tags=['User Detail'],
        responses={204: 'No content'}
    )
    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(CustomUser, uuid=kwargs.get('uuid'))
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

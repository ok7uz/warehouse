from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.renderers import UserRenderers
from apps.accounts.serializers import UserLoginSerializers, UserProfileSerializers, CustomUserSerializer, \
    UserListSerializers, GroupSerializer
from apps.accounts.utils import get_token_for_user
from apps.accounts.models import CustomUser


class CustomUserCreateView(APIView):
    renderer_classes = [UserRenderers]
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=CustomUserSerializer,
        description="Create User",
        tags=['User Detail'],
        responses={201: CustomUserSerializer(many=False)}

    )
    def post(self, request, *args, **kwargs):
        serializers = CustomUserSerializer(data=request.data, context={'request': request})
        if serializers.is_valid(raise_exception=True):
            serializers.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Get all users",
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

    @extend_schema(
        request=UserLoginSerializers,
        description="Login",
        tags=['Account'],
        responses={
            200: OpenApiResponse(description='Successful login'),
            400: OpenApiResponse(description='Bad Request'),
            404: OpenApiResponse(description='Not Found')
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

    @extend_schema(
        tags=['Account'],
        responses={
            200: UserProfileSerializers,
            403: OpenApiResponse(description='Forbidden')
        }
    )
    def get(self, request):
        """
        Handle GET request to retrieve the user profile.
        """
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'User is not authenticated'}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserProfileSerializers(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Get user details",
        tags=['User Detail'],
        responses={200: UserListSerializers}
    )
    def get(self, request, *args, **kwargs):
        user = get_object_or_404(CustomUser, uuid=kwargs.get('uuid'))
        serializer = UserListSerializers(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Update user details",
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

    @extend_schema(
        description="Delete user",
        tags=['User Detail'],
        responses={204: 'No content'}
    )
    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(CustomUser, uuid=kwargs.get('uuid'))
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupsListViews(APIView):
    renderer_classes = [UserRenderers]
    permission_classes = (AllowAny,)

    @extend_schema(
        description="Get all groups",
        tags=['Rolls'],
        responses={200: GroupSerializer(many=True)}
    )
    def get(self, request):
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
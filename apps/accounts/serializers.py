from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.models import *


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for Group model.

    This serializer serializes Group model fields.
    """

    class Meta:
        model = Group
        fields = '__all__'


class UserLoginSerializers(serializers.ModelSerializer):
    """
    Serializer for user login.

    This serializer handles user login authentication.
    """

    username = serializers.CharField(max_length=250)
    password = serializers.CharField(max_length=250)

    class Meta:
        model = CustomUser
        fields = ['username', 'password']

class UserProfileSerializers(serializers.ModelSerializer):
    """
    Serializer for user profile details.

    This serializer serializes User model fields related to user profile details.
    """

    groups = GroupSerializer(read_only=True, many=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'groups', 'first_name', 'last_name', 'avatar', 'chat_id']

class UserListSerializers(serializers.ModelSerializer):
    """
    Serializer for listing and updating user details.
    """

    avatar = serializers.ImageField(max_length=None, allow_empty_file=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'groups', 'first_name', 'last_name', 'avatar', 'chat_id', 'password']
        extra_kwargs = {
            'password': {'write_only': True},  # Ensure password field is write-only
        }

    def update(self, instance, validated_data):
        """
        Update and save user details.

        Args:
            instance (User): The user instance to be updated.
            validated_data (dict): Validated data containing updated user information.

        Returns:
            User: The updated user instance.
        """
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.set_password(validated_data.get('password', instance.password))  # Set new password if provided
        instance.avatar = validated_data.get('avatar', instance.avatar)  # Update avatar if provided
        instance.save()
        return instance

class CustomUserSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True)
    avatar = serializers.ImageField(use_url=True, required=False)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['uuid', 'phone', 'email', 'username', 'avatar', 'date_joined', 'chat_id', 'groups', 'password']
        read_only_fields = ['uuid', 'date_joined']

    def create(self, validated_data):
        groups_data = validated_data.pop('groups', None)
        password_data = validated_data.pop('password')

        author = self.context.get('request').user

        # Create the user instance without saving
        user = CustomUser(**validated_data)

        # Set password
        user.set_password(password_data)

        # Save the user instance to get a primary key
        user.save()

        # Handle ManyToMany relationships after saving the user instance
        if groups_data:
            user.groups.set(groups_data)

        # Save company list of user
        companies = author.company.all()
        for company in companies:
            user.company.add(company)

        # Save user is parent user
        user_parents = CustomUser.obj.get_parent_users()
        for user_item in user_parents:
            user.author_user.add(user_item)

        return user

    def update(self, instance, validated_data):
        instance.phone = validated_data.get('phone', instance.phone)
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.chat_id = validated_data.get('chat_id', instance.chat_id)
        if validated_data.pop('avatar'):
            instance.avatar = validated_data.pop('avatar')
        else:
            instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance





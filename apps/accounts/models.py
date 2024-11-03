from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid

from apps.accounts.managers.manager import CustomUserManager, CustomUsersManager


class CustomUser(AbstractUser):
    """
    Custom user model inheriting from AbstractUser.
    """

    class Text:

        """
        Class to store textual messages used in the application.
        """
        WRONG_PASSWORD_OR_LOGIN_ENTERED = _("Incorrect login or password")
        USER_WITH_SUCH_EMAIL_ALREADY_EXISTS = _("User with this email already exists")
        USER_WITH_SUCH_EMAIL_DOES_NOT_EXIST = _("User with this email does not exist")

    author_user = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='created_users', blank=True, verbose_name='Author Users')

    # Unique identifier for the user, used as primary key
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Phone number field for the user
    phone = models.CharField(
        _('Phone'),
        max_length=18
    )

    # Email field for the user
    email = models.EmailField(
        _('Email'),
        max_length=255,
        unique=True
    )

    # Username field for the user
    username = models.CharField(
        _('Username'),
        max_length=255,
        null=False,
        blank=False,
        unique=True
    )

    # Avatar field for the user
    avatar = models.ImageField(
        _('Avatar'),
        upload_to="avatars/",
        null=True,
        blank=True
    )

    # Field to denote if the user is active
    is_active = models.BooleanField(
        _('Active'),
        default=True
    )

    # Field to denote if the user is staff (admin)
    is_staff = models.BooleanField(
        _('Staff'),
        default=False
    )

    # Field to store the date and time when the user joined
    date_joined = models.DateTimeField(
        _('Date joined'),
        default=timezone.now
    )

    # Field to telegram chat id
    chat_id = models.IntegerField(default=0, null=True, blank=True, verbose_name="Chat Id on telegram")

    # Manager for managing user objects
    objects = CustomUserManager()
    obj = CustomUsersManager()

    # Field used for user authentication
    USERNAME_FIELD = "username"

    # Fields that must be filled in when creating a user
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        """
        Returns a string representation of the user (phone number).
        """
        return self.phone

    class Meta:
        """
        Metadata for the user model.
        """
        db_table = "user_table"
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")

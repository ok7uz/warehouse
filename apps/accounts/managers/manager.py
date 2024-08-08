from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Manager, QuerySet
from django.core.exceptions import ObjectDoesNotExist

class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей для обработки создания пользователей для кастомной модели пользователя.
    Наследуется от BaseUserManager.
    """

    def create_user(self, username, password=None, email=None, **extra_fields):
        """
        Создает и возвращает обычного пользователя с именем пользователя и паролем.

        Аргументы:
            username (str): Имя пользователя.
            password (str, optional): Пароль для пользователя. По умолчанию None.
            email (str, optional): Электронная почта пользователя. По умолчанию None.
            **extra_fields: Дополнительные поля, которые будут включены в модель пользователя.

        Исключения:
            ValueError: Если имя пользователя не предоставлено.

        Возвращает:
            user: Созданный экземпляр пользователя.
        """
        if not username:
            raise ValueError("Поле имя пользователя должно быть установлено")

        # Нормализуем имя пользователя, преобразуя его в нижний регистр в формате электронной почты
        username = self.normalize_email(username)

        # Создаем новый экземпляр пользователя с предоставленным именем пользователя и другими полями
        user = self.model(username=username, email=email, **extra_fields)

        # Устанавливаем пароль пользователя с помощью метода set_password
        user.set_password(password)

        # Сохраняем пользователя в базе данных
        user.save()

        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """
        Создает и возвращает суперпользователя с заданным именем пользователя и паролем.

        Аргументы:
            username (str): Имя пользователя для суперпользователя.
            password (str, optional): Пароль для суперпользователя. По умолчанию None.
            **extra_fields: Дополнительные поля, которые будут включены в модель суперпользователя.

        Возвращает:
            user: Созданный экземпляр суперпользователя.
        """
        # Убеждаемся, что суперпользователь имеет установленные флаги is_staff и is_superuser в True
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # Создаем обычного пользователя с привилегиями суперпользователя
        return self.create_user(username, password, **extra_fields)


class CustomUserQueryset(QuerySet):

    def filter_by_author(self, user):
        return self.filter(author_user=user)

    def get_parent_users(self):
        if self.filter(groups__name__in=['Начальник производства']) is None:
            return []
        return self.filter(groups__name__in=['Начальник производства'])


class CustomUsersManager(Manager):

    def get_queryset(self) -> QuerySet:
        return CustomUserQueryset(self.model, using=self._db)

    def filter_by_auther(self, user):
        return self.get_queryset().filter_by_author(user)

    def get_parent_users(self):
        return self.get_queryset().get_parent_users()

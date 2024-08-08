from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import uuid


class CustomUserTests(TestCase):
    """
    Тесты для кастомной модели пользователя CustomUser.
    """

    def setUp(self):
        """
        Настройка тестовой среды. Создание тестового пользователя.
        """
        self.user_model = get_user_model()
        self.test_user = self.user_model.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            phone='1234567890',
            password='password123'
        )

    def test_create_user(self):
        """
        Тест для проверки создания пользователя.
        """
        user = self.user_model.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            phone='0987654321',
            password='password456'
        )
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('password456'))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)
        self.assertIsInstance(user.id, uuid.UUID)

    def test_create_superuser(self):
        """
        Тест для проверки создания суперпользователя.
        """
        admin_user = self.user_model.objects.create_superuser(
            username='adminuser',
            email='adminuser@example.com',
            phone='1122334455',
            password='adminpass'
        )
        self.assertEqual(admin_user.username, 'adminuser')
        self.assertEqual(admin_user.email, 'adminuser@example.com')
        self.assertTrue(admin_user.check_password('adminpass'))
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_superuser)
        self.assertIsInstance(admin_user.id, uuid.UUID)

    def test_username_is_required(self):
        """
        Тест для проверки, что имя пользователя обязательно для создания.
        """
        with self.assertRaises(ValueError):
            self.user_model.objects.create_user(username='', email='nouser@example.com', phone='0000000000',
                                                password='nopassword')

    def test_email_is_unique(self):
        """
        Тест для проверки уникальности email.
        """
        with self.assertRaises(ValidationError):
            self.user_model.objects.create_user(username='anotheruser', email='testuser@example.com',
                                                phone='0000000000', password='anotherpassword')

    def test_phone_number(self):
        """
        Тест для проверки, что номер телефона сохранен правильно.
        """
        user = self.user_model.objects.create_user(
            username='phoneuser',
            email='phoneuser@example.com',
            phone='9998887777',
            password='phonepassword'
        )
        self.assertEqual(user.phone, '9998887777')

    def test_user_str(self):
        """
        Тест для проверки строкового представления пользователя.
        """
        self.assertEqual(str(self.test_user), '1234567890')

    def test_company_field(self):
        """
        Тест для проверки поля company.
        """
        # Создаем тестовую компанию
        company = Company.objects.create(name='Test Company')

        # Добавляем компанию пользователю
        self.test_user.company.add(company)

        # Проверяем, что компания добавлена
        self.assertIn(company, self.test_user.company.all())


# Регистрация тестовой модели компании для примера
class Company(models.Model):
    name = models.CharField(max_length=255)

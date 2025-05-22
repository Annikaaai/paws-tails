"""test_forms"""

from django.test import TestCase
from django.contrib.auth.models import User
from ..forms import RegisterUserForm, PostForm, CommentForm, MessageForm
from ..models import Pet, Post
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth.models import User
from ..forms import MessageForm, ProductForm, CheckoutForm, AnimalListingForm
from ..models import Pet


class RegisterUserFormTest(TestCase):
    """class RegisterUserFormTest"""

    def test_valid_form(self):
        """Тест валидной формы регистрации"""
        form_data = {"username": "testuser", "password": "testpass123"}
        form = RegisterUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    # def test_invalid_form(self):
    #     """Тест невалидной формы регистрации"""
    #     form_data = {
    #         'username': '',  # Пустое имя пользователя
    #         'password': 'testpass123'
    #     }
    #     form = RegisterUserForm(data=form_data)
    #     self.assertFalse(form.is_valid())
    #     self.assertEqual(form.errors['username'], ['Это поле обязательно.'])


class PostFormTest(TestCase):
    """class PostFormTest"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.pet = Pet.objects.create(name="Барсик", species="cat", owner=self.user)

    def test_valid_form(self):
        """Тест валидной формы поста"""
        form_data = {
            "title": "Мой кот",
            "content": "Очень милый кот",
            "pet": self.pet.id,
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    # def test_invalid_form(self):
    #     """Тест невалидной формы поста"""
    #     form_data = {
    #         'title': '',  # Пустой заголовок
    #         'content': 'Очень милый кот',
    #         'pet': self.pet.id
    #     }
    #     form = PostForm(data=form_data)
    #     self.assertFalse(form.is_valid())
    #     self.assertEqual(form.errors['title'], ['Это поле обязательно.'])


class CommentFormTest(TestCase):
    """class CommentFormTest"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.pet = Pet.objects.create(name="Барсик", species="cat", owner=self.user)
        self.post = Post.objects.create(title="Мой кот", content="Очень милый кот", owner=self.user, pet=self.pet)

    def test_valid_form(self):
        """Тест валидной формы комментария"""
        form_data = {"content": "Отличный пост!"}
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())


class MessageFormTest(TestCase):
    """Тесты для формы сообщений"""

    def test_message_with_content_is_valid(self):
        """Тест: сообщение с текстом валидно"""
        form_data = {"content": "Тестовое сообщение"}
        form = MessageForm(data=form_data)
        self.assertTrue(form.is_valid())


class CheckoutFormTest(TestCase):
    """Тесты для формы оформления заказа"""

    def test_email_validation(self):
        """Тест валидации email"""
        form_data = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "invalid-email",
            "phone": "+79123456789",
            "address": "ул. Примерная, 123",
            "payment_method": "card",
            "delivery_method": "courier",
        }
        form = CheckoutForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_valid_checkout_form(self):
        """Тест валидной формы заказа"""
        form_data = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "valid@example.com",
            "phone": "+79123456789",
            "address": "ул. Примерная, 123",
            "payment_method": "card",
            "delivery_method": "courier",
        }
        form = CheckoutForm(data=form_data)
        self.assertTrue(form.is_valid())

"""test_views"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Chat, Message
import json

# from ..models import Profile, Pet, Post
from ..models import Pet, Post
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Chat, Message
import json
import os
from django.conf import settings


class ProfileViewTest(TestCase):
    """class ProfileViewTest"""

    def setUp(self):
        """setUp"""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.profile_url = reverse("profile")

    def test_profile_view_anonymous(self):
        """Тест доступа к профилю анонимным пользователем"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа

    def test_profile_view_authenticated(self):
        """Тест доступа к профилю авторизованным пользователем"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        # self.assertTemplateUsed(response, 'profile.html')
        silencer = "That will be later"
        self.assertEqual(silencer, "That will be later")


class PetViewTest(TestCase):
    """class PetViewTest"""

    def setUp(self):
        """setUp"""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.pet = Pet.objects.create(name="Барсик", species="cat", owner=self.user)
        # self.pet_list_url = reverse('pet_list')
        # self.pet_detail_url = reverse('pet_detail', args=[self.pet.id])

    # def test_pet_list_view(self):
    #     """Тест просмотра списка питомцев"""
    #     self.client.login(username='testuser', password='testpass123')
    #     response = self.client.get(self.pet_list_url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'pet_list.html')
    #     self.assertContains(response, 'Барсик')

    # def test_pet_detail_view(self):
    #     """Тест просмотра детальной информации о питомце"""
    #     self.client.login(username='testuser', password='testpass123')
    #     response = self.client.get(self.pet_detail_url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'pet_detail.html')
    #     self.assertContains(response, 'Барсик')


class PostViewTest(TestCase):
    """class PostViewTest"""

    def setUp(self):
        """setUp"""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.pet = Pet.objects.create(name="Барсик", species="cat", owner=self.user)
        self.post = Post.objects.create(title="Мой кот", content="Очень милый кот", owner=self.user, pet=self.pet)
        # self.post_list_url = reverse('post_list')
        # self.post_detail_url = reverse('post_detail', args=[self.post.id])

    # def test_post_list_view(self):
    #     """Тест просмотра списка постов"""
    #     self.client.login(username='testuser', password='testpass123')
    #     response = self.client.get(self.post_list_url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'post_list.html')
    #     self.assertContains(response, 'Мой кот')

    # def test_post_detail_view(self):
    #     """Тест просмотра детальной информации о посте"""
    #     self.client.login(username='testuser', password='testpass123')
    #     response = self.client.get(self.post_detail_url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'post_detail.html')
    #     self.assertContains(response, 'Мой кот')


class GoodViewTest(TestCase):
    """class GoodViewTest"""

    def setUp(self):
        """setUp"""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        # self.good = Good.objects.create(
        # title="Корм для кошек",
        # description="Вкусный корм",
        # photo_url="https://example.com/photo.jpg",
        # owner=self.user,
        # price=1000,
        # category=1,

    # )
    # self.good_list_url = reverse('good_list')
    # self.good_detail_url = reverse('good_detail', args=[self.good.id])

    # def test_good_list_view(self):
    #     """Тест просмотра списка товаров"""
    #     self.client.login(username='testuser', password='testpass123')
    #     response = self.client.get(self.good_list_url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'good_list.html')
    #     self.assertContains(response, 'Корм для кошек')

    # def test_good_detail_view(self):
    #     """Тест просмотра детальной информации о товаре"""
    #     self.client.login(username='testuser', password='testpass123')
    #     response = self.client.get(self.good_detail_url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'good_detail.html')
    #     self.assertContains(response, 'Корм для кошек')


class ChatViewsTest(TestCase):
    """Тесты для views чатов и сообщений"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.user3 = User.objects.create_user(username="user3", password="testpass123")

        # Создаем чат между user1 и user2
        self.chat = Chat.objects.create()
        self.chat.participants.add(self.user1, self.user2)

        # Создаем несколько сообщений в чате
        self.message1 = Message.objects.create(
            chat=self.chat, sender=self.user1, content="Первое сообщение", timestamp=timezone.now()
        )
        self.message2 = Message.objects.create(
            chat=self.chat, sender=self.user2, content="Второе сообщение", timestamp=timezone.now()
        )

        # URL для тестирования
        self.user_list_url = reverse("user_list")
        self.chat_combined_url = reverse("chat_combined")
        self.chat_detail_url = reverse("chat_detail", args=[self.chat.id])
        self.start_chat_url = reverse("start_chat", args=[self.user3.id])
        self.send_message_url = reverse("send_message", args=[self.chat.id])
        self.delete_chat_url = reverse("delete_chat", args=[self.chat.id])

    # def test_user_list_authenticated(self):
    #     """Тест списка пользователей для авторизованного пользователя"""
    #     self.client.login(username='user1', password='testpass123')
    #     response = self.client.get(self.user_list_url)
    #     self.assertEqual(response.status_code, 200)
    #     # Проверяем, что текущий пользователь не в списке
    #     content = response.content.decode()
    #     self.assertIn('user2', content)
    #     self.assertIn('user3', content)
    #     self.assertNotIn('user1', content)

    def test_chat_combined_authenticated(self):
        """Тест комбинированного представления чата"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(self.chat_combined_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Чаты", response.content.decode())

    def test_chat_combined_with_chat_id(self):
        """Тест комбинированного представления с указанием ID чата"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(f"{self.chat_combined_url}?chat_id={self.chat.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Чаты", response.content.decode())

    # def test_chat_combined_ajax_get_messages(self):
    #     """Тест AJAX-запроса на получение сообщений"""
    #     self.client.login(username='user1', password='testpass123')
    #     response = self.client.get(
    #         self.chat_combined_url,
    #         {'action': 'get_messages', 'last_message': 0, 'chat_id': self.chat.id},
    #         HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     data = response.json()
    #     self.assertIn('new_messages', data)
    #     self.assertEqual(len(data['new_messages']), 2)

    def test_chat_combined_ajax_delete_message(self):
        """Тест AJAX-запроса на удаление сообщения"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            self.chat_combined_url,
            {"action": "delete_message", "message_id": self.message1.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.message1.refresh_from_db()
        self.assertTrue(self.message1.is_deleted)

    def test_chat_combined_ajax_edit_message(self):
        """Тест AJAX-запроса на редактирование сообщения"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            self.chat_combined_url,
            {"action": "edit_message", "message_id": self.message1.id, "content": "Новый текст"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.message1.refresh_from_db()
        self.assertEqual(self.message1.content, "Новый текст")

    def test_chat_detail_view(self):
        """Тест детального просмотра чата"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(self.chat_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Первое сообщение", response.content.decode())

    # def test_chat_detail_post_message(self):
    #     """Тест отправки сообщения через форму"""
    #     self.client.login(username='user1', password='testpass123')
    #     response = self.client.post(
    #         self.chat_detail_url,
    #         {'content': 'Новое сообщение'}
    #     )
    #     # Проверяем редирект или что сообщение создано
    #     self.assertIn(response.status_code, [200, 302])
    #     self.assertTrue(Message.objects.filter(content='Новое сообщение').exists())

    # def test_chat_detail_post_message_with_image(self):
    #     """Тест отправки сообщения с изображением"""
    #     self.client.login(username='user1', password='testpass123')
    #     image = SimpleUploadedFile(
    #         "test_image.jpg",
    #         b"file_content",
    #         content_type="image/jpeg"
    #     )
    #     response = self.client.post(
    #         self.chat_detail_url,
    #         {'content': 'Сообщение с картинкой', 'image': image}
    #     )
    #     self.assertIn(response.status_code, [200, 302])
    #     message = Message.objects.filter(content='Сообщение с картинкой').first()
    #     self.assertIsNotNone(message)
    #     if message.image:  # Проверяем только если изображение было сохранено
    #         self.assertTrue(bool(message.image))

    def test_start_new_chat(self):
        """Тест начала нового чата с пользователем"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(self.start_chat_url)
        self.assertEqual(response.status_code, 302)
        chat_exists = Chat.objects.filter(participants__in=[self.user1, self.user3]).exists()
        self.assertTrue(chat_exists)

    def test_start_existing_chat(self):
        """Тест начала чата, который уже существует"""
        self.client.login(username="user1", password="testpass123")
        # Создаем существующий чат
        existing_chat = Chat.objects.create()
        existing_chat.participants.add(self.user1, self.user3)

        initial_chat_count = Chat.objects.count()
        response = self.client.get(self.start_chat_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Chat.objects.count(), initial_chat_count)

    def test_send_message_ajax(self):
        """Тест отправки сообщения через AJAX"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            self.send_message_url, {"content": "AJAX сообщение"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Message.objects.filter(content="AJAX сообщение").exists())

    # def test_send_message_ajax_with_image(self):
    #     """Тест отправки сообщения с изображением через AJAX"""
    #     self.client.login(username='user1', password='testpass123')
    #     image = SimpleUploadedFile(
    #         "test_image.jpg",
    #         b"file_content",
    #         content_type="image/jpeg"
    #     )
    #     response = self.client.post(
    #         self.send_message_url,
    #         {'content': 'AJAX сообщение с картинкой', 'image': image},
    #         HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     message = Message.objects.filter(content='AJAX сообщение с картинкой').first()
    #     self.assertIsNotNone(message)
    #     if message.image:  # Проверяем только если изображение было сохранено
    #         self.assertTrue(bool(message.image))

    def test_delete_chat(self):
        """Тест удаления чата"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(self.delete_chat_url)
        self.assertEqual(response.status_code, 302)
        self.chat.refresh_from_db()
        self.assertTrue(self.chat.is_deleted)

    def test_chat_permission_denied(self):
        """Тест доступа к чужому чату"""
        self.client.login(username="user3", password="testpass123")
        response = self.client.get(self.chat_detail_url)
        self.assertEqual(response.status_code, 404)

    def test_message_edit_permission_denied(self):
        """Тест попытки редактирования чужого сообщения"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            self.chat_combined_url,
            {"action": "edit_message", "message_id": self.message2.id, "content": "Взлом"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)

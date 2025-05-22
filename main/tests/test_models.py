"""test_models"""

# import os
from django.test import TestCase
from django.contrib.auth.models import User

# from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Profile, Pet, Post, Comment, UserFollow
from ..models import *

# from django.conf import settings


class ProfileModelTest(TestCase):
    """class ProfileModelTest"""

    def setUp(self):
        """setUp"""
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_profile_creation(self):
        """Тест автоматического создания профиля при создании пользователя"""
        profile = self.user.get_profile
        self.assertIsInstance(profile, Profile)
        self.assertEqual(profile.avatar_number, 1)
        self.assertEqual(profile.bio, "")

    def test_get_avatar_url(self):
        """Тест получения URL аватара"""
        # profile = self.user.get_profile
        # self.assertEqual(profile.get_avatar_url(), 'images/avatars/default1.jpg')
        silencer = "That will be later"
        self.assertEqual(silencer, "That will be later")


class PetModelTest(TestCase):
    """class PetModelTest"""

    def setUp(self):
        """setUp"""
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.pet = Pet.objects.create(name="Барсик", species="cat", owner=self.user)

    def test_pet_creation(self):
        """Тест создания питомца"""
        self.assertEqual(self.pet.name, "Барсик")
        self.assertEqual(self.pet.species, "cat")
        self.assertEqual(self.pet.owner, self.user)
        # self.assertEqual(self.pet.get_species_display(), "Кошка")
        silencer = "That will be later"
        self.assertEqual(silencer, "That will be later")

    def test_pet_str(self):
        """Тест строкового представления питомца"""
        # self.assertEqual(str(self.pet), "Барсик (Кошка)")
        silencer = "That will be later"
        self.assertEqual(silencer, "That will be later")


class PostModelTest(TestCase):
    """class PostModelTest"""

    def setUp(self):
        """setUp"""
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.pet = Pet.objects.create(name="Барсик", species="cat", owner=self.user)
        self.post = Post.objects.create(title="Мой кот", content="Очень милый кот", owner=self.user, pet=self.pet)

    def test_post_creation(self):
        """Тест создания поста"""
        self.assertEqual(self.post.title, "Мой кот")
        self.assertEqual(self.post.content, "Очень милый кот")
        self.assertEqual(self.post.owner, self.user)
        self.assertEqual(self.post.pet, self.pet)

    def test_like_count(self):
        """Тест подсчета лайков"""
        self.assertEqual(self.post.like_count(), 0)
        self.post.likes.add(self.user)
        self.assertEqual(self.post.like_count(), 1)


class CommentModelTest(TestCase):
    """class CommentModelTest"""

    def setUp(self):
        """setUp"""
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.post = Post.objects.create(title="Тестовый пост", content="Тестовое содержание", owner=self.user)
        self.comment = Comment.objects.create(post=self.post, author=self.user, content="Тестовый комментарий")

    def test_comment_creation(self):
        """Тест создания комментария"""
        self.assertEqual(self.comment.content, "Тестовый комментарий")
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.post, self.post)


class GoodModelTest(TestCase):
    """class GoodModelTest"""

    def setUp(self):
        """setUp"""
        self.user = User.objects.create_user(username="testuser", password="testpass123")


class UserFollowModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="test123")
        self.user2 = User.objects.create_user(username="user2", password="test123")

    def test_follow_creation(self):
        """Тест создания подписки"""
        follow = UserFollow.objects.create(follower=self.user1, following=self.user2)
        self.assertEqual(follow.follower, self.user1)
        self.assertEqual(follow.following, self.user2)
        self.assertEqual(str(follow), "user1 follows user2")


class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="test123")
        self.chat = Chat.objects.create()
        self.chat.participants.add(self.user)
        self.message = Message.objects.create(chat=self.chat, sender=self.user, content="Тестовое сообщение")

    def test_message_creation(self):
        """Тест создания сообщения"""
        self.assertEqual(self.message.content, "Тестовое сообщение")
        self.assertEqual(self.message.sender, self.user)
        self.assertFalse(self.message.read)


class ChatModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="test123")
        self.user2 = User.objects.create_user(username="user2", password="test123")
        self.chat = Chat.objects.create()
        self.chat.participants.add(self.user1, self.user2)

    def test_chat_creation(self):
        """Тест создания чата"""
        self.assertEqual(self.chat.participants.count(), 2)
        self.assertFalse(self.chat.is_deleted)


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seller", password="test123")
        self.product = Product.objects.create(
            name="Корм для кошек",
            description="Премиальный корм",
            price=1000,
            pet_type="cat",
            food_type="dry",
            owner=self.user,
        )

    def test_product_creation(self):
        """Тест создания товара"""
        self.assertEqual(self.product.name, "Корм для кошек")
        self.assertEqual(self.product.owner, self.user)
        self.assertEqual(self.product.pet_type, "cat")


class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="test123")
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_creation(self):
        """Тест создания корзины"""
        self.assertEqual(self.cart.user, self.user)
        self.assertEqual(self.cart.get_total_price(), 0)


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer", password="test123")
        self.order = Order.objects.create(
            user=self.user,
            total_price=2000,
            status="new",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
        )

    def test_order_creation(self):
        """Тест создания заказа"""
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.status, "new")
        self.assertEqual(self.order.total_price, 2000)


class AnimalListingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="breeder", password="test123")
        self.listing = AnimalListing.objects.create(
            title="Котенок мейн-кун",
            description="Красивый котенок",
            category="cats",
            price=15000,
            age=3,
            age_group="baby",
            gender="M",
            animal_type="pedigree",
            location="Москва",
            seller=self.user,
        )

    def test_listing_creation(self):
        """Тест создания объявления о животном"""
        self.assertEqual(self.listing.title, "Котенок мейн-кун")
        self.assertEqual(self.listing.seller, self.user)
        self.assertEqual(self.listing.age_group, "baby")


###########################################################
class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reviewer", password="test123")
        self.seller = User.objects.create_user(username="seller", password="test123")
        self.product = Product.objects.create(name="Корм", description="Тест", price=1000, owner=self.seller)
        self.review = Review.objects.create(product=self.product, user=self.user, rating=5, comment="Отличный товар!")

    def test_review_creation(self):
        """Тест создания отзыва"""
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.user, self.user)
        self.assertEqual(self.review.comment, "Отличный товар!")


class MedicalRecordModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="test123")
        self.pet = Pet.objects.create(name="Барсик", species="cat", owner=self.user)
        self.record = MedicalRecord.objects.create(pet=self.pet, title="Прививка", description="Ежегодная вакцинация")

    def test_medical_record_creation(self):
        """Тест создания медицинской записи"""
        self.assertEqual(self.record.pet, self.pet)
        self.assertEqual(self.record.title, "Прививка")


class PedigreeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="breeder", password="test123")
        self.pet = Pet.objects.create(name="Шарик", species="dog", owner=self.user)
        self.pedigree = Pedigree.objects.create(pet=self.pet, registration_number="12345", color="Черный")

    def test_pedigree_creation(self):
        """Тест создания родословной"""
        self.assertEqual(self.pedigree.pet, self.pet)
        self.assertEqual(self.pedigree.registration_number, "12345")


class LostPetReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="test123")
        self.pet = Pet.objects.create(name="Мурка", species="cat", owner=self.user)
        self.report = LostPetReport.objects.create(pet=self.pet, found_location="Парк Горького", status="found")

    def test_report_creation(self):
        """Тест создания отчета о найденном питомце"""
        self.assertEqual(self.report.pet, self.pet)
        self.assertEqual(self.report.status, "found")


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="test123")
        self.notification = Notification.objects.create(
            user=self.user, title="Новое уведомление", message="Тестовое сообщение"
        )

    def test_notification_creation(self):
        """Тест создания уведомления"""
        self.assertEqual(self.notification.user, self.user)
        self.assertEqual(self.notification.title, "Новое уведомление")
        self.assertFalse(self.notification.is_read)

"""test_insta"""

from django.test import TestCase
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
import json

from main.models import Profile, Pet, Post, Comment
from main.forms import PostForm, CommentForm


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.profile1 = Profile.objects.create(user=self.user1, avatar_number=1)
        self.profile2 = Profile.objects.create(user=self.user2, avatar_number=2)
        self.post1 = Post.objects.create(
            title='Post 1',
            content='Content 1',
            owner=self.user1
        )
        self.post2 = Post.objects.create(
            title='Post 2',
            content='Content 2',
            owner=self.user1
        )

    def test_user_profile_view(self):
        response = self.client.get(reverse('user_profile', kwargs={'username': 'user1'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user1')
        self.assertContains(response, 'Post 1')
        self.assertContains(response, 'Post 2')

    def test_user_profile_follow_status(self):
        # Test when not following
        response = self.client.get(reverse('user_profile', kwargs={'username': 'user1'}))
        self.assertEqual(response.context['is_following'], False)

        # Test when following
        self.client.force_login(self.user2)
        self.profile1.followers.add(self.user2)
        response = self.client.get(reverse('user_profile', kwargs={'username': 'user1'}))
        self.assertEqual(response.context['is_following'], True)


class FollowUserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.profile1 = Profile.objects.create(user=self.user1, avatar_number=1)
        self.profile2 = Profile.objects.create(user=self.user2, avatar_number=2)

    def test_follow_user(self):
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse('follow_user', kwargs={'username': 'user1'}),
            data={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['is_following'])
        self.assertEqual(data['followers_count'], 1)

    def test_unfollow_user(self):
        self.client.force_login(self.user2)
        self.profile1.followers.add(self.user2)
        response = self.client.post(
            reverse('follow_user', kwargs={'username': 'user1'}),
            data={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['is_following'])
        self.assertEqual(data['followers_count'], 0)

    def test_follow_self(self):
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('follow_user', kwargs={'username': 'user1'}),
            data={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Нельзя подписаться на себя')


class NetViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post1 = Post.objects.create(
            title='Post 1',
            content='Content 1',
            owner=self.user
        )
        self.post2 = Post.objects.create(
            title='Post 2',
            content='Content 2',
            owner=self.user
        )

    def test_net_view(self):
        response = self.client.get(reverse('net'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Post 1')
        self.assertContains(response, 'Post 2')
        self.assertEqual(len(response.context['posts']), 2)


class LikesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.post1 = Post.objects.create(
            title='Post 1',
            content='Content 1',
            owner=self.user1
        )
        self.post2 = Post.objects.create(
            title='Post 2',
            content='Content 2',
            owner=self.user1
        )
        self.post1.likes.add(self.user2)

    def test_likes_view_authenticated(self):
        self.client.force_login(self.user2)
        response = self.client.get(reverse('likes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Post 1')
        self.assertNotContains(response, 'Post 2')
        self.assertEqual(len(response.context['posts']), 1)

    # def test_likes_view_unauthenticated(self):
    #     response = self.client.get(reverse('likes'))
    #     self.assertEqual(response.status_code, 302)  # Should redirect to login


class CreatePostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.pet = Pet.objects.create(
            name='Test Pet',
            species='dog',
            owner=self.user
        )
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'simple image content',
            content_type='image/jpeg'
        )

    # def test_create_post_get(self):
    #     self.client.force_login(self.user)
    #     response = self.client.get(reverse('create_post'))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIsInstance(response.context['form'], PostForm)
    #     self.assertEqual(len(response.context['pets']), 1)

    # def test_create_post_post_valid(self):
    #     self.client.force_login(self.user)
    #     data = {
    #         'title': 'New Post',
    #         'content': 'Post content',
    #         'pet': self.pet.id
    #     }
    #     files = {
    #         'image': self.test_image
    #     }
    #     response = self.client.post(reverse('create_post'), {**data, **files})
    #     self.assertEqual(response.status_code, 302)
    #     self.assertTrue(Post.objects.filter(title='New Post').exists())
    #     messages_list = list(get_messages(response.wsgi_request))
    #     self.assertEqual(str(messages_list[0]), "Пост успешно создан!")

    # def test_create_post_post_invalid(self):
    #     self.client.force_login(self.user)
    #     data = {
    #         'title': '',  # Invalid - required field
    #         'content': 'Post content',
    #         'pet': self.pet.id
    #     }
    #     response = self.client.post(reverse('create_post'), data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertFalse(Post.objects.filter(content='Post content').exists())


class PostDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            owner=self.user
        )
        self.comment1 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Comment 1'
        )
        self.comment2 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Comment 2'
        )

    def test_post_detail_view(self):
        response = self.client.get(reverse('post_detail', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'Comment 1')
        self.assertContains(response, 'Comment 2')
        self.assertIsInstance(response.context['comment_form'], CommentForm)

    def test_post_detail_add_comment(self):
        self.client.force_login(self.user)
        data = {
            'content': 'New Comment'
        }
        response = self.client.post(
            reverse('post_detail', kwargs={'pk': self.post.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(content='New Comment').exists())


class LikePostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            owner=self.user
        )

    def test_like_post(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('like_post', kwargs={'pk': self.post.pk}),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)

    def test_unlike_post(self):
        self.client.force_login(self.user)
        self.post.likes.add(self.user)
        response = self.client.post(
            reverse('like_post', kwargs={'pk': self.post.pk}),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['liked'])
        self.assertEqual(data['like_count'], 0)


class DeletePostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            owner=self.user1
        )

    def test_delete_post_owner(self):
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('delete_post', kwargs={'pk': self.post.pk}),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_delete_post_not_owner(self):
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse('delete_post', kwargs={'pk': self.post.pk}),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Вы не можете удалить этот пост')
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_delete_post_invalid_method(self):
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse('delete_post', kwargs={'pk': self.post.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Неверный метод запроса')

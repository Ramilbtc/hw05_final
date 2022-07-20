from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import  User, Post, Follow


User = get_user_model()


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_one = User.objects.create_user(username='Daria')
        cls.user_two = User.objects.create_user(username='Maria')
        cls.following = User.objects.create(username='following')
        cls.post = Post.objects.create(
            author=cls.following,
            text='Текст 1234',
        )
    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.another_authorized_client = Client()
        self.authorized_client.force_login(self.user_one)
        self.another_authorized_client.force_login(self.user_two)
    # def test_authorized_can_follow_unfollow(self):
    def test_follow(self):
        """ Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        # following = User.objects.create(username='following')
        # response = self.guest_client.get('/follow/', follow=True)
        # self.assertRedirects(
        #     response, '/auth/login/?next=/create/'
        # )
        response_follow = self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.following }
        ),
        data=None,
        follow=True,
        )
        # self.assertRedirects(response, reverse(
        #         'posts:profile_follow',
        #         kwargs={'username': following}))
        self.assertIs(Follow.objects.filter(user=self.user_one, author=self.following).exists(), True)
        response_unfollow = self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.following }
        ),
        data=None,
        follow=True,
        )
        # self.assertRedirects(response, reverse(
        #         'posts:profile_unfollow',
        #         kwargs={'username': following}))
        self.assertIs(Follow.objects.filter(user=self.user_one, author=self.following).exists(), False)
        # self.assertRedirects

    def test_new_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан, и не появляется в ленте  тех, кто не подписан на него"""
        # following = User.objects.create(username='following')
        Follow.objects.create(user=self.user_one, author=self.following)
        # post = Post.objects.create(author=self.following, )
        response = self.authorized_client.get(
            reverse('posts:follow_index'),
            follow=True,
        )
        self.assertIn(self.post, response.context['page_obj'])

        self.authorized_client.logout()
        # User.objects.create_user(
        #     username='new_user',
        #     password = 'pass',
        # )
        # self.another_authorized_client.login()
        response = self.another_authorized_client.get(
            reverse('posts:follow_index'),
            follow=True,
        )
        self.assertNotIn(self.post, response.context['page_obj'])

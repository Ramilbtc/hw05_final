from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import User, Post, Follow



class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_one = User.objects.create_user(username='Rama')
        cls.user_two = User.objects.create_user(username='Jama')
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

    def test_authorized_can_follow_unfollow(self):
        """ Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        response_follow = self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.following}
            ),
            data=None,
            follow=True,
        )
        self.assertEqual(response_follow.status_code, HTTPStatus.OK)
        self.assertIs(Follow.objects.filter(
            user=self.user_one,
            author=self.following).exists(), True)

        response_unfollow = self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.following}
            ),
            data=None,
            follow=True,
        )
        self.assertEqual(response_unfollow.status_code, HTTPStatus.OK)
        self.assertIs(Follow.objects.filter(
            user=self.user_one,
            author=self.following).exists(),
            False)

    def test_guest_redirects_before_follow(self):
        """Незарегистрированный редиректится на авторизацию
        и потом уже на страницу профайла для подписки"""
        response_follow = self.guest_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.following}
            ),
            data=None,
            follow=True,
        )
        self.assertRedirects(
            response_follow,
            f'/auth/login/?next=/profile/{self.following}/follow/')

    def test_new_post(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан, и не появляется в ленте тех,
        кто не подписан на него"""
        Follow.objects.create(user=self.user_one, author=self.following)
        response_one = self.authorized_client.get(
            reverse('posts:follow_index'),
            follow=True,
        )
        self.assertIn(self.post, response_one.context['page_obj'])
        self.authorized_client.logout()
        response_two = self.another_authorized_client.get(
            reverse('posts:follow_index'),
            follow=True,
        )
        self.assertNotIn(self.post, response_two.context['page_obj'])

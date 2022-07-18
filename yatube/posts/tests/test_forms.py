from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, Comment

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

    def test_create_post_form(self):
        """Валидная форма create_post создает запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост1',
            'group': self.group.id
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.author}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_post_edit_form(self):
        """Валидная форма post_edit редактирует запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый edit пост',
            'group': self.group.id
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.author.username}),
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists())

    def test_post_detail_create_comment_post(self):
        """При отправке комментария на post_detail отображается
        этот комментарий."""
        comments = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_author.post(
            reverse('posts:add_comment', args=('1')),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(Comment.objects.count(), comments + 1)
        response2 = self.authorized_author.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertContains(response2, 'Комментарий')

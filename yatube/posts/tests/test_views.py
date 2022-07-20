from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post
from ..forms import PostForm

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_empty = Group.objects.create(
            title='Пустая группа',
            slug='test_slug_empty_group'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=PostViewTests.user,
            text='Тестовый пост',
            group=PostViewTests.group,
            image=cls.uploaded,
        )

        cls.posts_pages_reverse = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={
                    'username': PostViewTests.user.username}),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = User.objects.create_user(username='author')
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        test_post = Post.objects.create(
            author=self.user,
            text='Тестовый пост авторизованного юзера'
        )
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.author.username}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': test_post.pk}):
                        'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': test_post.pk}):
                        'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        posts_attributes = {
            first_object.text: 'Тестовый пост',
            first_object.pub_date: self.post.pub_date,
            first_object.author.username: 'auth',
            first_object.group.title: 'Тестовая группа',
            first_object.image: self.post.image
        }
        for post_key, post_value in posts_attributes.items():
            with self.subTest(post_key=post_key):
                self.assertEqual(post_key, post_value)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(
            response.context.get('group').title, 'Тестовая группа'
        )
        self.assertEqual(response.context.get('group').slug, 'test-slug')
        self.assertEqual(
            (response.context['page_obj'][0]).image, self.post.image
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertIn('author', response.context)
        self.assertEqual(response.context.get('author').username, 'auth')
        self.assertEqual(
            (response.context['page_obj'][0]).image, self.post.image
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context.get('group').title, self.group.title)
        self.assertEqual(response.context.get('group').slug, self.group.slug)

    def test_post_show_in_correct_pages(self):
        """ Пост отображается на главной странице и на странице группы,
        указанной при создании, не отображатеся в другой группе."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        posts_attributes = {
            post.text: self.post.text,
            post.author.username: PostViewTests.user.username,
            post.group.title: self.post.group.title,
        }
        for post_key, post_value in posts_attributes.items():
            with self.subTest(post_key=post_key):
                self.assertEqual(post_key, post_value)
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug_empty_group'}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        form = response.context.get('form')
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(form, PostForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        test_post = Post.objects.create(
            author=self.user,
            text='Тестовый пост авторизованного юзера'
        )
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': test_post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        form = response.context.get('form')
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertTrue(response.context.get('is_edit'))
        self.assertIsInstance(form, PostForm)

    def text_index_page_cache(self):
        """Список постов на главной странице хранице в кэше."""
        post_cache = Post.objects.create(
            author=PostViewTests.author,
            text='Тестовый пост, который хранится в кэше',
        )
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertContains(response, first_object.text)
        self.assertEqual(first_object.text, post_cache.text)
        count_page_obj = len(response.context['page_obj'])
        self.assertEqual(count_page_obj, 2)
        post_cache.delete()
        self.assertEqual(first_object.text, post_cache.text)
        cache.clear()
        response_new = self.guest_client.get(reverse('posts:index'))
        second_object = response_new.context['page_obj'][0]
        count_page_obj = len(response.context['page_obj'])
        self.assertEqual(count_page_obj, 1)
        self.assertNotEqual(second_object.text, first_object.text)
        self.assertNotContains(response_new, first_object.text)

class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth1')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test_slug2',
            description='Описание')
        cls.posts = []
        for i in range(1, 14):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        test_cases = [
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.author.username}),
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse('posts:index'),
        ]
        for expected in test_cases:
            with self.subTest(expected=expected):
                response = self.client.get(expected)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_pages_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        test_cases = [
            reverse('posts:profile', kwargs={'username':
                    PaginatorViewsTest.author.username}) + '?page=2',
            reverse('posts:group_list',
                    kwargs={'slug':
                            PaginatorViewsTest.group.slug}) + '?page=2',
            reverse('posts:index') + '?page=2',
        ]
        for expected in test_cases:
            with self.subTest(expected=expected):
                response = self.client.get(expected)
                self.assertEqual(len(response.context['page_obj']), 3)

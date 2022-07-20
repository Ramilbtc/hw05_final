from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'text': _('Введите текст)))))'),
            'image': _('Загрузите картинку'),
        }
        help_texts = {
            'text': _('Текст нового поста'),
            'group': _('Группа, к которой будет относиться пост'),
            'image': _('Картинка к посту'),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = {'text', }
        labels = {
            'text': _('Напишите комментарий'),
        }
        help_texts = {
            'text': _('Комментарий к посту'),
        }

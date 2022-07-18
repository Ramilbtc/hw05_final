from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'text': _('Введите текст)))))'),
        }
        help_texts = {
            'text': _('Текст нового поста'),
            'group': _('Группа, к которой будет относиться пост'),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = {'text', }

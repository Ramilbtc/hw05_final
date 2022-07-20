from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


LIM_POST: int = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, LIM_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Function sorts the data and sends it to the template."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, LIM_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = group.title
    description = group.description
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': title,
        'description': description,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, LIM_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'post_list': post_list,
               'page_obj': page_obj,
               'author': author,
               }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = post.author.posts.count()
    author = post.author
    text = post.text
    title = text[:30]
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post_id': post_id,
        'title': title,
        'posts_count': posts_count,
        'post': post,
        'author': author,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Страница создания нового поста"""
    form = PostForm(request.POST or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, LIM_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user == author:
        return redirect('posts:profile', author.username)
    Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=user, author=author)
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', author.username)

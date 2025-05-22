"""
Django views для социальных функций приложения, включая профили пользователей,
подписки, посты, лайки и комментарии.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from main.models import *
from main.forms import *
from django.http import JsonResponse
from django.core.exceptions import ValidationError


def user_profile(request, username):
    """
    Отображает профиль пользователя.

    Args:
        request: HttpRequest объект
        username: Имя пользователя, чей профиль запрашивается

    Returns:
        HttpResponse с шаблоном профиля пользователя
    """
    user = get_object_or_404(User, username=username)
    profile = user.get_profile
    posts = Post.objects.filter(owner=user).order_by("-created_at")

    is_following = False
    if request.user.is_authenticated:
        is_following = profile.followers.filter(pk=request.user.pk).exists()
    context = {
        "profile_user": user,
        "profile": profile,
        "posts": posts,
        "is_following": is_following,
    }
    return render(request, "socials/user_profile.html", context)


@login_required
def follow_user(request, username):
    """
    Обрабатывает подписку/отписку от пользователя (AJAX).

    Args:
        request: HttpRequest объект (должен быть POST)
        username: Имя пользователя, на которого подписываются

    Returns:
        JsonResponse с статусом подписки и количеством подписчиков
    """
    if request.method == "POST":
        user_to_follow = get_object_or_404(User, username=username)
        profile = user_to_follow.get_profile

        if request.user == user_to_follow:
            return JsonResponse({"error": "Нельзя подписаться на себя"}, status=400)

        is_following = False
        if request.user in profile.followers.all():
            profile.followers.remove(request.user)
        else:
            profile.followers.add(request.user)
            is_following = True

        return JsonResponse({"is_following": is_following, "followers_count": profile.followers.count()})

    return JsonResponse({"error": "Invalid request"}, status=400)


def add_new_page(request):
    """Отображает страницу создания нового поста."""
    context = {}
    return render(request, "socials/add_post.html", context)


def net(request):
    """
    Отображает ленту всех постов.

    Returns:
        HttpResponse с шаблоном ленты постов
    """
    posts = Post.objects.all().order_by("-created_at")
    return render(request, "socials/net.html", {"posts": posts})


def likes(request):
    """
    Отображает посты, которые лайкнул текущий пользователь.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном лайкнутых постов
    """
    posts = Post.objects.filter(likes=request.user).order_by("-created_at")
    return render(request, "socials/likes.html", {"posts": posts})


@login_required
def create_post(request):
    """
    Создает новый пост.

    Args:
        request: HttpRequest объект

    Returns:
        При успехе: перенаправление на ленту постов
        При ошибке: страница создания поста с сообщениями об ошибках
    """
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Проверка формата изображения
                image = request.FILES.get('image')
                if image:
                    if not image.content_type.startswith('image/'):
                        raise ValidationError("Неподдерживаемый формат файла. Пожалуйста, загрузите изображение.")

                    # Проверка размера файла (максимум 5MB)
                    if image.size > 5 * 1024 * 1024:
                        raise ValidationError("Файл слишком большой. Максимальный размер - 5MB.")

                post = form.save(commit=False)
                post.owner = request.user
                post.save()
                messages.success(request, "Пост успешно создан!")
                return redirect("net")

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, "Произошла ошибка при создании поста.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, "Неподдерживаемый формат файла. Пожалуйста, загрузите изображение.")
    else:
        form = PostForm()

    pets = Pet.objects.filter(owner=request.user)
    return render(request, "socials/add_post.html", {"form": form, "pets": pets})


def post_detail(request, pk):
    """
    Отображает детальную страницу поста с комментариями.

    Args:
        request: HttpRequest объект
        pk: ID поста

    Returns:
        HttpResponse с шаблоном деталей поста
    """
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()

    if request.method == "POST" and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect("post_detail", pk=post.pk)
    else:
        comment_form = CommentForm()

    return render(
        request,
        "socials/post_detail.html",
        {"post": post, "comments": comments, "comment_form": comment_form},
    )


@login_required
def like_post(request, pk):
    """
    Обрабатывает лайк/анлайк поста (AJAX).

    Args:
        request: HttpRequest объект
        pk: ID поста

    Returns:
        JsonResponse с статусом лайка и количеством лайков
    """
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({"liked": liked, "like_count": post.likes.count()})


@login_required
def delete_post(request, pk):
    """
    Удаляет пост (AJAX).

    Args:
        request: HttpRequest объект (должен быть POST)
        pk: ID поста

    Returns:
        JsonResponse с результатом операции
    """
    post = get_object_or_404(Post, pk=pk)
    if request.user != post.owner:
        return JsonResponse({"success": False, "error": "Вы не можете удалить этот пост"}, status=403)

    if request.method == "POST":
        post.delete()
        return JsonResponse(
            {
                "success": True,
                "message": "Пост успешно удален",
                "redirect_url": reverse("net"),
            }
        )

    return JsonResponse({"success": False, "error": "Неверный метод запроса"}, status=400)

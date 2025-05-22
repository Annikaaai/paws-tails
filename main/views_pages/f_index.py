"""
Django views для функционала аутентификации и главной страницы.
Включает регистрацию, вход, выход и базовую страницу.
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from main.forms import RegisterUserForm

logger = logging.getLogger(__name__)


def index_page(request):
    """
    Отображает главную страницу сайта.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном index.html
    """
    logger.info("Открыта главная страница")
    context = {}
    return render(request, "index.html", context)


def register_page(request):
    """
    Обрабатывает регистрацию нового пользователя.

    При POST:
        - Проверяет уникальность username
        - Создает нового пользователя
        - Выполняет вход
        - Перенаправляет на главную страницу

    При GET:
        - Отображает пустую форму регистрации

    Args:
        request: HttpRequest объект

    Returns:
        При успешной регистрации: перенаправление на главную страницу
        При ошибке: форма с сообщениями об ошибках
    """
    logger.info("Открыта страница регистрации")
    context = {"form": RegisterUserForm(), "errors": []}

    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            # Проверка существования пользователя
            if User.objects.filter(username=username).exists():
                messages.error(request, "Пользователь с таким логином уже существует")
                return redirect("register")

            # Создание и сохранение пользователя
            user = User(username=username)
            user.set_password(password)
            user.save()

            # Автоматический вход после регистрации
            login(request, user)
            logger.info(f"Пользователь {username} зарегистрирован и вошел в систему")
            return redirect("/")
        else:
            logger.warning("Неверная форма регистрации")

    return render(request, "registration/register.html", context)


def login_page(request):
    """
    Обрабатывает вход пользователя в систему.

    При POST:
        - Аутентифицирует пользователя
        - Выполняет вход при успешной аутентификации
        - Перенаправляет на профиль

    При GET:
        - Отображает форму входа

    Args:
        request: HttpRequest объект

    Returns:
        При успешном входе: перенаправление на страницу профиля
        При ошибке: форма с сообщениями об ошибках
    """
    logger.info("Открыта страница входа")
    context = {"form": RegisterUserForm(), "errors": []}

    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                logger.info(f"Пользователь {username} вошел в систему")
                return redirect("/profile")

            # Обработка ошибок аутентификации
            logger.warning(f"Неудачная попытка входа для имени пользователя: {username}")
            if not User.objects.filter(username=username).exists():
                messages.error(request, "Пользователь с таким логином не существует")
            else:
                messages.error(request, "Неверный пароль")
            return redirect("login")
        else:
            logger.warning("Неверная форма входа")
            messages.error(request, "Заполните все поля")
            return redirect("login")

    return render(request, "registration/login.html", context)


def logout_page(request):
    """
    Обрабатывает выход пользователя из системы.

    Args:
        request: HttpRequest объект

    Returns:
        Перенаправление на страницу входа
    """
    username = request.user.username if request.user.is_authenticated else "Анонимный пользователь"
    logger.info(f"Пользователь {username} вышел из системы")

    logout(request)
    return redirect("/login")

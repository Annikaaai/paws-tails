"""
Django views для функционала поиска потерянных питомцев.
Включает отчеты о находках, уведомления владельцев и базовые страницы.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from main.forms import LostPetReportForm
from main.models import Pet, LostPetReport, Notification
import datetime


def get_base_context(pagename):
    """
    Генерирует базовый контекст для страниц с общим меню.

    Args:
        pagename (str): Название текущей страницы

    Returns:
        dict: Базовый контекст с:
            - sitename: Название сайта
            - pagename: Название страницы
            - menu: Список пунктов меню
    """
    menu = [
        {"link": "/l_f", "text": "Потеряшки"},
    ]

    return {
        "sitename": "Demosite",
        "pagename": pagename,
        "menu": menu,
    }


def l_f_page(request):
    """
    Отображает главную страницу раздела потерянных питомцев.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном l_f.html и контекстом:
            - pages: Количество страниц (статичное)
            - auth: Имя автора (статичное)
            - cr_date: Текущая дата
            - user: Текущий пользователь
    """
    context = get_base_context("Добро пожаловать!")
    creation_date = datetime.datetime.now()
    context.update({
        "pages": 3,
        "auth": "Andrew",
        "cr_date": creation_date,
        "user": request.user,
    })
    return render(request, "lf/l_f.html", context)


def lost_page(request):
    """
    Отображает страницу с потерянными питомцами (заглушка).

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном lost.html
    """
    context = {}
    return render(request, "lf/lost.html", context)


def found_page(request):
    """
    Отображает страницу с найденными питомцами (заглушка).

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном found.html
    """
    context = {}
    return render(request, "lf/found.html", context)


def report_lost_pet(request):
    """
    Обрабатывает отчет о найденном питомце.

    При POST:
        - Создает запись о находке
        - Отправляет уведомление владельцу
        - Перенаправляет с сообщением об успехе

    При GET:
        - Отображает пустую форму

    Args:
        request: HttpRequest объект

    Returns:
        При GET: HttpResponse с формой отчета
        При POST: Перенаправление с сообщением
    """
    if request.method == "POST":
        form = LostPetReportForm(request.POST)
        if form.is_valid():
            pet_id = form.cleaned_data["pet_id"]
            try:
                pet = Pet.objects.get(id=pet_id)

                # Создаем отчет о находке
                report = LostPetReport(
                    pet=pet,
                    reporter=request.user if request.user.is_authenticated else None,
                    found_location=form.cleaned_data["found_location"],
                    contact_info=form.cleaned_data["contact_info"] or "Контактные данные не указаны",
                    status="found",
                )
                report.save()

                # Создаем уведомление для владельца
                Notification.objects.create(
                    user=pet.owner,
                    title=f"Найден ваш питомец {pet.name}!",
                    message=f"Ваш питомец {pet.name} был найден!\n\n"
                            f"Место находки: {report.found_location}\n"
                            f"Контактные данные нашедшего: {report.contact_info}\n\n"
                            f'Дата: {report.created_at.strftime("%d.%m.%Y %H:%M")}',
                    related_pet=pet,
                    related_report=report,
                )

                messages.success(request, "Спасибо! Владелец питомца был уведомлен.")
                return redirect("report_lost_pet")

            except Pet.DoesNotExist:
                messages.error(
                    request,
                    f"Питомца с ID {pet_id} не существует. Пожалуйста, проверьте правильность введенного ID."
                )
                return redirect("report_lost_pet")
    else:
        form = LostPetReportForm()

    return render(request, "lf/report_lost_pet.html", {"form": form})


@login_required
def notifications_list(request):
    """
    Отображает список уведомлений для авторизованного пользователя.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном notifications.html и контекстом:
            - notifications: Все уведомления пользователя
            - unread_count: Количество непрочитанных уведомлений
    """
    context = {
        "notifications": request.user.notifications.all().order_by("-created_at"),
        "unread_count": request.user.notifications.filter(is_read=False).count(),
    }
    return render(request, "lf/notifications.html", context)


@login_required
def notification_detail(request, notification_id):
    """
    Отображает детали уведомления и помечает его как прочитанное.

    Args:
        request: HttpRequest объект
        notification_id: ID уведомления

    Returns:
        HttpResponse с шаблоном notification_detail.html и контекстом:
            - notification: Объект уведомления
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()  # Помечаем как прочитанное

    return render(request, "lf/notification_detail.html", {"notification": notification})


@login_required
def mark_all_as_read(request):
    """
    Помечает все уведомления пользователя как прочитанные.

    Args:
        request: HttpRequest объект

    Returns:
        Перенаправление на список уведомлений
    """
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("notifications_list")

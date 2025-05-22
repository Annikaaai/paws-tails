import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from main.models import *
from main.forms import *
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import PermissionDenied

"""
Django views для функционала чатов и сообщений между пользователями.
Включает создание чатов, отправку сообщений, управление чатами и сообщениями.
"""

logger = logging.getLogger(__name__)


@login_required
def user_list(request):
    """
    Отображает список пользователей для начала чата.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном списка пользователей или страницей ошибки
    """
    try:
        logger.info(f"User list accessed by {request.user.username}")
        users = get_user_model().objects.exclude(id=request.user.id).order_by("username")
        return render(request, "socials/user_list.html", {"users": users})
    except Exception as e:
        logger.error(f"Error in user_list: {str(e)}", exc_info=True)
        messages.error(request, "Произошла ошибка при загрузке списка пользователей")
        return render(request, "socials/user_list.html", {"users": []})


@login_required
def chat_combined(request, chat_id=None):
    """
    Комбинированное представление чатов с обработкой AJAX-запросов.
    Обрабатывает:
    - Просмотр списка чатов
    - Просмотр конкретного чата
    - AJAX-запросы на получение/удаление/редактирование сообщений

    Args:
        request: HttpRequest объект
        chat_id: ID чата (опционально)

    Returns:
        HttpResponse с шаблоном чата или JSON-ответ для AJAX
    """
    try:
        # Получаем все активные чаты пользователя
        chats = Chat.objects.filter(participants=request.user, is_deleted=False).order_by("-updated_at").distinct()

        # Обработка AJAX-запросов
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            action = request.GET.get("action")

            if action == "get_messages":
                return _handle_get_messages(request, chat_id, chats)
            elif action == "delete_message":
                return _handle_delete_message(request)
            elif action == "edit_message":
                return _handle_edit_message(request)
            else:
                return JsonResponse({"error": "Invalid action"}, status=400)

        # Подготовка контекста для обычного запроса
        context = {
            "chats": chats,
            "current_chat": None,
            "messages_list": [],
            "other_user": None,
            "chats_with_unread": [(chat, chat.get_unread_count(request.user)) for chat in chats],
        }

        if chat_id:
            current_chat = get_object_or_404(Chat, id=chat_id, participants=request.user, is_deleted=False)
            messages_list = current_chat.messages.filter(is_deleted=False).order_by("timestamp")
            other_user = current_chat.participants.exclude(id=request.user.id).first()

            messages_list.exclude(sender=request.user).update(read=True)
            logger.info(f"Chat {chat_id} opened by {request.user.username}")

            context.update(
                {
                    "current_chat": current_chat,
                    "messages_list": messages_list,
                    "other_user": other_user,
                }
            )

        return render(request, "socials/chat_combined.html", context)
    except PermissionDenied:
        logger.warning(f"Unauthorized access attempt by {request.user.username}")
        return render(request, "socials/error.html", {"message": "Доступ запрещен"}, status=403)
    except Http404:
        raise  # Пробрасываем 404 дальше
    except Exception as e:
        logger.error(f"Error in chat_combined: {str(e)}", exc_info=True)
        return render(request, "socials/error.html", {"message": "Внутренняя ошибка сервера"}, status=500)


def _handle_get_messages(request, chat_id, chats):
    """
    Обработчик AJAX-запроса на получение новых сообщений.

    Args:
        request: HttpRequest объект
        chat_id: ID чата
        chats: QuerySet чатов пользователя

    Returns:
        JsonResponse с новыми сообщениями и счетчиками непрочитанных
    """
    last_message_id = request.GET.get("last_message", 0)
    try:
        last_message_id = int(last_message_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid message ID"}, status=400)

    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    new_messages = chat.messages.filter(id__gt=last_message_id, is_deleted=False).order_by("timestamp")

    messages_data = [
        {
            "id": msg.id,
            "content": msg.content,
            "image_url": msg.image.url if msg.image else None,
            "sender": msg.sender.username,
            "timestamp": msg.timestamp.strftime("%H:%M"),
            "is_current_user": msg.sender == request.user,
            "edited": msg.edited,
            "is_deleted": msg.is_deleted,
        }
        for msg in new_messages
    ]

    if new_messages.exists():
        new_messages.exclude(sender=request.user).update(read=True)
        logger.info(f"New messages retrieved in chat {chat_id}")

    return JsonResponse(
        {
            "new_messages": messages_data,
            "unread_counts": {chat.id: chat.get_unread_count(request.user) for chat in chats},
        }
    )


def _handle_delete_message(request):
    """
    Обработчик AJAX-запроса на удаление сообщения.

    Args:
        request: HttpRequest объект

    Returns:
        JsonResponse с результатом операции
    """
    message_id = request.GET.get("message_id")
    if not message_id:
        return JsonResponse({"error": "Message ID required"}, status=400)

    message = get_object_or_404(Message, id=message_id, sender=request.user)
    message.soft_delete()
    logger.info(f"Message {message_id} deleted by {request.user.username}")
    return JsonResponse({"success": True})


def _handle_edit_message(request):
    """
    Обработчик AJAX-запроса на редактирование сообщения.

    Args:
        request: HttpRequest объект

    Returns:
        JsonResponse с обновленными данными сообщения
    """
    message_id = request.GET.get("message_id")
    new_content = request.GET.get("content", "").strip()

    if not message_id:
        return JsonResponse({"error": "Message ID required"}, status=400)
    if not new_content:
        return JsonResponse({"error": "Content cannot be empty"}, status=400)

    message = get_object_or_404(Message, id=message_id, sender=request.user)
    message.edit_message(new_content)
    logger.info(f"Message {message_id} edited by {request.user.username}")

    return JsonResponse(
        {
            "success": True,
            "content": message.content,
            "edited": message.edited,
        }
    )


@login_required
@require_POST
def delete_chat(request, chat_id):
    """
    Мягкое удаление чата (помечаем как удаленный).

    Args:
        request: HttpRequest объект (POST)
        chat_id: ID чата

    Returns:
        Перенаправление на список чатов
    """
    try:
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        chat.soft_delete()
        logger.info(f"Chat {chat_id} deleted by {request.user.username}")
        messages.success(request, "Чат успешно удален")
        return redirect("chat_combined")
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {str(e)}", exc_info=True)
        messages.error(request, "Ошибка при удалении чата")
        return redirect("chat_combined")


@login_required
def chat_detail(request, chat_id):
    """
    Детальное представление чата с возможностью отправки сообщений.

    Args:
        request: HttpRequest объект
        chat_id: ID чата

    Returns:
        HttpResponse с шаблоном чата
    """
    try:
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        messages_list = chat.messages.filter(is_deleted=False).order_by("timestamp")
        other_user = chat.participants.exclude(id=request.user.id).first()

        messages_list.exclude(sender=request.user).update(read=True)

        if request.method == "POST":
            form = MessageForm(request.POST, request.FILES)
            if form.is_valid():
                Message.objects.create(
                    chat=chat,
                    sender=request.user,
                    content=form.cleaned_data["content"],
                    image=form.cleaned_data["image"],
                )
                chat.updated_at = timezone.now()
                chat.save()
                logger.info(f"Message sent to chat {chat_id} by {request.user.username}")
                return redirect("chat_detail", chat_id=chat.id)
            else:
                messages.error(request, "Ошибка в форме сообщения")
        else:
            form = MessageForm()

        logger.info(f"Chat {chat_id} opened by {request.user.username}")
        return render(
            request,
            "socials/chat_detail.html",
            {
                "chat": chat,
                "messages_list": messages_list,
                "other_user": other_user,
                "form": form,
            },
        )
    except Exception as e:
        logger.error(f"Error in chat_detail for chat {chat_id}: {str(e)}", exc_info=True)
        messages.error(request, "Ошибка при загрузке чата")
        return redirect("chat_combined")


@login_required
def start_chat(request, user_id):
    """
    Создает новый чат с пользователем или восстанавливает удаленный.

    Args:
        request: HttpRequest объект
        user_id: ID пользователя для чата

    Returns:
        Перенаправление в созданный/восстановленный чат
    """
    try:
        other_user = get_object_or_404(get_user_model(), id=user_id)

        if request.user == other_user:
            logger.warning(f"User {request.user.username} tried to chat with themselves")
            messages.warning(request, "Нельзя начать чат с самим собой")
            return redirect("profile")

        # Ищем существующий чат (включая удаленные)
        chat = Chat.objects.filter(participants=request.user).filter(participants=other_user).first()

        if chat:
            if chat.is_deleted:
                chat.is_deleted = False
                chat.save()
                logger.info(f"Restored deleted chat with {other_user.username}")
                messages.info(request, "Чат восстановлен")
            else:
                messages.info(request, "Чат уже существует")
        else:
            chat = Chat.objects.create()
            chat.participants.add(request.user, other_user)
            logger.info(f"Created new chat with {other_user.username}")
            messages.success(request, "Новый чат создан")

        return redirect("chat_detail", chat_id=chat.id)
    except Exception as e:
        logger.error(f"Error starting chat with user {user_id}: {str(e)}", exc_info=True)
        messages.error(request, "Ошибка при создании чата")
        return redirect("user_list")


@login_required
@require_POST
def send_message(request, chat_id):
    """
    Отправляет сообщение в чат (AJAX).

    Args:
        request: HttpRequest объект (POST)
        chat_id: ID чата

    Returns:
        JsonResponse с данными отправленного сообщения или ошибкой
    """
    try:
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        form = MessageForm(request.POST, request.FILES)

        if not form.is_valid():
            errors = form.errors.get_json_data()
            logger.warning(f"Invalid message form in chat {chat_id}: {errors}")
            return JsonResponse({"success": False, "errors": errors}, status=400)

        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=form.cleaned_data["content"],
            image=form.cleaned_data["image"],
        )
        chat.updated_at = timezone.now()
        chat.save()
        logger.info(f"Message sent to chat {chat_id} by {request.user.username}")

        response_data = {
            "success": True,
            "message": {
                "id": message.id,
                "content": message.content,
                "timestamp": message.timestamp.strftime("%H:%M"),
                "sender": message.sender.username,
                "is_current_user": True,
                "image_url": message.image.url if message.image else None,
            },
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error sending message to chat {chat_id}: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e)}, status=500)

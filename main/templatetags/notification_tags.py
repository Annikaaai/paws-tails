from django import template
from ..models import Notification  # или полный путь к вашей модели

register = template.Library()


@register.filter
def unread_notifications_count(user):
    return user.notifications.filter(is_read=False).count()

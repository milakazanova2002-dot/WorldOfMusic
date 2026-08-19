from .models import Notification


def notifications(request):
    """Добавляет в контекст любого шаблона: unread_notifications_count и
    recent_notifications (последние 5) для авторизованного пользователя.
    Используется колокольчиком в хедере (base.html)."""
    if not request.user.is_authenticated:
        return {}

    qs = Notification.objects.filter(user=request.user)
    return {
        "unread_notifications_count": qs.filter(is_read=False).count(),
        "recent_notifications": qs[:5],
    }

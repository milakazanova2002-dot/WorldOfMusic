from django.core.cache import cache

from .models import Notification


def notifications(request):
    """Добавляет в контекст любого шаблона: unread_notifications_count и
    recent_notifications (последние 5) для авторизованного пользователя.
    Используется колокольчиком в хедере (base.html).

    Кешируем на 30 секунд — это самое частое обращение к базе на сайте
    (срабатывает на КАЖДОЙ странице у любого залогиненного пользователя),
    а 30 секунд устаревания незаметны для человека, листающего сайт."""
    if not request.user.is_authenticated:
        return {}

    cache_key = f"notifications:{request.user.id}"
    data = cache.get(cache_key)
    if data is not None:
        return data

    qs = Notification.objects.filter(user=request.user)
    data = {
        "unread_notifications_count": qs.filter(is_read=False).count(),
        "recent_notifications": list(qs[:5]),
    }
    cache.set(cache_key, data, 30)
    return data

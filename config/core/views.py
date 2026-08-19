from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Notification


class HomeView(TemplateView):
    template_name = "core/home.html"


class NotificationListView(LoginRequiredMixin, ListView):
    """Полный список уведомлений пользователя."""
    model = Notification
    template_name = "core/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # заходя на страницу со всеми уведомлениями — считаем их прочитанными
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return response


@login_required
@require_POST
def notification_mark_read(request, pk):
    """Отмечает одно уведомление прочитанным и ведёт по его ссылке (клик по колокольчику)."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.link or "home")
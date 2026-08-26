from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy

from .forms import SupportRequestForm
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
        cache.delete(f"notifications:{request.user.id}")
        return response


@login_required
@require_POST
def notification_mark_read(request, pk):
    """Отмечает одно уведомление прочитанным и ведёт по его ссылке (клик по колокольчику)."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    cache.delete(f"notifications:{request.user.id}")
    return redirect(notification.link or "home")


class SupportRequestCreateView(CreateView):
    """Форма «Написать в поддержку» — доступна всем, даже незалогиненным."""
    form_class = SupportRequestForm
    template_name = "core/support_form.html"
    success_url = reverse_lazy("support")

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial["email"] = self.request.user.email
        return initial

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        messages.success(self.request, "Заявка отправлена! Мы ответим на указанный email.")
        return super().form_valid(form)


class FAQView(TemplateView):
    template_name = "core/faq.html"
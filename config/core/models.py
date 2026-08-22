from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Уведомление пользователю: новый урок, задание, комментарий педагога и т.п."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Кому"
    )

    text = models.CharField(max_length=255, verbose_name="Текст")

    # Относительная ссылка (например /education/lesson/5/), куда ведёт уведомление.
    link = models.CharField(max_length=255, blank=True, verbose_name="Ссылка")

    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.text}"

    @staticmethod
    def notify(user, text, link=""):
        """Короткий помощник для создания уведомления из любого места в коде:
        Notification.notify(student.user, "Новый урок", link=lesson.get_absolute_url())"""
        return Notification.objects.create(user=user, text=text, link=link)


class SupportRequest(models.Model):
    """Заявка в поддержку — форма обратной связи на сайте."""

    subject = models.CharField(max_length=200, verbose_name="Тема")
    message = models.TextField(verbose_name="Сообщение")
    email = models.EmailField(verbose_name="Email для ответа")

    # Если писал залогиненный пользователь — сохраняем связь, но поле необязательное:
    # гость (не пользователь сайта) тоже может написать в поддержку.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_requests",
        verbose_name="Пользователь",
    )

    is_resolved = models.BooleanField(default=False, verbose_name="Решено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Заявка в поддержку"
        verbose_name_plural = "Заявки в поддержку"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.email})"

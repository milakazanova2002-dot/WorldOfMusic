from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from core.forms import SupportRequestForm
from core.models import Notification, SupportRequest


class NotificationHelperTests(TestCase):
    """Notification.notify — общий помощник для создания уведомлений."""

    def setUp(self):
        self.user = User.objects.create_user(username="notif_user", password="pass12345", gender=User.Gender.MALE)

    def test_notify_creates_unread_notification(self):
        notification = Notification.notify(self.user, "Новый урок", link="/education/lesson/1/")

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.user, self.user)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.link, "/education/lesson/1/")

    def test_str_contains_username_and_text(self):
        notification = Notification.notify(self.user, "Текст уведомления")
        self.assertIn("notif_user", str(notification))
        self.assertIn("Текст уведомления", str(notification))


class NotificationMarkReadViewTests(TestCase):
    """Клик по уведомлению помечает его прочитанным и ведёт по ссылке."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="click_user", password="pass12345", gender=User.Gender.MALE)
        self.other_user = User.objects.create_user(username="other_user", password="pass12345", gender=User.Gender.MALE)
        self.client = Client()
        self.client.login(username="click_user", password="pass12345")

    def test_marks_notification_as_read_and_redirects_to_link(self):
        notification = Notification.notify(self.user, "Проверьте задание", link="/education/lesson/5/")

        response = self.client.post(reverse("notification_mark_read", kwargs={"pk": notification.pk}))

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertRedirects(response, "/education/lesson/5/", fetch_redirect_response=False)

    def test_redirects_home_when_no_link(self):
        notification = Notification.notify(self.user, "Без ссылки")

        response = self.client.post(reverse("notification_mark_read", kwargs={"pk": notification.pk}))

        self.assertRedirects(response, reverse("home"))

    def test_cannot_mark_someone_elses_notification(self):
        foreign_notification = Notification.notify(self.other_user, "Чужое уведомление")

        response = self.client.post(reverse("notification_mark_read", kwargs={"pk": foreign_notification.pk}))

        self.assertEqual(response.status_code, 404)
        foreign_notification.refresh_from_db()
        self.assertFalse(foreign_notification.is_read)

    def test_get_request_not_allowed(self):
        notification = Notification.notify(self.user, "GET не разрешён")
        response = self.client.get(reverse("notification_mark_read", kwargs={"pk": notification.pk}))
        self.assertEqual(response.status_code, 405)


class SupportRequestFormTests(TestCase):
    def test_valid_data_is_accepted(self):
        form = SupportRequestForm(data={
            "subject": "Не приходит письмо",
            "message": "Зарегистрировался, но письмо с подтверждением не пришло.",
            "email": "user@example.com",
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields_is_invalid(self):
        form = SupportRequestForm(data={"subject": "", "message": "", "email": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("subject", form.errors)
        self.assertIn("message", form.errors)
        self.assertIn("email", form.errors)

    def test_invalid_email_is_rejected(self):
        form = SupportRequestForm(data={
            "subject": "Тема",
            "message": "Сообщение",
            "email": "not-an-email",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class SupportRequestCreateViewTests(TestCase):
    """Форма поддержки доступна всем, для гостя привязка к пользователю не создаётся."""

    def test_anonymous_user_can_submit_support_request(self):
        client = Client()
        response = client.post(reverse("support"), {
            "subject": "Вопрос",
            "message": "Как зарегистрироваться как педагог?",
            "email": "guest@example.com",
        })

        self.assertRedirects(response, reverse("support"))
        request_obj = SupportRequest.objects.get(email="guest@example.com")
        self.assertIsNone(request_obj.user)

    def test_authenticated_user_request_is_linked_to_account(self):
        user = User.objects.create_user(username="support_user", password="pass12345", gender=User.Gender.MALE)
        client = Client()
        client.login(username="support_user", password="pass12345")

        client.post(reverse("support"), {
            "subject": "Вопрос от юзера",
            "message": "Проверка привязки заявки к аккаунту.",
            "email": "support_user@example.com",
        })

        request_obj = SupportRequest.objects.get(subject="Вопрос от юзера")
        self.assertEqual(request_obj.user, user)

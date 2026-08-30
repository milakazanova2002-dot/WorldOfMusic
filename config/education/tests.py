from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from core.models import Notification
from education.models import (
    Lesson,
    ParentLink,
    Performance,
    StudentProfile,
    Subject,
    TeacherProfile,
    TeachingAssignment,
)


def make_teacher(username, approved=True):
    # is_approved передаём сразу при создании: если True, сигнал
    # create_teacher_profile_after_approval (accounts/signals.py) может
    # создать TeacherProfile сам — поэтому дальше используем get_or_create,
    # а не create, чтобы не словить дубликат независимо от того,
    # успел сигнал сработать или нет.
    user = User.objects.create_user(
        username=username, password="pass12345", gender=User.Gender.MALE, is_approved=approved
    )
    profile, _ = TeacherProfile.objects.get_or_create(user=user)
    return profile


def make_student(username):
    user = User.objects.create_user(username=username, password="pass12345", gender=User.Gender.FEMALE)
    return StudentProfile.objects.create(user=user)


class ModelStrTests(TestCase):
    """__str__ у ключевых моделей должен быть человекочитаемым."""

    def test_teacher_profile_str(self):
        teacher = make_teacher("t_str")
        teacher.user.first_name = "Иван"
        teacher.user.last_name = "Иванов"
        teacher.user.save()
        self.assertIn("Иван", str(teacher))

    def test_student_profile_str(self):
        student = make_student("s_str")
        student.user.first_name = "Аня"
        student.user.save()
        self.assertIn("Аня", str(student))

    def test_teaching_assignment_str_contains_subject(self):
        teacher = make_teacher("t_ta")
        student = make_student("s_ta")
        subject = Subject.objects.create(name="вокал", slug="vocal")
        assignment = TeachingAssignment.objects.create(teacher=teacher, student=student, subject=subject)
        self.assertIn("вокал", str(assignment))


class ParentLinkFlowTests(TestCase):
    """Полный цикл: запрос родителя → уведомление → подтверждение → доступ."""

    def setUp(self):
        self.parent = User.objects.create_user(username="parent_flow", password="pass12345", gender=User.Gender.FEMALE)
        self.student = make_student("student_flow")
        self.client = Client()

    def test_request_creates_link_and_notifies_student(self):
        self.client.login(username="parent_flow", password="pass12345")

        response = self.client.post(
            reverse("education:parent_request_link"),
            {"student_id": self.student.pk},
        )

        self.assertRedirects(response, reverse("education:parent_request_link"))
        link = ParentLink.objects.get(parent__username="parent_flow", student=self.student)
        self.assertFalse(link.is_approved)
        self.assertTrue(Notification.objects.filter(user=self.student.user).exists())

    def test_second_request_does_not_duplicate_link(self):
        self.client.login(username="parent_flow", password="pass12345")

        self.client.post(reverse("education:parent_request_link"), {"student_id": self.student.pk})
        self.client.post(reverse("education:parent_request_link"), {"student_id": self.student.pk})

        self.assertEqual(
            ParentLink.objects.filter(parent__username="parent_flow", student=self.student).count(), 1
        )

    def test_student_or_teacher_cannot_access_parent_section(self):
        self.client.login(username=self.student.user.username, password="pass12345")

        response = self.client.get(reverse("education:parent_request_link"))

        self.assertEqual(response.status_code, 403)

    def test_approve_grants_access_to_student_detail(self):
        link = ParentLink.objects.create(parent=self.parent, student=self.student)

        self.client.login(username=self.student.user.username, password="pass12345")
        response = self.client.post(
            reverse("education:parent_link_confirm", kwargs={"pk": link.pk}),
            {"action": "approve"},
        )
        self.assertRedirects(
            response, reverse("accounts:role_redirect"), fetch_redirect_response=False
        )

        link.refresh_from_db()
        self.assertTrue(link.is_approved)
        self.assertTrue(Notification.objects.filter(user=self.parent).exists())

        self.client.logout()
        self.client.login(username="parent_flow", password="pass12345")
        detail_response = self.client.get(reverse("education:student_detail", kwargs={"pk": self.student.pk}))
        self.assertEqual(detail_response.status_code, 200)

    def test_unapproved_parent_cannot_view_student_detail(self):
        ParentLink.objects.create(parent=self.parent, student=self.student)  # ещё не подтверждено

        self.client.login(username="parent_flow", password="pass12345")
        response = self.client.get(reverse("education:student_detail", kwargs={"pk": self.student.pk}))

        self.assertEqual(response.status_code, 403)

    def test_decline_deletes_the_link(self):
        link = ParentLink.objects.create(parent=self.parent, student=self.student)

        self.client.login(username=self.student.user.username, password="pass12345")
        self.client.post(
            reverse("education:parent_link_confirm", kwargs={"pk": link.pk}),
            {"action": "decline"},
        )

        self.assertFalse(ParentLink.objects.filter(pk=link.pk).exists())


class StudentDetailAccessTests(TestCase):
    """Доступ к странице ученика: сам ученик, его педагог, чужие — запрет."""

    def setUp(self):
        self.subject = Subject.objects.create(name="фортепиано", slug="piano")
        self.teacher = make_teacher("t_access")
        self.other_teacher = make_teacher("t_other")
        self.student = make_student("s_access")
        self.other_student = make_student("s_other")
        TeachingAssignment.objects.create(teacher=self.teacher, student=self.student, subject=self.subject)
        self.client = Client()

    def test_student_can_view_own_page(self):
        self.client.login(username=self.student.user.username, password="pass12345")
        response = self.client.get(reverse("education:student_detail", kwargs={"pk": self.student.pk}))
        self.assertEqual(response.status_code, 200)

    def test_other_student_cannot_view_page(self):
        self.client.login(username=self.other_student.user.username, password="pass12345")
        response = self.client.get(reverse("education:student_detail", kwargs={"pk": self.student.pk}))
        self.assertEqual(response.status_code, 403)

    def test_assigned_teacher_can_view_page(self):
        self.client.login(username=self.teacher.user.username, password="pass12345")
        response = self.client.get(reverse("education:student_detail", kwargs={"pk": self.student.pk}))
        self.assertEqual(response.status_code, 200)

    def test_unrelated_teacher_cannot_view_page(self):
        self.client.login(username=self.other_teacher.user.username, password="pass12345")
        response = self.client.get(reverse("education:student_detail", kwargs={"pk": self.student.pk}))
        self.assertEqual(response.status_code, 403)


class LessonAccessTests(TestCase):
    """Доступ к уроку — только у своего педагога и своего ученика."""

    def setUp(self):
        self.subject = Subject.objects.create(name="гитара", slug="guitar")
        self.teacher = make_teacher("t_lesson")
        self.student = make_student("s_lesson")
        self.stranger = make_student("s_stranger")
        assignment = TeachingAssignment.objects.create(teacher=self.teacher, student=self.student, subject=self.subject)
        self.lesson = Lesson.objects.create(assignment=assignment, student=self.student, date=timezone.now())
        self.client = Client()

    def test_owner_student_can_view_lesson(self):
        self.client.login(username=self.student.user.username, password="pass12345")
        response = self.client.get(reverse("education:lesson_detail", kwargs={"pk": self.lesson.pk}))
        self.assertEqual(response.status_code, 200)

    def test_owner_teacher_can_view_lesson(self):
        self.client.login(username=self.teacher.user.username, password="pass12345")
        response = self.client.get(reverse("education:lesson_detail", kwargs={"pk": self.lesson.pk}))
        self.assertEqual(response.status_code, 200)

    def test_unrelated_student_cannot_view_lesson(self):
        self.client.login(username=self.stranger.user.username, password="pass12345")
        response = self.client.get(reverse("education:lesson_detail", kwargs={"pk": self.lesson.pk}))
        self.assertEqual(response.status_code, 403)


class PerformanceAccessTests(TestCase):
    """Доступ к исполнению: свои ученик/педагог + суперпользователь."""

    def setUp(self):
        self.subject = Subject.objects.create(name="скрипка", slug="violin")
        self.teacher = make_teacher("t_perf")
        self.student = make_student("s_perf")
        self.stranger = make_student("s_perf_stranger")
        assignment = TeachingAssignment.objects.create(teacher=self.teacher, student=self.student, subject=self.subject)
        self.performance = Performance.objects.create(assignment=assignment)
        self.client = Client()

    def test_owner_student_can_view(self):
        self.client.login(username=self.student.user.username, password="pass12345")
        response = self.client.get(reverse("education:performance_detail", kwargs={"pk": self.performance.pk}))
        self.assertEqual(response.status_code, 200)

    def test_unrelated_student_forbidden(self):
        self.client.login(username=self.stranger.user.username, password="pass12345")
        response = self.client.get(reverse("education:performance_detail", kwargs={"pk": self.performance.pk}))
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_view_any_performance(self):
        User.objects.create_superuser(username="root", email="root@example.com", password="rootpass")
        self.client.login(username="root", password="rootpass")
        response = self.client.get(reverse("education:performance_detail", kwargs={"pk": self.performance.pk}))
        self.assertEqual(response.status_code, 200)


class MyStudentsAndTeachersDedupTests(TestCase):
    """Список 'своих' учеников/педагогов не должен дублироваться из-за
    нескольких предметов между теми же людьми."""

    def setUp(self):
        self.teacher = make_teacher("t_dedup")
        self.student = make_student("s_dedup")
        vocal = Subject.objects.create(name="вокал2", slug="vocal2")
        piano = Subject.objects.create(name="фортепиано2", slug="piano2")
        TeachingAssignment.objects.create(teacher=self.teacher, student=self.student, subject=vocal)
        TeachingAssignment.objects.create(teacher=self.teacher, student=self.student, subject=piano)
        self.client = Client()

    def test_teacher_sees_student_once(self):
        self.client.login(username=self.teacher.user.username, password="pass12345")
        response = self.client.get(reverse("education:my_students"))
        self.assertEqual(list(response.context["students"]), [self.student])

    def test_student_sees_teacher_once(self):
        self.client.login(username=self.student.user.username, password="pass12345")
        response = self.client.get(reverse("education:my_teachers"))
        self.assertEqual(list(response.context["teachers"]), [self.teacher])

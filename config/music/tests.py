from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from education.models import Lesson, StudentProfile, Subject, TeacherProfile, TeachingAssignment
from music.models import Composer, Favorite, Genre, MusicalPiece, MusicMaterial


def make_piece(title, composer_first="Иоганн", composer_last="Бах"):
    composer = Composer.objects.create(first_name=composer_first, last_name=composer_last)
    return MusicalPiece.objects.create(title=title, composer=composer)


class MusicalPieceModelTests(TestCase):
    def test_str_returns_title(self):
        piece = make_piece("Аве Мария")
        self.assertEqual(str(piece), "Аве Мария")

    def test_get_gradient_class_has_default_when_no_genre(self):
        piece = make_piece("Без жанра")
        self.assertIn("linear-gradient", piece.get_gradient_class())


class MusicalPieceSearchTests(TestCase):
    """Поиск и фильтрация каталога произведений."""

    def setUp(self):
        cache.clear()
        self.piece_bach = make_piece("Токката и фуга", "Иоганн Себастьян", "Бах")
        self.piece_mozart = make_piece("Реквием", "Вольфганг", "Моцарт")
        self.client = Client()

    def test_search_by_title(self):
        response = self.client.get(reverse("music:piece_list"), {"q": "Токката"})
        pieces = list(response.context["pieces"])
        self.assertIn(self.piece_bach, pieces)
        self.assertNotIn(self.piece_mozart, pieces)

    def test_search_by_composer_last_name(self):
        response = self.client.get(reverse("music:piece_list"), {"q": "Моцарт"})
        pieces = list(response.context["pieces"])
        self.assertIn(self.piece_mozart, pieces)
        self.assertNotIn(self.piece_bach, pieces)

    def test_filter_by_genre(self):
        genre = Genre.objects.create(name="классика")
        self.piece_bach.genre.add(genre)

        response = self.client.get(reverse("music:piece_list"), {"genre": genre.pk})
        pieces = list(response.context["pieces"])

        self.assertIn(self.piece_bach, pieces)
        self.assertNotIn(self.piece_mozart, pieces)

    def test_no_query_returns_everything(self):
        response = self.client.get(reverse("music:piece_list"))
        pieces = list(response.context["pieces"])
        self.assertIn(self.piece_bach, pieces)
        self.assertIn(self.piece_mozart, pieces)


class FavoriteToggleViewTests(TestCase):
    """Добавление/снятие произведения из избранного одним и тем же запросом."""

    def setUp(self):
        self.piece = make_piece("Лунная соната")
        self.user = User.objects.create_user(username="fav_user", password="pass12345", gender=User.Gender.MALE)
        self.client = Client()
        self.client.login(username="fav_user", password="pass12345")

    def test_first_post_adds_to_favorites(self):
        self.client.post(reverse("music:favorite_toggle", kwargs={"pk": self.piece.pk}))
        self.assertTrue(Favorite.objects.filter(user=self.user, piece=self.piece).exists())

    def test_second_post_removes_from_favorites(self):
        url = reverse("music:favorite_toggle", kwargs={"pk": self.piece.pk})
        self.client.post(url)
        self.client.post(url)
        self.assertFalse(Favorite.objects.filter(user=self.user, piece=self.piece).exists())

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.post(reverse("music:favorite_toggle", kwargs={"pk": self.piece.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Favorite.objects.filter(piece=self.piece).exists())


class PieceDetailPrivacyTests(TestCase):
    """Приватные материалы произведения видят только педагоги/причастные ученики."""

    def setUp(self):
        self.piece = make_piece("Вальс цветов")
        MusicMaterial.objects.create(
            piece=self.piece, type=MusicMaterial.MaterialType.SHEET,
            description="Публичные ноты", is_public=True,
        )
        self.private_material = MusicMaterial.objects.create(
            piece=self.piece, type=MusicMaterial.MaterialType.SHEET,
            description="Приватные ноты", is_public=False,
        )
        self.client = Client()

    def test_anonymous_sees_only_public_materials(self):
        response = self.client.get(reverse("music:piece_detail", kwargs={"pk": self.piece.pk}))
        materials = list(response.context["materials"])
        self.assertNotIn(self.private_material, materials)
        self.assertFalse(response.context["has_private_access"])

    def test_approved_teacher_sees_private_materials(self):
        # is_approved=True при создании может автоматически создать TeacherProfile
        # через сигнал (accounts/signals.py) — get_or_create() не даст дубля.
        teacher_user = User.objects.create_user(
            username="t_priv", password="pass12345", gender=User.Gender.MALE, is_approved=True
        )
        TeacherProfile.objects.get_or_create(user=teacher_user)
        self.client.login(username="t_priv", password="pass12345")

        response = self.client.get(reverse("music:piece_detail", kwargs={"pk": self.piece.pk}))

        self.assertIn(self.private_material, list(response.context["materials"]))
        self.assertTrue(response.context["has_private_access"])

    def test_unrelated_student_does_not_see_private_materials(self):
        student_user = User.objects.create_user(username="s_priv", password="pass12345", gender=User.Gender.FEMALE)
        StudentProfile.objects.create(user=student_user)
        self.client.login(username="s_priv", password="pass12345")

        response = self.client.get(reverse("music:piece_detail", kwargs={"pk": self.piece.pk}))

        self.assertNotIn(self.private_material, list(response.context["materials"]))
        self.assertFalse(response.context["has_private_access"])

    def test_student_with_a_lesson_on_this_piece_sees_private_materials(self):
        teacher_user = User.objects.create_user(username="t_for_lesson", password="pass12345", gender=User.Gender.MALE)
        teacher = TeacherProfile.objects.create(user=teacher_user)
        student_user = User.objects.create_user(username="s_for_lesson", password="pass12345", gender=User.Gender.FEMALE)
        student = StudentProfile.objects.create(user=student_user)
        subject = Subject.objects.create(name="вокал3", slug="vocal3")
        assignment = TeachingAssignment.objects.create(teacher=teacher, student=student, subject=subject)
        Lesson.objects.create(assignment=assignment, student=student, date=timezone.now(), piece=self.piece)

        self.client.login(username="s_for_lesson", password="pass12345")
        response = self.client.get(reverse("music:piece_detail", kwargs={"pk": self.piece.pk}))

        self.assertIn(self.private_material, list(response.context["materials"]))
        self.assertTrue(response.context["has_private_access"])

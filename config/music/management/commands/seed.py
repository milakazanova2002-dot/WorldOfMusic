from django.core.management.base import BaseCommand
from music.models import Composer, Genre, Instrument, MusicalPiece
from education.models import Subject, TeacherProfile, StudentProfile, TeachingAssignment
from accounts.models import User


class Command(BaseCommand):
    help = 'Заполняет базу данных демо-данными'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Заполнение базы данных...'))

        # Создаём композиторов
        composers_data = [
            ('Иоганн Себастьян', 'Бах', 'Великий немецкий композитор и органист'),
            ('Вольфганг Амадей', 'Моцарт', 'Австрийский композитор и музыкант'),
            ('Пётр Ильич', 'Чайковский', 'Русский композитор, дирижёр и педагог'),
            ('Людвиг ван', 'Бетховен', 'Немецкий композитор и пианист'),
            ('Фридерик', 'Шопен', 'Французско-польский композитор и пианист'),
        ]

        composers = []
        for first_name, last_name, biography in composers_data:
            composer, created = Composer.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={'biography': biography}
            )
            if created:
                self.stdout.write(f'  ✅ Композитор: {first_name} {last_name}')
            composers.append(composer)

        # Создаём жанры
        genres_data = [
            ('Классика',),
            ('Романс',),
            ('Народная',),
            ('Оперная',),
            ('Хоровая',),
        ]

        genres = []
        for name in genres_data:
            genre, created = Genre.objects.get_or_create(name=name[0])
            if created:
                self.stdout.write(f'  ✅ Жанр: {name[0]}')
            genres.append(genre)

        # Создаём инструменты
        instruments_data = [
            ('Фортепиано', 'Клавишный клавишно-клавишный инструмент'),
            ('Скрипка', 'Смычковый струнный музыкальный инструмент'),
            ('Вокал', 'Исполнение музыкальных произведений голосом'),
            ('Гитара', 'Щипковый струнный музыкальный инструмент'),
            ('Флейта', 'Духовой музыкальный инструмент'),
        ]

        instruments = []
        for name, description in instruments_data:
            instrument, created = Instrument.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'  ✅ Инструмент: {name}')
            instruments.append(instrument)

        # Создаём предметы
        subjects_data = [
            ('Вокал', 'vocal'),
            ('Фортепиано', 'piano'),
            ('Гитара', 'guitar'),
            ('Скрипка', 'violin'),
        ]

        subjects = []
        for name, slug in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=name,
                defaults={'slug': slug}
            )
            if created:
                self.stdout.write(f'  ✅ Предмет: {name}')
            subjects.append(subject)

        # Создаём педагога
        teacher_user, _ = User.objects.get_or_create(
            username='teacher_ivanova',
            defaults={
                'first_name': 'Иванова',
                'last_name': 'Мария Петровна',
                'email': 'teacher@wom.ru',
                'is_approved': True,
                'is_active': True,
            }
        )

        teacher_profile, _ = TeacherProfile.objects.get_or_create(
            user=teacher_user,
            defaults={
                'bio': 'Педагог высшей категории, стаж 15 лет',
                'experience_years': 15,
            }
        )
        teacher_profile.instruments.set(instruments[:3])
        self.stdout.write(f'  ✅ Педагог: {teacher_user.get_full_name()}')

        # Создаём ученика
        student_user, _ = User.objects.get_or_create(
            username='student_petrova',
            defaults={
                'first_name': 'Петрова',
                'last_name': 'Анна',
                'email': 'student@wom.ru',
                'is_active': True,
            }
        )

        student_profile, _ = StudentProfile.objects.get_or_create(
            user=student_user,
            defaults={
                'age': 14,
                'level': 'Средний',
            }
        )
        student_profile.instruments.set(instruments[:2])
        self.stdout.write(f'  ✅ Ученик: {student_user.get_full_name()}')

        # Создаём связь педагог-ученик
        TeachingAssignment.objects.get_or_create(
            teacher=teacher_profile,
            student=student_profile,
            subject=subjects[0],  # Вокал
        )
        self.stdout.write('  ✅ Связь педагог-ученик создана')

        # Создаём произведения
        pieces_data = [
            {
                'title': 'Аониды',
                'composer': composers[0],  # Бах
                'genres': [genres[0]],  # Классика
                'instruments': [instruments[2]],  # Вокал
                'description': 'Одна из лучших романсов',
            },
            {
                'title': 'Молитва (Madrigal)',
                'composer': composers[1],  # Моцарт
                'genres': [genres[0], genres[4]],  # Классика, Хоровая
                'instruments': [instruments[2]],  # Вокал
                'description': 'Знаменитый романс',
            },
            {
                'title': 'Ночной покой',
                'composer': composers[3],  # Бетховен
                'genres': [genres[0]],
                'instruments': [instruments[0]],  # Фортепиано
                'description': 'Классическое фортепианное произведение',
            },
            {
                'title': 'Вальс цветов',
                'composer': composers[2],  # Чайковский
                'genres': [genres[0]],
                'instruments': [instruments[0]],  # Фортепиано
                'description': 'Экстравагантный вальс из балета',
            },
            {
                'title': 'Прелюдия ми минор',
                'composer': composers[4],  # Шопен
                'genres': [genres[0]],
                'instruments': [instruments[0]],  # Фортепиано
                'description': 'Лирическая прелюдия',
            },
        ]

        for data in pieces_data:
            piece, created = MusicalPiece.objects.get_or_create(
                title=data['title'],
                composer=data['composer'],
                defaults={
                    'description': data['description'],
                }
            )
            piece.genre.set(data['genres'])
            piece.instruments.set(data['instruments'])
            if created:
                self.stdout.write(f'  ✅ Произведение: {data["title"]}')

        self.stdout.write(self.style.SUCCESS('✅ База данных заполнена успешно!'))
        self.stdout.write('')
        self.stdout.write('Логин для входа:')
        self.stdout.write('  Педагог: teacher_ivanova / password')
        self.stdout.write('  Ученик: student_petrova / password')
import io
import math
import struct
import wave
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User
from education.models import (
    Lesson,
    ParentLink,
    Performance,
    PerformanceComment,
    StudentProfile,
    Subject,
    TeacherProfile,
    TeachingAssignment,
)
from music.models import Composer, Favorite, Genre, Instrument, MusicalPiece, MusicMaterial

# Пароль и формат логина — как попросили: одинаковый пароль у всех учебных
# аккаунтов, логин = транслитерированное имя + "@mail.ru".
DEMO_PASSWORD = "op[]90-="

# Демо-ссылка на свободно распространяемое видео (Big Buck Bunny, Blender
# Foundation, CC-BY) — используется только как заглушка для поля "видео
# исполнения", чтобы плеер на странице было на чём проверить. Замените на
# реальную запись, когда она появится.
DEMO_VIDEO_URL = "https://www.w3schools.com/html/mov_bbb.mp4"

TRANSLIT_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def translit(name):
    """Простая транслитерация имени в латиницу для логина/почты."""
    result = "".join(TRANSLIT_MAP.get(ch, ch) for ch in name.lower())
    return "".join(c for c in result if c.isalnum())


def make_tone_wav(freq=440, duration=2.5):
    """Генерирует короткий синус-тон в WAV на лету — чтобы минусовки были
    РЕАЛЬНО проигрываемыми файлами, без скачивания из интернета."""
    rate = 22050
    n_samples = int(rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        frames = bytearray()
        for i in range(n_samples):
            value = int(3000 * math.sin(2 * math.pi * freq * (i / rate)))
            frames += struct.pack("<h", value)
        wav.writeframes(bytes(frames))
    return buf.getvalue()


def get_or_create_subject(name):
    name = name.strip().lower()
    existing = Subject.objects.filter(name__iexact=name).first()
    if existing:
        return existing
    slug = slugify(name, allow_unicode=True)
    existing_by_slug = Subject.objects.filter(slug=slug).first()
    if existing_by_slug:
        return existing_by_slug
    return Subject.objects.create(name=name, slug=slug)


MALE_FIRST_NAMES = [
    "Иван", "Пётр", "Алексей", "Дмитрий", "Сергей", "Андрей", "Николай",
    "Владимир", "Михаил", "Максим", "Артём", "Кирилл", "Егор", "Роман",
    "Тимур", "Данил", "Игорь", "Олег", "Виктор", "Григорий", "Александр",
    "Владислав", "Степан", "Матвей", "Ярослав",
]

FEMALE_FIRST_NAMES = [
    "Анна", "Мария", "Елена", "Ольга", "Наталья", "Светлана", "Ирина",
    "Татьяна", "Юлия", "Дарья", "Виктория", "Полина", "Ксения", "Алина",
    "Софья", "Екатерина", "Валентина", "Людмила", "Марина", "Алёна",
    "Анастасия", "Евгения", "Вероника", "Диана", "Милана",
]

LAST_NAME_STEMS = [
    "Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Попов", "Соколов",
    "Лебедев", "Козлов", "Новиков", "Морозов", "Волков", "Алексеев", "Лукин",
    "Егоров", "Павлов", "Семёнов", "Голубев", "Виноградов", "Богданов",
    "Воробьёв", "Фёдоров", "Михайлов", "Беляев", "Тарасов", "Белов",
    "Комаров", "Орлов", "Киселёв", "Макаров",
]


def last_name(stem_index, gender):
    stem = LAST_NAME_STEMS[stem_index % len(LAST_NAME_STEMS)]
    return stem if gender == User.Gender.MALE else stem + "а"


INSTRUMENTS_DATA = [
    ("вокал", "Исполнение голосом"),
    ("национальная гармонь", "Народный клавишно-язычковый инструмент"),
    ("хор", "Коллективное вокальное исполнение"),
    ("гитара", "Щипковый струнный инструмент"),
    ("фортепиано", "Клавишный музыкальный инструмент"),
    ("аккордеон", "Язычковый клавишно-пневматический инструмент"),
    ("шикапшина", "Традиционный смычковый инструмент"),
    ("балалайка", "Народный щипковый струнный инструмент"),
]

GENRES = [
    "классика", "романс", "народная", "оперная", "хоровая",
    "джаз", "эстрада", "фольклор", "инструментальная музыка", "детская музыка",
]

COMPOSERS_DATA = [
    ("Иоганн Себастьян", "Бах", "Великий немецкий композитор и органист"),
    ("Вольфганг Амадей", "Моцарт", "Австрийский композитор и музыкант"),
    ("Пётр Ильич", "Чайковский", "Русский композитор, дирижёр и педагог"),
    ("Людвиг ван", "Бетховен", "Немецкий композитор и пианист"),
    ("Фридерик", "Шопен", "Французско-польский композитор и пианист"),
    ("Михаил", "Глинка", "Русский композитор, основоположник русской классической школы"),
    ("Арам", "Хачатурян", "Советский композитор и дирижёр"),
    ("Николай", "Римский-Корсаков", "Русский композитор и дирижёр"),
    ("Эдвард", "Григ", "Норвежский композитор и пианист"),
    ("Александр", "Бородин", "Русский композитор и учёный-химик"),
    ("Василий", "Агапкин", "Русский и советский военный дирижёр и композитор"),
    ("Народное", "творчество", "Автор неизвестен — произведение передавалось устно"),
]

# (название, индекс_композитора, [жанры], [инструменты], год, описание)
PIECES_DATA = [
    ("Соловей", 11, ["романс", "народная"], ["вокал"], 1826, "Русский романс на народный мотив"),
    ("Однозвучно гремит колокольчик", 11, ["романс"], ["вокал"], 1831, "Один из самых известных русских романсов"),
    ("Калинка", 11, ["народная"], ["балалайка", "национальная гармонь"], 1860, "Русская народная плясовая песня"),
    ("Во саду ли, в огороде", 11, ["народная"], ["балалайка"], 1800, "Русская народная песня"),
    ("Ой, мороз, мороз", 11, ["народная"], ["вокал", "национальная гармонь"], 1954, "Известная русская народная песня"),
    ("Лунная соната", 3, ["классика"], ["фортепиано"], 1801, "Соната №14 — одно из самых известных произведений для фортепиано"),
    ("К Элизе", 3, ["классика"], ["фортепиано"], 1810, "Багатель для фортепиано"),
    ("Времена года. Осень", 2, ["классика"], ["фортепиано"], 1876, "Пьеса из цикла «Времена года»"),
    ("Вальс цветов", 2, ["классика", "оперная"], ["фортепиано", "аккордеон"], 1892, "Вальс из балета «Щелкунчик»"),
    ("Аве Мария", 0, ["романс", "хоровая"], ["хор", "вокал"], 1859, "Один из самых известных духовных романсов"),
    ("Реквием (Lacrimosa)", 1, ["хоровая", "классика"], ["хор"], 1791, "Фрагмент знаменитого реквиема"),
    ("Танец с саблями", 6, ["инструментальная музыка"], ["аккордеон"], 1942, "Из балета «Гаянэ»"),
    ("Цыганочка", 11, ["народная"], ["гитара"], 1900, "Народная плясовая мелодия для гитары"),
    ("Романс о влюблённых", 11, ["романс"], ["гитара", "вокал"], 1974, "Лирический романс"),
    ("Полёт шмеля", 7, ["классика", "инструментальная музыка"], ["аккордеон", "фортепиано"], 1900, "Виртуозная оркестровая интермедия"),
    ("Чардаш", 11, ["инструментальная музыка"], ["аккордеон"], 1904, "Известная венгерская танцевальная пьеса"),
    ("Свадебный наигрыш", 11, ["фольклор"], ["шикапшина", "национальная гармонь"], 1900, "Традиционный свадебный наигрыш"),
    ("Праздничный наигрыш", 11, ["фольклор"], ["шикапшина"], 1900, "Наигрыш для народных гуляний"),
    ("Плясовая", 11, ["народная", "фольклор"], ["национальная гармонь", "балалайка"], 1900, "Плясовая мелодия"),
    ("Хор из оперы «Иван Сусанин»", 5, ["оперная", "хоровая"], ["хор"], 1836, "Знаменитый хор из первой русской классической оперы"),
    ("Попутная песня", 5, ["романс"], ["вокал"], 1840, "Один из первых русских романтических романсов"),
    ("Утро", 8, ["классика"], ["фортепиано"], 1875, "Пьеса из сюиты «Пер Гюнт»"),
    ("Ноктюрн ми-бемоль мажор", 4, ["классика", "романс"], ["фортепиано"], 1830, "Один из самых известных ноктюрнов"),
    ("Прелюдия до минор", 4, ["классика"], ["фортепиано"], 1839, "Лирическая фортепианная прелюдия"),
    ("Турецкий марш", 1, ["классика"], ["фортепиано", "аккордеон"], 1783, "Часть сонаты №11, одна из самых узнаваемых мелодий"),
    ("Половецкие пляски", 9, ["оперная", "хоровая"], ["хор"], 1890, "Хоровой фрагмент из оперы «Князь Игорь»"),
    ("Детская полька", 11, ["детская музыка"], ["аккордеон", "фортепиано"], 1900, "Лёгкая пьеса для начинающих"),
    ("Весёлые нотки", 11, ["детская музыка"], ["вокал"], 1900, "Песня для детского хора"),
    ("Джазовая импровизация №1", 11, ["джаз"], ["гитара", "фортепиано"], 1990, "Учебная джазовая пьеса"),
    ("Прощание славянки", 10, ["народная", "эстрада"], ["аккордеон", "национальная гармонь"], 1912, "Знаменитый русский марш"),
]

LEVELS = ["Начальный", "Средний", "Продвинутый"]

PATRONYMICS_MALE = ["Иванович", "Петрович", "Сергеевич", "Александрович", "Дмитриевич"]
PATRONYMICS_FEMALE = ["Ивановна", "Петровна", "Сергеевна", "Александровна", "Дмитриевна"]


class Command(BaseCommand):
    help = (
        "Заполняет базу полным набором дипломных демо-данных: 8 инструментов, "
        "10 жанров, 30 произведений, 30 учеников, 10 педагогов, 10 родителей, "
        "курсы, уроки, исполнения, минусовки и видео к нескольким произведениям."
    )

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Заполнение базы полным набором данных...\n"))

        # ---------- Справочники ----------

        composers = []
        for first_name, last_name_, biography in COMPOSERS_DATA:
            composer, _ = Composer.objects.get_or_create(
                first_name=first_name, last_name=last_name_, defaults={"biography": biography}
            )
            composers.append(composer)

        genres = {name: Genre.objects.get_or_create(name=name)[0] for name in GENRES}

        instruments = {}
        for name, description in INSTRUMENTS_DATA:
            instrument, _ = Instrument.objects.get_or_create(name=name, defaults={"description": description})
            instruments[name] = instrument
        instrument_list = [instruments[name] for name, _ in INSTRUMENTS_DATA]

        subjects = {}
        for name, _ in INSTRUMENTS_DATA:
            subjects[name] = get_or_create_subject(name)

        self.stdout.write(
            f"  ✅ Композиторов: {len(composers)}, жанров: {len(genres)}, "
            f"инструментов: {len(instruments)}, предметов: {len(subjects)}"
        )

        # ---------- Произведения ----------

        pieces = []
        for title, composer_idx, genre_names, instrument_names, year, description in PIECES_DATA:
            piece, _ = MusicalPiece.objects.get_or_create(
                title=title,
                composer=composers[composer_idx],
                defaults={"description": description, "year_created": year},
            )
            piece.genre.set([genres[g] for g in genre_names])
            piece.instruments.set([instruments[i] for i in instrument_names])
            pieces.append(piece)
        self.stdout.write(f"  ✅ Произведений: {len(pieces)}")

        # ---------- Минусовки и видео исполнения (к нескольким произведениям) ----------

        materials_added = 0
        for idx in range(0, len(pieces), 4):  # каждое 4-е произведение — 8 штук
            piece = pieces[idx]
            if not piece.materials.filter(type=MusicMaterial.MaterialType.MINUS).exists():
                MusicMaterial.objects.create(
                    piece=piece,
                    type=MusicMaterial.MaterialType.MINUS,
                    file=ContentFile(make_tone_wav(330, 3), name=f"minus_{piece.pk}.wav"),
                    description="Минусовка (демо-запись)",
                    is_public=True,
                )
                materials_added += 1
            if not piece.materials.filter(type=MusicMaterial.MaterialType.VIDEO).exists():
                MusicMaterial.objects.create(
                    piece=piece,
                    type=MusicMaterial.MaterialType.VIDEO,
                    url=DEMO_VIDEO_URL,
                    description="Видео исполнения (демо-ссылка — замените на реальную запись)",
                    is_public=True,
                )
                materials_added += 1
        self.stdout.write(f"  ✅ Материалов (минусовки/видео) добавлено: {materials_added} к {len(range(0, len(pieces), 4))} произведениям")

        # ---------- Педагоги ----------

        teacher_profiles = []
        credentials = []
        for i in range(10):
            gender = User.Gender.MALE if i % 2 == 0 else User.Gender.FEMALE
            first_names_pool = MALE_FIRST_NAMES if gender == User.Gender.MALE else FEMALE_FIRST_NAMES
            first_name = first_names_pool[i % len(first_names_pool)]
            surname = last_name(i, gender)
            patronymic = (
                PATRONYMICS_MALE[(i // 2) % len(PATRONYMICS_MALE)]
                if gender == User.Gender.MALE
                else PATRONYMICS_FEMALE[(i // 2) % len(PATRONYMICS_FEMALE)]
            )
            login = translit(first_name)
            base_login = login
            n = 1
            while User.objects.filter(username=login).exists():
                n += 1
                login = f"{base_login}{n}"
            email = f"{login}@mail.ru"

            user, created = User.objects.get_or_create(
                username=login,
                defaults={
                    "first_name": first_name,
                    "last_name": surname,
                    "patronymic": patronymic,
                    "email": email,
                    "gender": gender,
                    "is_approved": True,
                    "is_active": True,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()

            primary_instrument = instrument_list[i % len(instrument_list)]
            profile, _ = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={"bio": f"Педагог по классу «{primary_instrument.name}»", "experience_years": 2 + i * 2},
            )
            profile.instruments.set([primary_instrument])
            profile.subjects.set([subjects[primary_instrument.name]])

            teacher_profiles.append(profile)
            credentials.append(("Педагог", login, email))
        self.stdout.write(f"  ✅ Педагогов: {len(teacher_profiles)}")

        # ---------- Ученики ----------

        student_profiles = []
        for i in range(30):
            gender = User.Gender.MALE if i % 2 == 0 else User.Gender.FEMALE
            first_names_pool = MALE_FIRST_NAMES if gender == User.Gender.MALE else FEMALE_FIRST_NAMES
            # Педагоги уже заняли первые 10 имён каждого пола — берём со сдвигом,
            # чтобы логины не пересекались с педагогами.
            first_name = first_names_pool[(i // 2 + 5) % len(first_names_pool)]
            surname = last_name(i + 10, gender)
            login = translit(first_name)
            # Если транслитерация имени случайно совпала с уже занятым логином —
            # добавляем порядковый номер, чтобы логин остался уникальным.
            base_login = login
            n = 1
            while User.objects.filter(username=login).exists():
                n += 1
                login = f"{base_login}{n}"
            email = f"{login}@mail.ru"

            user, created = User.objects.get_or_create(
                username=login,
                defaults={
                    "first_name": first_name,
                    "last_name": surname,
                    "email": email,
                    "gender": gender,
                    "is_active": True,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()

            primary_instrument = instrument_list[i % len(instrument_list)]
            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={"age": 7 + (i % 11), "level": LEVELS[i % len(LEVELS)]},
            )
            profile.instruments.set([primary_instrument])

            student_profiles.append(profile)
            credentials.append(("Ученик", login, email))
        self.stdout.write(f"  ✅ Учеников: {len(student_profiles)}")

        # ---------- Родители ----------

        parent_links_created = 0
        for i in range(10):
            gender = User.Gender.MALE if i % 2 == 0 else User.Gender.FEMALE
            first_names_pool = MALE_FIRST_NAMES if gender == User.Gender.MALE else FEMALE_FIRST_NAMES
            first_name = first_names_pool[(i // 2 + 15) % len(first_names_pool)]

            # Родителя привязываем к одному из учеников — берём его фамилию,
            # чтобы было видно, что это семья.
            linked_student = student_profiles[i * 3]
            surname = linked_student.user.last_name

            login = translit(first_name)
            base_login = login
            n = 1
            while User.objects.filter(username=login).exists():
                n += 1
                login = f"{base_login}{n}"
            email = f"{login}@mail.ru"

            user, created = User.objects.get_or_create(
                username=login,
                defaults={
                    "first_name": first_name,
                    "last_name": surname,
                    "email": email,
                    "gender": gender,
                    "is_active": True,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()

            _, link_created = ParentLink.objects.get_or_create(
                parent=user, student=linked_student, defaults={"is_approved": True}
            )
            if link_created:
                parent_links_created += 1

            credentials.append(("Родитель", login, email))
        self.stdout.write(f"  ✅ Родителей: 10 (связей с учениками: {parent_links_created})")

        # ---------- Курсы (педагог—ученик—предмет) ----------

        # Группируем педагогов по инструменту, который они преподают.
        teachers_by_instrument = {}
        for profile in teacher_profiles:
            for instrument in profile.instruments.all():
                teachers_by_instrument.setdefault(instrument.name, []).append(profile)

        assignments = []
        for i, student in enumerate(student_profiles):
            instrument = student.instruments.first()
            if not instrument:
                continue
            candidates = teachers_by_instrument.get(instrument.name, [])
            if not candidates:
                continue
            teacher = candidates[i % len(candidates)]
            subject = subjects[instrument.name]
            assignment, _ = TeachingAssignment.objects.get_or_create(
                teacher=teacher, student=student, subject=subject
            )
            assignments.append((assignment, instrument))
        self.stdout.write(f"  ✅ Курсов (педагог—ученик—предмет): {len(assignments)}")

        # ---------- Уроки ----------

        pieces_by_instrument = {}
        for piece in pieces:
            for instrument in piece.instruments.all():
                pieces_by_instrument.setdefault(instrument.name, []).append(piece)

        now = timezone.now()
        lessons_created = 0
        for i, (assignment, instrument) in enumerate(assignments):
            matching_pieces = pieces_by_instrument.get(instrument.name) or pieces
            for j in range(2):  # по 2 урока на курс
                piece = matching_pieces[(i + j) % len(matching_pieces)]
                date = now + timedelta(days=(j * 7) - 14 + i)
                if not Lesson.objects.filter(assignment=assignment, date=date).exists():
                    Lesson.objects.create(
                        assignment=assignment,
                        student=assignment.student,
                        date=date,
                        instrument=instrument,
                        piece=piece,
                        homework="Повторить произведение в медленном темпе, отработать сложные места",
                        comment="Хороший прогресс, продолжаем в том же темпе" if j == 0 else "",
                    )
                    lessons_created += 1
        self.stdout.write(f"  ✅ Уроков: {lessons_created}")

        # ---------- Исполнения ----------

        performances_created = 0
        for i, (assignment, instrument) in enumerate(assignments):
            matching_pieces = pieces_by_instrument.get(instrument.name) or pieces
            piece = matching_pieces[i % len(matching_pieces)]
            performance, created = Performance.objects.get_or_create(
                assignment=assignment, piece=piece, defaults={"score": 6 + (i % 5)}
            )
            if created:
                performances_created += 1
                if i % 3 == 0:
                    PerformanceComment.objects.create(
                        performance=performance,
                        teacher=assignment.teacher,
                        text="Хорошая динамика, поработай над темпом во второй части.",
                    )
        self.stdout.write(f"  ✅ Исполнений: {performances_created}")

        # ---------- Избранное (немного, для полноты) ----------

        favorites_created = 0
        for i, student in enumerate(student_profiles[:10]):
            piece = pieces[i % len(pieces)]
            _, created = Favorite.objects.get_or_create(user=student.user, piece=piece)
            if created:
                favorites_created += 1
        self.stdout.write(f"  ✅ Избранного добавлено: {favorites_created}")

        # ---------- Итог ----------

        self.stdout.write(self.style.SUCCESS("\n✅ База данных полностью заполнена!\n"))
        self.stdout.write(f"Пароль у всех аккаунтов из этой команды: {DEMO_PASSWORD}")
        self.stdout.write("Логин = email в формате имя_латиницей@mail.ru (совпадает с username и email)\n")

        by_role = {}
        for role, login, email in credentials:
            by_role.setdefault(role, []).append((login, email))

        self.stdout.write("Примеры логинов (первые 2 из каждой роли):")
        for role, entries in by_role.items():
            for login, email in entries[:2]:
                self.stdout.write(f"  {role}: {login}  ({email})")
            self.stdout.write(f"  ... всего «{role}»: {len(entries)}")

        self.stdout.write(f"\nВсего аккаунтов создано/проверено: {len(credentials)}")

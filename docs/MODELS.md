  Модель                         Что она описывает?
User	                     Учётную запись человека
TeacherProfile	             Педагога
StudentProfile               Ученика
Subject                      Учебную дисциплину
TeachingAssignment           Факт обучения ученика у конкретного педагога по конкретному предмету
MusicPiece	                 Музыкальное произведение
MusicMaterial	             Материал к произведению
Performance	                 Конкретное исполнение произведения
PerformanceComment           Комментарий к исполнению
Article                      Статью



Модели:


📌 Карточка модели №1 — User

1. User (AbstractUser)

Назначение: учетная запись пользователя.

| Поле           | Тип           | Назначение                   |
| -------------- | ------------- | ---------------------------- |
| username       | CharField     | Логин                        |
| email          | EmailField    | Авторизация                  |
| password       | PasswordField | Пароль                       |
| first_name     | CharField     | Имя                          |
| last_name      | CharField     | Фамилия                      |
| email_verified | BooleanField  | Подтверждение e-mail         |
| is_approved    | BooleanField  | Подтверждение администрацией |
| is_active      | BooleanField  | Активность аккаунта          |
| date_joined    | DateTimeField | Дата регистрации             |


Назначение

Представляет учетную запись пользователя, которая используется для входа в систему.

Это базовая модель, от которой начинается работа всех остальных ролей.

Почему отдельная модель?

Потому что авторизация — самостоятельная задача.

Аккаунт пользователя существует независимо от того, является он педагогом, учеником или обычным пользователем.

Почему не поле?

Потому что все пользователи должны иметь одинаковый механизм входа.

Если хранить email и пароль отдельно в моделях "Педагог" и "Ученик", получится дублирование кода и невозможность использовать встроенную систему авторизации Django.

Кто использует
Педагог
Ученик
Обычный пользователь
Администратор
Связи
User
 │
 ├── TeacherProfile (OneToOne)
 ├── StudentProfile (OneToOne)
 ├── UserStudentAccess (OneToMany)
 ├── Comment (OneToMany)
 └── Article (OneToMany, автор статьи)
Что будет, если удалить?
Перестанет работать вся система авторизации.






📌 Карточка модели №2 — TeacherProfile

2. TeacherProfile

Назначение: профиль педагога.

Поле	Тип	Обязательное
user	OneToOne(User)	✅
middle_name	CharField	❌
photo	ImageField	❌
biography	TextField	❌
education	TextField	❌
experience_years	PositiveSmallIntegerField	❌
website	URLField	❌
vk_url	URLField	❌
telegram	CharField	❌
subjects	ManyToMany(Subject)	❌
is_verified	BooleanField	✅
is_public	BooleanField	✅
created_at	DateTimeField	✅
updated_at	DateTimeField	✅


Назначение

Хранит профессиональную информацию о педагоге.

Почему отдельная модель?

Педагог — это роль пользователя.

Не каждый пользователь является педагогом.

Почему не поле User?

Большинство пользователей не имеют:

стажа;
образования;
предмета преподавания.

Эти поля будут пустыми.

Кто использует

Только педагог.

Связи
TeacherProfile

↓

User (OneToOne)

↓

Performance (OneToMany)
Что будет, если удалить?

Нельзя будет определить преподавателя произведения и исполнений.


📌 Карточка модели №3 — StudentProfile

3. StudentProfile

Назначение: профиль ученика.

Поле	Тип	Обязательное
user	OneToOne(User)	✅
middle_name	CharField	❌
photo	ImageField	❌
birth_date	DateField	❌
biography	TextField	❌
school	CharField	❌
city	CharField	❌
is_public	BooleanField	✅
created_at	DateTimeField	✅
updated_at	DateTimeField	✅

Примечание: возраст будем вычислять автоматически по birth_date, а не хранить отдельным полем.

Назначение

Хранит сведения об ученике.

Почему отдельная модель?

У ученика совершенно другой набор данных, чем у педагога.

Почему не поле User?

Поля:

класс;
дата рождения;
музыкальная школа

не нужны большинству пользователей.

Кто использует

Ученик.

Связи
StudentProfile

↓

User (OneToOne)

↓

Performance (OneToMany)

↓

UserStudentAccess (OneToMany)
Что будет, если удалить?

Исчезнет карточка ученика.


4. Subject

Назначение: учебная дисциплина.

Поле	Тип
name	CharField (unique)
slug	SlugField
description	TextField


📌 Карточка модели №4 — UserStudentAccess


Назначение

Определяет, какие пользователи имеют доступ к странице ученика.

Почему отдельная модель?

Одному ученику можно предоставить доступ нескольким людям.

Одному пользователю может быть предоставлен доступ к нескольким ученикам.

Это связь многие ко многим, но с дополнительными данными (например, уровнем доступа).

Почему не поле?

Поле может хранить только одно значение.

Например:

родитель = User

Но тогда нельзя добавить второго родителя.

Кто использует
родители;
родственники;
концертмейстеры;
сопровождающие.
Связи
User

↓

UserStudentAccess

↓

StudentProfile
Что будет, если удалить?

Ученики не смогут делиться своими страницами с другими пользователями.

📌 Карточка модели №5 — Category

5. Category

Назначение: категория произведений.

Поле	Тип
name	CharField (unique)
slug	SlugField
description	TextField

Назначение

Объединяет произведения по тематике.

Почему отдельная модель?

Одна категория содержит много произведений.

Почему не CharField?

Если хранить текстом:

Новогодние

новогодние

Новый год

Зимние

появятся дубликаты и ошибки.

Кто использует

Все пользователи.

Связи
Category

↓

Work
Что будет, если удалить?

Поиск и группировка произведений станут неудобными.

📌 Карточка модели №6 — MusicPiece

6. MusicPiece ⭐

Назначение: музыкальное произведение.

Поле	Тип	Обязательное
title	CharField	✅
slug	SlugField	✅
composer	CharField	✅
lyricist	CharField	❌
description	TextField	❌
categories	ManyToMany(Category)	❌
difficulty	PositiveSmallIntegerField	❌
duration	DurationField	❌
is_public	BooleanField	✅
created_at	DateTimeField	✅
updated_at	DateTimeField	✅
Почему difficulty?

Например:

1 — очень легко
2 — легко
3 — средне
4 — сложно
5 — очень сложно

Педагог сможет подбирать произведения по уровню подготовки.

Назначение

Хранит музыкальное произведение.

Почему отдельная модель?

Одно произведение исполняют многие ученики.

Почему не поле Student?

Иначе одна и та же песня будет храниться десятки раз.

Кто использует

Все пользователи сайта.

Связи
Category

↓

MusicPiece

↓

Material

↓

Performance
Что будет, если удалить?

Исчезнет вся библиотека произведений.

📌 Карточка модели №7 — Material

7. MusicMaterial ⭐

Назначение: материалы произведения.

Поле	Тип
music_piece	ForeignKey(MusicPiece)
material_type	ChoiceField
title	CharField
file	FileField
description	TextField
is_public	BooleanField
uploaded_at	DateTimeField

Тип материала
Ноты
Минусовка
Плюсовка
Видео
Текст
Другое

Назначение

Хранит материалы, относящиеся к произведению.

Может содержать
ноты;
плюсовку;
минусовку;
видео;
текст;
PDF.
Почему отдельная модель?

У одного произведения может быть несколько материалов каждого типа.

Например:

две минусовки в разных тональностях;
несколько вариантов нот;
разные видео.

Если хранить их полями в Work, структура быстро станет неудобной.

Кто использует

Педагоги и ученики.

Связи
Work

↓

Material
Что будет, если удалить?

Произведения останутся без файлов.



8. TeachingAssignment ⭐⭐⭐

Назначение: связь "педагог — ученик — предмет".

Поле	Тип
teacher	ForeignKey(TeacherProfile)
student	ForeignKey(StudentProfile)
subject	ForeignKey(Subject)
start_date	DateField
end_date	DateField
is_active	BooleanField
notes	TextField




📌 Карточка модели №8 — Performance ⭐

9. Performance ⭐⭐⭐⭐⭐

Назначение: исполнение произведения учеником.

Поле	Тип
teaching_assignment	ForeignKey(TeachingAssignment)
music_piece	ForeignKey(MusicPiece)
grade	PositiveSmallIntegerField
teacher_comment	TextField
student_comment	TextField
performance_video	FileField
performance_date	DateField
status	ChoiceField
created_at	DateTimeField
updated_at	DateTimeField
Статусы
Назначено

В работе

Готово

Исполнено

Архив

Назначение

Описывает факт исполнения произведения конкретным учеником.

Почему отдельная модель?

Она хранит информацию не о произведении, а о самом исполнении.

Исполнение имеет собственные данные:

оценку;
комментарий;
видео;
дату;
статус.
Почему не поле Work?

Потому что одну песню могут исполнять десятки учеников.

Почему не поле Student?

Потому что один ученик исполняет множество произведений.

Кто использует

Педагог.

Ученик.

Родители.

Связи
TeacherProfile

↓

Performance

↑

StudentProfile

↑

Work
Что будет, если удалить?

Исчезнет электронный журнал.

📌 Карточка модели №9 — Comment

10. PerformanceComment

Назначение: комментарии пользователей.

Поле	Тип
performance	ForeignKey(Performance)
author	ForeignKey(User)
text	TextField
created_at	DateTimeField


Назначение

Позволяет пользователям обсуждать исполнения.

Почему отдельная модель?

Комментариев может быть любое количество.

Почему не TextField?

Поле хранит только один текст.

Нельзя сохранить:

автора;
дату;
несколько комментариев.
Кто использует

Зарегистрированные пользователи.

Связи
User

↓

Comment

↓

Performance

Я предлагаю привязывать комментарии именно к Performance, а не к Work. Тогда комментарий будет относиться к конкретному исполнению ученика, а не к произведению вообще. Например: «Очень выразительно спел на отчетном концерте!» — это относится к исполнению, а не к песне «Катюша» в целом.

Что будет, если удалить?

Пользователи потеряют возможность оставлять отзывы.

📌 Карточка модели №10 — Article

11. Article

Назначение: статьи и полезные материалы.

Поле	Тип
author	ForeignKey(User)
title	CharField
slug	SlugField
preview	ImageField
content	TextField
is_published	BooleanField
created_at	DateTimeField
updated_at	DateTimeField

Назначение

Хранит информационные материалы сайта.

Почему отдельная модель?

Статьи являются самостоятельной частью сайта и не связаны с учебным процессом.

Почему не HTML-файл?

Информация должна редактироваться через админ-панель.

Кто использует

Все посетители сайта.

Связи
User (автор)

↓

Article
Что будет, если удалить?

На главной странице останется только каталог произведений без новостей и полезных материалов.

📋 Итоговая классификация моделей
Модель	Тип	Обязательна
User	Основная	✅
TeacherProfile	Профиль	✅
StudentProfile	Профиль	✅
UserStudentAccess	Связующая	✅
Category	Справочник	✅
Work	Основная	✅
Material	Основная	✅
Performance	Связующая (с данными)	✅
Comment	Основная	✅
Article	Информационная	✅
Одно небольшое предложение перед тем, как мы начнем проектировать поля

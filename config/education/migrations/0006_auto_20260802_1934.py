from django.db import migrations

def transfer_teacher_to_assignment(apps, schema_editor):
    StudentProfile = apps.get_model("education", "StudentProfile")
    TeacherProfile = apps.get_model("education", "TeacherProfile")
    TeachingAssignment = apps.get_model("education", "TeachingAssignment")
    Subject = apps.get_model("education", "Subject")

    # выбираем предмет по умолчанию
    subject = Subject.objects.first()

    if subject is None:
        return  # если предметов нет — пропускаем

    for student in StudentProfile.objects.all():
        if student.teacher:
            TeachingAssignment.objects.create(
                teacher=student.teacher,
                student=student,
                subject=subject,
                is_active=True
            )

class Migration(migrations.Migration):

    dependencies = [
        ('education', '0005_subject_alter_lesson_options_teachingassignment'),
    ]

    operations = [
        migrations.RunPython(transfer_teacher_to_assignment),
    ]

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0014_alter_teachingassignment_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ParentLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_approved', models.BooleanField(default=False, verbose_name='Подтверждено')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Запрошено')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parent_links', to=settings.AUTH_USER_MODEL, verbose_name='Родитель')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parent_links', to='education.studentprofile', verbose_name='Ученик')),
            ],
            options={
                'verbose_name': 'Связь родитель-ученик',
                'verbose_name_plural': 'Связи родитель-ученик',
                'ordering': ['-created_at'],
                'unique_together': {('parent', 'student')},
            },
        ),
    ]

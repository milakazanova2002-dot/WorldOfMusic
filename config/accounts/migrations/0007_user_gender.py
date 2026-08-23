from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_user_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('male', 'Мужской'), ('female', 'Женский')],
                help_text='Используется для подбора аватара по умолчанию',
                max_length=10,
                verbose_name='Пол',
            ),
        ),
    ]

# Generated by Django 5.2.1 on 2025-05-26 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0007_alter_typeproduct_image_alter_userinfo_avatar_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('questions', models.CharField(blank=True, max_length=200, verbose_name='Вопрос')),
                ('answer', models.CharField(blank=True, max_length=200, verbose_name='Ответ')),
            ],
        ),
    ]

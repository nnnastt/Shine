# Generated by Django 5.2.1 on 2025-05-28 21:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0017_alter_viewproduct_discount'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='infoproduct',
            options={'verbose_name': 'Информация о товаре', 'verbose_name_plural': 'Информация о товаре'},
        ),
        migrations.AlterModelOptions(
            name='viewproduct',
            options={'ordering': ['-created_at'], 'verbose_name': 'Все товары', 'verbose_name_plural': 'Все товары'},
        ),
    ]

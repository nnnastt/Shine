# Generated by Django 5.2.1 on 2025-06-03 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0023_remove_infoproduct_material_remove_infoproduct_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productdetail',
            name='title',
            field=models.CharField(default='Состав и характеристики', max_length=100),
        ),
    ]

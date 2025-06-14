# Generated by Django 5.2.1 on 2025-06-07 15:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0025_alter_typeproduct_image_alter_userinfo_avatar_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='infoproduct',
            name='view_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detailed_info', to='webapp.viewproduct', verbose_name='Товар'),
        ),
        migrations.AlterField(
            model_name='orderconfirmation',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confirmation', to='webapp.order'),
        ),
    ]

# Generated by Django 3.1.2 on 2020-10-30 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_auto_20201030_1512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='students',
            name='sid',
            field=models.PositiveIntegerField(unique=True),
        ),
    ]

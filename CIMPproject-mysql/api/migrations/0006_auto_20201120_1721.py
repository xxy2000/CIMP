# Generated by Django 3.1.2 on 2020-11-20 09:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20201120_1715'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='likes',
            index_together={('user', 'paper')},
        ),
    ]
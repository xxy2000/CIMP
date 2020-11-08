# Generated by Django 3.1.2 on 2020-10-30 07:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_workstep_operator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workstep',
            name='operator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
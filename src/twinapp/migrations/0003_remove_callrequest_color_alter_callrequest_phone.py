# Generated by Django 5.1.8 on 2025-04-18 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twinapp', '0002_remove_callrequest_twin_call_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='callrequest',
            name='color',
        ),
        migrations.AlterField(
            model_name='callrequest',
            name='phone',
            field=models.CharField(),
        ),
    ]

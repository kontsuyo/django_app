# Generated by Django 3.2.15 on 2022-09-06 03:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sns', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='tittle',
            new_name='title',
        ),
    ]

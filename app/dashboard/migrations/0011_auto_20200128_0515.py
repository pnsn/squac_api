# Generated by Django 2.2.9 on 2020-01-28 05:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_auto_20191211_2226'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboard',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='widget',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
    ]

# Generated by Django 2.2.16 on 2020-10-07 21:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0023_auto_20201007_2119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alarmthreshold',
            name='level',
            field=models.IntegerField(default=1),
        ),
    ]

# Generated by Django 2.2.2 on 2019-07-08 21:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('measurement', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Threshold',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(blank=True, default='', max_length=255)),
                ('min', models.FloatField()),
                ('max', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('metricgroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='thresholds', to='measurement.MetricGroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

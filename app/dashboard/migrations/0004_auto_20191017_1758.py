# Generated by Django 2.2.6 on 2019-10-17 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_widget_stattype'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='dashboard',
            index=models.Index(fields=['name'], name='dashboard_d_name_8857a6_idx'),
        ),
        migrations.AddIndex(
            model_name='stattype',
            index=models.Index(fields=['type'], name='dashboard_s_type_b3db9e_idx'),
        ),
        migrations.AddIndex(
            model_name='widget',
            index=models.Index(fields=['name'], name='dashboard_w_name_ad651e_idx'),
        ),
        migrations.AddIndex(
            model_name='widgettype',
            index=models.Index(fields=['type'], name='dashboard_w_type_e4d375_idx'),
        ),
    ]

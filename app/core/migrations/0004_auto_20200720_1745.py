# Generated by Django 2.2.12 on 2020-07-20 17:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
        ('core', '0003_remove_user_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_org_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization', to='organization.Organization'),
            preserve_default=False,
        ),
    ]

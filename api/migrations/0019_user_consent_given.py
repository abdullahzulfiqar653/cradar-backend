# Generated by Django 4.2.3 on 2024-02-27 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_alter_user_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='consent_given',
            field=models.BooleanField(default=False),
        ),
    ]
# Generated by Django 4.2.3 on 2024-02-16 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_note_file_size_note_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='skip_tutorial',
            field=models.BooleanField(default=False),
        ),
    ]
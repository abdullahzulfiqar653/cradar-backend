# Generated by Django 4.2.3 on 2024-03-20 03:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_usersavedtakeaway_user_saved_takeaways'),
    ]

    operations = [
        migrations.AddField(
            model_name='notequestion',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notequestion',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='note_questions', to=settings.AUTH_USER_MODEL),
        ),
    ]

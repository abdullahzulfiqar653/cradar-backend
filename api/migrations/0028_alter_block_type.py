# Generated by Django 4.2.3 on 2024-04-18 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0027_theme'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='type',
            field=models.CharField(choices=[('Text', 'Text'), ('Takeaways', 'Takeaways'), ('Themes', 'Themes')], max_length=9),
        ),
    ]

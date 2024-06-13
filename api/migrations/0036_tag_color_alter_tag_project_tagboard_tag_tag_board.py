# Generated by Django 4.2.3 on 2024-06-13 01:43

from django.db import migrations, models
import django.db.models.deletion
import shortuuid.django_fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0035_alter_notetype_project_alter_takeawaytype_project_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='color',
            field=models.CharField(blank=True, max_length=7),
        ),
        migrations.AlterField(
            model_name='tag',
            name='project',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='api.project'),
        ),
        migrations.CreateModel(
            name='TagBoard',
            fields=[
                ('id', shortuuid.django_fields.ShortUUIDField(alphabet=None, editable=False, length=12, max_length=12, prefix='', primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('color', models.CharField(blank=True, max_length=7)),
                ('project', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='tag_boards', to='api.project')),
            ],
            options={
                'unique_together': {('name', 'project')},
            },
        ),
        migrations.AddField(
            model_name='tag',
            name='tag_board',
            field=models.ManyToManyField(related_name='tags', to='api.tagboard'),
        ),
    ]

# Generated by Django 4.2.3 on 2024-04-18 08:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0029_migrate_to_lexical"),
    ]

    operations = [
        # Reference: https://docs.djangoproject.com/en/4.2/howto/writing-migrations/#changing-a-manytomanyfield-to-use-a-through-model
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE api_workspace_members RENAME TO api_workspaceuser;",
                    reverse_sql="ALTER TABLE api_workspaceuser RENAME TO api_workspace_members;",
                )
            ],
            state_operations=[
                migrations.CreateModel(
                    name="WorkspaceUser",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "user",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="workspace_users",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        (
                            "workspace",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="workspace_users",
                                to="api.workspace",
                            ),
                        ),
                    ],
                    options={
                        "unique_together": {("workspace", "user")},
                    },
                ),
                migrations.AlterField(
                    model_name="workspace",
                    name="members",
                    field=models.ManyToManyField(
                        related_name="workspaces",
                        through="api.WorkspaceUser",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="workspaceuser",
            name="role",
            field=models.CharField(
                choices=[("Editor", "Editor"), ("Viewer", "Viewer")],
                default="Editor",
                max_length=6,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="workspaceuser",
            name="role",
            field=models.CharField(
                choices=[("Editor", "Editor"), ("Viewer", "Viewer")],
                default="Viewer",
                max_length=6,
            ),
        ),
    ]
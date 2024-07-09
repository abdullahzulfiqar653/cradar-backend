# Generated by Django 4.2.3 on 2024-07-02 08:09

import django.contrib.postgres.indexes
import django.db.models.deletion
import pgvector.django
import shortuuid.django_fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0044_add_mixpanel_users"),
    ]

    operations = [
        migrations.CreateModel(
            name="Message",
            fields=[
                (
                    "order",
                    models.PositiveIntegerField(
                        db_index=True, editable=False, verbose_name="order"
                    ),
                ),
                (
                    "id",
                    shortuuid.django_fields.ShortUUIDField(
                        alphabet=None,
                        editable=False,
                        length=12,
                        max_length=12,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("system", "System"),
                            ("human", "Human"),
                            ("ai", "Ai"),
                        ],
                        editable=False,
                        max_length=6,
                    ),
                ),
                ("text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "note",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="api.note",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["user", "order"],
            },
        ),
        migrations.CreateModel(
            name="Chunk",
            fields=[
                (
                    "id",
                    shortuuid.django_fields.ShortUUIDField(
                        alphabet=None,
                        editable=False,
                        length=12,
                        max_length=12,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("text", models.TextField()),
                ("vector", pgvector.django.VectorField(dimensions=1536)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "note",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="api.note",
                    ),
                ),
            ],
            options={
                "indexes": [
                    django.contrib.postgres.indexes.HashIndex(
                        fields=["text"], name="api_chunk_text_b74cf5_hash"
                    ),
                    pgvector.django.HnswIndex(
                        fields=["vector"],
                        name="chunk-vector-index",
                        opclasses=["vector_ip_ops"],
                    ),
                ],
            },
        ),
    ]
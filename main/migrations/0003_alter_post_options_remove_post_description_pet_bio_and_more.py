# Generated by Django 5.0.2 on 2025-04-15 20:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_alter_post_options_remove_post_pet_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="post",
            options={"ordering": ["-created_at"]},
        ),
        migrations.RemoveField(
            model_name="post",
            name="description",
        ),
        migrations.AddField(
            model_name="pet",
            name="bio",
            field=models.TextField(blank=True, verbose_name="О питомце"),
        ),
        migrations.AddField(
            model_name="post",
            name="content",
            field=models.TextField(default="", verbose_name="Содержание"),
        ),
        migrations.AddField(
            model_name="post",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="posts/", verbose_name="Изображение"),
        ),
        migrations.AddField(
            model_name="post",
            name="likes",
            field=models.ManyToManyField(blank=True, related_name="liked_posts", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="post",
            name="pet",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="posts",
                to="main.pet",
                verbose_name="Питомец",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="bio",
            field=models.TextField(blank=True, verbose_name="О себе"),
        ),
        migrations.CreateModel(
            name="Comment",
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
                ("content", models.TextField(verbose_name="Комментарий")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Дата создания"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="main.post",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]

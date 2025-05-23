# Generated by Django 5.0.2 on 2025-05-06 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0025_review"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="composition",
            field=models.TextField(default="Не указано", verbose_name="Состав продукта"),
        ),
        migrations.AddField(
            model_name="product",
            name="weight",
            field=models.CharField(
                default="Не указано",
                help_text="Например: 2 кг, 500 г",
                max_length=50,
                verbose_name="Вес упаковки",
            ),
        ),
    ]

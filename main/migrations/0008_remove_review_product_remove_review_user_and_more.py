# Generated by Django 5.0.2 on 2025-04-26 17:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0007_product_added_by"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="review",
            name="product",
        ),
        migrations.RemoveField(
            model_name="review",
            name="user",
        ),
        migrations.RemoveField(
            model_name="wishlist",
            name="products",
        ),
        migrations.RemoveField(
            model_name="wishlist",
            name="user",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="is_on_sale",
            new_name="is_bestseller",
        ),
        migrations.RemoveField(
            model_name="product",
            name="added_by",
        ),
        migrations.AddField(
            model_name="cart",
            name="session_key",
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="is_new",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="cart",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="cartitem",
            name="cart",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="main.cart"),
        ),
        migrations.AlterField(
            model_name="product",
            name="stock",
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.DeleteModel(
            name="ProductImage",
        ),
        migrations.DeleteModel(
            name="Review",
        ),
        migrations.DeleteModel(
            name="Wishlist",
        ),
    ]

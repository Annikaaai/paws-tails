"""admin"""

from django.contrib import admin
from .models import AnimalListing, AnimalImage


class AnimalImageInline(admin.TabularInline):
    """class AnimalImageInline"""

    model = AnimalImage
    extra = 1


@admin.register(AnimalListing)
class AnimalListingAdmin(admin.ModelAdmin):
    """class AnimalListingAdmin"""

    list_display = (
        "title",
        "category",
        "price",
        "location",
        "seller",
        "created_at",
        "is_active",
    )
    list_filter = ("category", "animal_type", "is_active")
    search_fields = ("title", "description")
    inlines = [AnimalImageInline]


admin.site.register(AnimalImage)

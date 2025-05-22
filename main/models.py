"""Models for the pet service application."""

import os

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.urls import reverse

User = get_user_model()

User.add_to_class(
    "get_profile",
    property(lambda u: Profile.objects.get_or_create(user=u, defaults={"avatar_number": 1})[0]),
)


class Profile(models.Model):
    """Profile model representing user profile data."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    followers = models.ManyToManyField(User, related_name="following", blank=True)
    avatar_number = models.PositiveSmallIntegerField(default=1)
    bio = models.TextField("О себе", blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    def get_avatar_url(self):
        """Get the URL of the user's avatar."""
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return f"/static/images/avatars/default{self.avatar_number}.jpg"

    def followers_count(self):
        """Get the number of followers."""
        return self.followers.count()

    def following_count(self):
        """Get the number of users being followed."""
        return self.user.following.count()

    def __str__(self):
        """__str__

        Returns:
            str: The username of the associated user.
        """
        return self.user.username


class UserFollow(models.Model):
    """UserFollow model representing follow relationships."""

    follower = models.ForeignKey(User, related_name="follows", on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the follow relationship.
        """
        return f"{self.follower.username} follows {self.following.username}"


class Pet(models.Model):
    """Pet model representing pet information."""

    SPECIES_CHOICES = [
        ("dog", "Собака"),
        ("cat", "Кошка"),
        ("bird", "Птица"),
        ("other", "Другое"),
    ]

    name = models.CharField("Кличка", max_length=100)
    species = models.CharField("Вид животного", max_length=20, choices=SPECIES_CHOICES)
    breed = models.CharField("Порода", max_length=100, blank=True)
    age = models.PositiveIntegerField("Возраст", null=True, blank=True)
    photo = models.ImageField("Фотография", upload_to="pets/", null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)
    bio = models.TextField("О питомце", blank=True, default="")

    class Meta:
        verbose_name = "Питомец"
        verbose_name_plural = "Питомцы"
        ordering = ["-created_at"]

    def __str__(self):
        """__str__

        Returns:
            str: The pet's name and species.
        """
        return f"{self.name} ({self.get_species_display()})"

    def get_species_display(self):
        """Get the display name of the species."""
        # Placeholder for species display logic
        return self.species


class Post(models.Model):
    """Post model representing user posts."""

    title = models.CharField("Заголовок", max_length=200)
    content = models.TextField("Содержание", default="")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    pet = models.ForeignKey(
        Pet,
        on_delete=models.SET_NULL,
        verbose_name="Питомец",
        related_name="posts",
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """__str__

        Returns:
            str: The title of the post.
        """
        return self.title

    def like_count(self):
        """Get the number of likes on the post."""
        return self.likes.count()


@receiver(post_delete, sender=Post)
def auto_delete_file_on_delete(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Delete the image file when a Post is deleted."""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


class Comment(models.Model):
    """Comment model representing comments on posts."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField("Комментарий")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the comment.
        """
        return f'Комментарий от {self.author.username} к "{self.post.title}"'


class Chat(models.Model):
    """Chat model representing chat conversations."""

    participants = models.ManyToManyField(User, related_name="chats")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the chat.
        """
        return f"Chat {self.id}"

    def get_last_message(self):
        """Get the most recent message in the chat."""
        return self.messages.order_by("-timestamp").first()

    def get_unread_count(self, user):
        """Get the number of unread messages for a user, considering deletion status."""
        if self.is_deleted:
            return self.messages.exclude(sender=user).filter(read=False, is_deleted=False).count()
        return self.messages.exclude(sender=user).filter(read=False).count()

    def soft_delete(self):
        """Soft delete the chat by marking it as deleted."""
        self.is_deleted = True
        self.save()


class Message(models.Model):
    """Message model representing messages in a chat."""

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to="chat_images/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        """__str__

        Returns:
            str: A truncated string representation of the message.
        """
        return f"{self.sender.username}: {self.content[:20]}..."

    def soft_delete(self):
        """Soft delete the message by marking it as deleted."""
        self.is_deleted = True
        self.save()

    def edit_message(self, new_content):
        """Edit the message content."""
        self.content = new_content
        self.edited = True
        self.save()


class Product(models.Model):
    """Product model representing pet products."""

    PET_TYPE_CHOICES = [
        ("cat", "Для кошек"),
        ("dog", "Для собак"),
        ("kitten", "Для котят"),
        ("puppy", "Для щенков"),
    ]

    FOOD_TYPE_CHOICES = [
        ("dry", "Сухой корм"),
        ("wet", "Влажный корм"),
        ("premium", "Премиум"),
        ("holistic", "Холистик"),
    ]

    pet_type = models.CharField(max_length=20, choices=PET_TYPE_CHOICES, default="cat")

    food_type = models.CharField(max_length=20, choices=FOOD_TYPE_CHOICES, default="dry")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to="products/")
    rating = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], default=0.0)
    weight = models.CharField(
        max_length=50,
        verbose_name="Вес упаковки",
        help_text="Например: 2 кг, 500 г",
        default="Не указано",
    )
    composition = models.TextField(verbose_name="Состав продукта", default="Не указано")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stock = models.PositiveIntegerField(default=10)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец", related_name="products")

    def __str__(self):
        """__str__

        Returns:
            str: The name of the product.
        """
        return self.name

    def save(self, *args, **kwargs):
        """Save the product instance with stock validation."""
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative")
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        """Calculate the average rating from all reviews."""
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return 0

    def update_rating(self):
        """Update the product rating based on reviews."""
        self.rating = self.average_rating
        self.save()


class Cart(models.Model):
    """Cart model representing a user's shopping cart."""

    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        """Calculate the total price of items in the cart."""
        return sum(item.get_total_price() for item in self.cartitem_set.all())

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the cart.
        """
        return f"Cart for {self.user.username if self.user else 'Anonymous'}"


class CartItem(models.Model):
    """CartItem model representing items in a cart."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        """Calculate the total price of the cart item."""
        return self.product.price * self.quantity

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the cart item.
        """
        return f"{self.quantity} x {self.product.name} in cart"


class Order(models.Model):
    """Order model representing a user's order."""

    STATUS_CHOICES = [
        ("new", "Новый"),
        ("processing", "В обработке"),
        ("shipped", "Отправлен"),
        ("delivered", "Доставлен"),
        ("cancelled", "Отменен"),
    ]

    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    payment_method = models.CharField(max_length=50)
    delivery_method = models.CharField(max_length=50)

    notes = models.TextField(blank=True)

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the order.
        """
        return f"Заказ #{self.id} - {self.get_status_display()}"

    def get_status_display(self):
        """Get the display name of the order status."""
        # Placeholder for status display logic
        return self.status


class OrderItem(models.Model):
    """OrderItem model representing items in an order."""

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        """Calculate the total price of the order item."""
        return self.price * self.quantity

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the order item.
        """
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"


class Favorite(models.Model):
    """Favorite model representing user favorite products."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные товары"

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the favorite item.
        """
        return f"{self.user.username} - {self.product.name}"


class AnimalListing(models.Model):
    """AnimalListing model representing animals for sale or adoption."""

    CATEGORY_CHOICES = [
        ("dogs", "Собаки"),
        ("cats", "Кошки"),
        ("birds", "Птицы"),
        ("rodents", "Грызуны"),
        ("reptiles", "Рептилии"),
        ("other", "Другие"),
    ]

    breed = models.CharField(max_length=100, verbose_name="Порода", blank=True, null=True)

    GENDER_CHOICES = [
        ("M", "Самец"),
        ("F", "Самка"),
    ]

    AGE_GROUP_CHOICES = [
        ("baby", "Детеныш (до 6 мес)"),
        ("young", "Молодой (6 мес - 2 года)"),
        ("adult", "Взрослый (2+ года)"),
    ]

    TYPE_CHOICES = [
        ("pedigree", "Породистый"),
        ("regular", "Обычный"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_free = models.BooleanField(default=False)
    age = models.PositiveIntegerField(help_text="Возраст в месяцах")
    age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES, verbose_name="Возрастная группа")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    animal_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    location = models.CharField(max_length=100)
    main_image = models.ImageField(upload_to="animal_listings/")
    additional_images = models.ManyToManyField("AnimalImage", blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """__str__

        Returns:
            str: The title of the animal listing.
        """
        return self.title

    def get_breed_display(self):
        """Get the display name of the breed."""
        return self.breed if self.breed else "Не указана"

    def get_absolute_url(self):
        """Get the absolute URL for the animal listing detail view."""
        return reverse("animal_detail", kwargs={"pk": self.pk})

    def get_age_display(self):
        """Get the formatted age display."""
        if self.age < 12:
            return f"{self.age} мес"
        years = self.age // 12
        months = self.age % 12
        if months == 0:
            return f"{years} г"
        return f"{years} г {months} мес"


class AnimalImage(models.Model):
    """AnimalImage model representing additional images for animal listings."""

    image = models.ImageField(upload_to="animal_listings/")
    listing = models.ForeignKey(AnimalListing, on_delete=models.CASCADE, related_name="images")

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the animal image.
        """
        return f"Image for {self.listing.title}"


class LikesMarket(models.Model):
    """LikesMarket model representing likes on animal listings."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="liked_animals_pet_market")
    animal = models.ForeignKey(AnimalListing, on_delete=models.CASCADE, related_name="likes_pet_market")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "animal")
        verbose_name = "Лайк животного"
        verbose_name_plural = "Лайки животных"

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the like.
        """
        return f"{self.user.username} лайкнул {self.animal.title}"


class Review(models.Model):
    """Review model representing user reviews for products."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5",
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["product", "user"]

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the review.
        """
        return f"Review for {self.product.name} by {self.user.username}"


class MedicalRecord(models.Model):
    """MedicalRecord model representing pet medical records."""

    pet = models.ForeignKey("Pet", on_delete=models.CASCADE, related_name="medical_records")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="medical_records/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the medical record.
        """
        return f"{self.title} - {self.pet.name}"


class Document(models.Model):
    """Document model representing pet documents."""

    pet = models.ForeignKey("Pet", on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="pet_documents/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the document.
        """
        return f"{self.title} - {self.pet.name}"


class Pedigree(models.Model):
    """Pedigree model representing pet pedigrees."""

    pet = models.OneToOneField(Pet, on_delete=models.CASCADE, related_name="pedigree")
    registration_number = models.CharField("Регистрационный номер", max_length=50, blank=True)
    color = models.CharField("Окрас", max_length=100, blank=True)
    breeder = models.CharField("Заводчик", max_length=200, blank=True)
    date_of_birth = models.DateField("Дата рождения", null=True, blank=True)
    is_confirmed = models.BooleanField("Подтверждена", default=False)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the pedigree.
        """
        return f"Родословная {self.pet.name}"


class Ancestor(models.Model):
    """Ancestor model representing pedigree ancestors."""

    pedigree = models.ForeignKey(Pedigree, on_delete=models.CASCADE, related_name="ancestors")
    name = models.CharField("Кличка", max_length=100)
    breed = models.CharField("Порода", max_length=100, blank=True)
    registration_number = models.CharField("Регистрационный номер", max_length=50, blank=True)
    generation = models.PositiveIntegerField("Поколение")
    position = models.PositiveIntegerField("Позиция в поколении")
    is_male = models.BooleanField("Самец", default=True)
    notes = models.TextField("Примечания", blank=True)
    #
    # class Meta:
    #     ordering = ["generation", "position"]
    #     # unique_together = ["pedigree", "generation", "position"]

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the ancestor.
        """
        return f"{self.name} (поколение {self.generation})"


class LostPetReport(models.Model):
    """LostPetReport model representing lost pet reports."""

    STATUS_CHOICES = [
        ("found", "Найден"),
        ("returned", "Возвращен владельцу"),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="lost_reports")
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_lost_pets",
    )
    found_location = models.TextField("Место, где нашли питомца")
    contact_info = models.TextField("Контактная информация", blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="found")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Найденный питомец"
        verbose_name_plural = "Найденные питомцы"
        ordering = ["-created_at"]

    def __str__(self):
        """__str__

        Returns:
            str: A string representation of the lost pet report.
        """
        return f"Найден {self.pet.name} ({self.pet.owner.username})"


class Notification(models.Model):
    """Notification model representing user notifications."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200, default="")
    message = models.TextField()
    related_pet = models.ForeignKey(Pet, on_delete=models.CASCADE, null=True, blank=True)
    related_report = models.ForeignKey(LostPetReport, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True
        self.save()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        """__str__

        Returns:
            str: The title of the notification.
        """
        return self.title

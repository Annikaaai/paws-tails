"""forms"""

from django import forms
from main.models import AnimalListing

# from django.core.files.images import get_image_dimensions
from .models import (
    Post,
    Comment,
    Message,
    Product,
    Pet,
    Profile,
    User,
    Review,
    MedicalRecord,
    Document,
    Pedigree,
    Ancestor,
    LostPetReport,
)


class RegisterUserForm(forms.Form):
    """class RegisterUserForm"""

    username = forms.CharField(
        max_length=32,
        label="Username",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя пользователя"}),
    )
    password = forms.CharField(
        max_length=32,
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"}),
    )


class PostForm(forms.ModelForm):
    """class PostForm"""

    class Meta:
        """class Meta"""

        model = Post
        fields = ["title", "content", "pet", "image"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class CommentForm(forms.ModelForm):
    """class CommentForm"""

    class Meta:
        """class Meta"""

        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class MessageForm(forms.ModelForm):
    """class MessageForm"""

    class Meta:
        """class Meta"""

        model = Message
        fields = ["content", "image"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control message-input",
                    "rows": 1,
                    "placeholder": "Введите сообщение...",
                }
            ),
            "image": forms.FileInput(
                attrs={
                    "id": "imageInput",
                    "style": "display: none;",
                    "accept": "image/*",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class ProductForm(forms.ModelForm):
    """class ProductForm"""

    class Meta:
        """class Meta"""

        model = Product
        exclude = ["rating"]  # Исключаем рейтинг, так как он будет рассчитываться автоматически
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "composition": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        """Устанавливаем обязательные поля"""
        super().__init__(*args, **kwargs)
        self.fields["weight"].required = True
        self.fields["composition"].required = True


class CheckoutForm(forms.Form):
    """class CheckoutForm"""

    PAYMENT_CHOICES = [
        ("card", "Банковская карта"),
        ("cash", "Наличные при получении"),
        ("online", "Онлайн-платеж"),
    ]

    DELIVERY_CHOICES = [
        ("courier", "Курьером"),
        ("pickup", "Самовывоз"),
        ("post", "Почта России"),
    ]

    first_name = forms.CharField(label="Имя", max_length=100, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=100, required=True)
    email = forms.EmailField(label="Email", required=True)
    phone = forms.CharField(label="Телефон", max_length=20, required=True)
    address = forms.CharField(label="Адрес доставки", widget=forms.Textarea(attrs={"rows": 3}), required=True)
    payment_method = forms.ChoiceField(label="Способ оплаты", choices=PAYMENT_CHOICES, widget=forms.RadioSelect)
    delivery_method = forms.ChoiceField(label="Способ доставки", choices=DELIVERY_CHOICES, widget=forms.RadioSelect)
    notes = forms.CharField(
        label="Примечания к заказу",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )


class PetForm(forms.ModelForm):
    """class PetForm"""

    class Meta:
        """class Meta"""

        model = Pet
        fields = ["name", "species", "breed", "age", "photo", "bio"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class ProfileEditForm(forms.ModelForm):
    """class ProfileEditForm"""

    class Meta:
        """class Meta"""

        model = Profile
        fields = ["bio"]
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Расскажите о себе",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class MultipleFileInput(forms.ClearableFileInput):
    """class MultipleFileInput"""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """class MultipleFileField"""

    def __init__(self, *args, **kwargs):
        """__init__"""
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        """clean"""
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class AnimalListingForm(forms.ModelForm):
    """class AnimalListingForm"""

    category = forms.ChoiceField(
        choices=AnimalListing.CATEGORY_CHOICES,
        label="Категория",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    breed = forms.CharField(
        required=False,
        label="Порода",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": 'Например: "Сиамская" или "Метис"',
            }
        ),
    )

    class Meta:
        """class Meta"""

        model = AnimalListing
        fields = [
            "title",
            "category",
            "breed",
            "description",
            "price",
            "is_free",
            "age",
            "gender",
            "animal_type",
            "location",
            "main_image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "age": forms.NumberInput(attrs={"min": 1}),
            "price": forms.NumberInput(attrs={"min": 0}),
        }
        labels = {
            "main_image": "Основное фото",
            "is_free": "Отдать бесплатно",
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class UsernameEditForm(forms.ModelForm):
    """class UsernameEditForm"""

    class Meta:
        """class Meta"""

        model = User
        fields = ["username"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите новый username"}),
        }

    def clean_username(self):
        """clean_username"""
        username = self.cleaned_data["username"]
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError("Этот username уже занят")
        return username


class ReviewForm(forms.ModelForm):
    """class ReviewForm"""

    class Meta:
        """class Meta"""

        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class MedicalRecordForm(forms.ModelForm):
    """class MedicalRecordForm"""

    class Meta:
        """class Meta"""

        model = MedicalRecord
        fields = ["title", "description", "file"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class DocumentForm(forms.ModelForm):
    """class DocumentForm"""

    class Meta:
        """class Meta"""

        model = Document
        fields = ["title", "description", "file"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class PedigreeForm(forms.ModelForm):
    """class PedigreeForm"""

    class Meta:
        """class Meta"""

        model = Pedigree
        fields = ["registration_number", "color", "breeder", "date_of_birth"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class AncestorForm(forms.ModelForm):
    """class AncestorForm"""

    class Meta:
        """class Meta"""

        model = Ancestor
        fields = [
            "name",
            "breed",
            "registration_number",
            "generation",
            "position",
            "is_male",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class AvatarUploadForm(forms.ModelForm):
    """class AvatarUploadForm"""

    class Meta:
        """class Meta"""

        model = Profile
        fields = ["avatar"]
        widgets = {"avatar": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"})}

    def __init__(self, *args, **kwargs):
        """form for additional settings"""
        super().__init__(*args, **kwargs)


class LostPetReportForm(forms.ModelForm):
    """class LostPetReportForm"""

    pet_id = forms.IntegerField(label="ID питомца")
    found_location = forms.CharField(
        label="Где нашли питомца",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Введите точный адрес или ориентиры"}),
    )
    contact_info = forms.CharField(
        label="Ваши контактные данные",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Как с вами связаться (не обязательно)"}),
    )

    class Meta:
        """class Meta"""

        model = LostPetReport
        fields = ["pet_id", "found_location", "contact_info"]

    def clean_pet_id(self):
        """clean_pet_id"""
        pet_id = self.cleaned_data["pet_id"]
        try:
            pass
            # pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist as e:
            raise forms.ValidationError("Питомец с таким ID не найден") from e
        return pet_id

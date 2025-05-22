"""
Django views для функционала профиля пользователя и управления питомцами.
Включает работу с аватарами, профилями питомцев, медицинскими записями, документами и родословными.
"""
from main.forms import *
from main.models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import io
from datetime import datetime


@login_required
def profile_page(request):
    """
    Отображает главную страницу профиля пользователя.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном профиля, содержащим:
        - информацию о пользователе
        - список постов пользователя
        - список питомцев пользователя
        - номер аватарки
    """
    user = get_object_or_404(User, username=request.user)
    profile_user = request.user
    profile = profile_user.get_profile
    posts = Post.objects.filter(owner=user).order_by("-created_at")
    pets = Pet.objects.filter(owner=profile_user).order_by("-created_at")
    avatar_number = str(request.user.profile.avatar_number) if hasattr(request.user, "profile") else "1"
    context = {
        "avatar_number": avatar_number,
        "profile_user": profile_user,
        "user": request.user,
        "profile": profile,
        "posts": posts,
        "pets": pets,
    }
    return render(request, "profile/profile.html", context)


@login_required
def update_avatar(request):
    """
    Обрабатывает обновление аватара пользователя.
    Поддерживает три способа обновления:
    1. Удаление текущего аватара
    2. Загрузка нового изображения
    3. Выбор стандартного аватара

    Args:
        request: HttpRequest объект (POST)

    Returns:
        Перенаправление на страницу профиля с сообщением о результате операции
    """
    if request.method == "POST":
        profile = request.user.profile

        # Обработка удаления аватарки
        if request.POST.get("delete_avatar") == "1":
            profile.avatar.delete(save=False)
            profile.avatar = None
            profile.save()
            messages.success(request, "Аватар успешно удален!")
            return redirect("profile")

        # Обработка загруженного файла
        if "avatar" in request.FILES:
            profile.avatar = request.FILES["avatar"]
            profile.save()
            messages.success(request, "Аватар успешно обновлен!")
            return redirect("profile")

        # Обработка выбора стандартного аватара
        avatar_number = request.POST.get("avatar_number")
        if avatar_number:
            profile.avatar_number = avatar_number
            profile.avatar = None  # Удаляем загруженную аватарку, если выбрали стандартную
            profile.save()
            messages.success(request, "Аватар успешно обновлен!")
            return redirect("profile")

    return redirect("profile")


@login_required
def add_pet(request):
    """
    Обрабатывает добавление нового питомца.

    Args:
        request: HttpRequest объект

    Returns:
        При GET: страница формы добавления питомца
        При POST: перенаправление на профиль при успешном добавлении
    """
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            return redirect("profile")
    else:
        form = PetForm()
    return render(request, "profile/add_pet.html", {"form": form})


@login_required
def edit_pet(request, pet_id):
    """
    Редактирование профиля существующего питомца.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца

    Returns:
        При GET: страница редактирования с заполненной формой
        При POST: перенаправление на профиль питомца при успешном обновлении
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль питомца успешно обновлен")
            return redirect("pet_profile", pet_id=pet.id)
    else:
        form = PetForm(instance=pet)

    return render(request, "profile/edit_pet.html", {"form": form, "pet": pet})


@login_required
def delete_pet(request, pet_id):
    """
    Удаление питомца с подтверждением.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца

    Returns:
        При GET: страница подтверждения удаления
        При POST: перенаправление на профиль после удаления
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == "POST":
        pet.delete()
        messages.success(request, f"Питомец {pet.name} успешно удален")
        return redirect("profile")
    return render(request, "profile/delete_pet.html", {"pet": pet})


@login_required
def pet_profile(request, pet_id):
    """
    Отображает профиль питомца с медицинскими записями и документами.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца

    Returns:
        HttpResponse с шаблоном профиля питомца
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    medical_records = pet.medical_records.all().order_by("-created_at")
    documents = pet.documents.all().order_by("-created_at")

    return render(
        request,
        "profile/pet_profile.html",
        {
            "pet": pet,
            "medical_records": medical_records,
            "documents": documents,
        },
    )


@login_required
def edit_profile(request):
    """
    Редактирование профиля пользователя (основной информации и username).

    Args:
        request: HttpRequest объект

    Returns:
        При GET: страница редактирования с формами
        При POST: перенаправление на профиль при успешном обновлении
    """
    if request.method == "POST":
        username_form = UsernameEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=request.user.profile)

        if username_form.is_valid() and profile_form.is_valid():
            username_form.save()
            profile_form.save()
            messages.success(request, "Профиль успешно обновлен")
            return redirect("profile")
    else:
        username_form = UsernameEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    return render(
        request,
        "profile/edit_profile.html",
        {"username_form": username_form, "profile_form": profile_form},
    )


@login_required
def add_medical_record(request, pet_id):
    """
    Добавление медицинской записи для питомца.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца

    Returns:
        При GET: страница формы добавления записи
        При POST: перенаправление на профиль питомца при успешном добавлении
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == "POST":
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.pet = pet
            medical_record.save()
            messages.success(request, "Медицинская запись добавлена")
            return redirect("pet_profile", pet_id=pet.id)
    else:
        form = MedicalRecordForm()

    return render(
        request,
        "profile/add_medical_record.html",
        {
            "form": form,
            "pet": pet,
        },
    )


@login_required
def add_document(request, pet_id):
    """
    Добавление документа для питомца.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца

    Returns:
        При GET: страница формы добавления документа
        При POST: перенаправление на профиль питомца при успешном добавлении
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.pet = pet
            document.save()
            messages.success(request, "Документ добавлен")
            return redirect("pet_profile", pet_id=pet.id)
    else:
        form = DocumentForm()

    return render(
        request,
        "profile/add_document.html",
        {
            "form": form,
            "pet": pet,
        },
    )


@login_required
def pedigree_page(request, pet_id):
    """
    Отображает страницу родословной питомца.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца

    Returns:
        HttpResponse с шаблоном родословной, содержащим:
        - информацию о питомце
        - форму редактирования родословной
        - список предков
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    pedigree, created = Pedigree.objects.get_or_create(pet=pet)
    ancestors = pedigree.ancestors.all().order_by("generation", "position")

    if request.method == "POST":
        form = PedigreeForm(request.POST, instance=pedigree)
        if form.is_valid():
            form.save()
            messages.success(request, "Информация о родословной обновлена")
            return redirect("pedigree", pet_id=pet.id)
    else:
        form = PedigreeForm(instance=pedigree)

    return render(
        request,
        "profile/pedigree.html",
        {
            "pet": pet,
            "pedigree": pedigree,
            "ancestors": ancestors,
            "form": form,
        },
    )


@login_required
def add_ancestor(request, pet_id):
    """
    Добавление предка в родословную питомца.
    Автоматически определяет следующее поколение и позицию.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца

    Returns:
        При GET: страница формы добавления предка
        При POST: перенаправление на страницу родословной при успешном добавлении
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    pedigree = get_object_or_404(Pedigree, pet=pet)

    if request.method == "POST":
        form = AncestorForm(request.POST)
        if form.is_valid():
            # Проверяем, нет ли уже предка с такими generation и position
            generation = form.cleaned_data["generation"]
            position = form.cleaned_data["position"]

            if Ancestor.objects.filter(pedigree=pedigree, generation=generation, position=position).exists():
                messages.error(request, "Предок с таким поколением и позицией уже существует в родословной")
                return render(request, "profile/add_ancestor.html", {"pet": pet, "form": form})

            ancestor = form.save(commit=False)
            ancestor.pedigree = pedigree
            ancestor.save()
            messages.success(request, "Предок добавлен в родословную")
            return redirect("pedigree", pet_id=pet.id)
    else:
        # Автоматически определяем следующее поколение и позицию
        if request.method == "GET":
            last_generation = pedigree.ancestors.aggregate(models.Max("generation"))["generation__max"] or 0

            # Находим максимальную позицию в текущем поколении
            max_position = (
                    pedigree.ancestors.filter(generation=last_generation).aggregate(models.Max("position"))[
                        "position__max"]
                    or -1
            )

            # Если достигли максимума для поколения (2^n), переходим к следующему
            if max_position >= (2 ** last_generation - 1):
                next_generation = last_generation + 1
                next_position = 0
            else:
                next_generation = last_generation
                next_position = max_position + 1

            form = AncestorForm(
                initial={
                    "generation": next_generation,
                    "position": next_position,
                }
            )

    return render(
        request,
        "profile/add_ancestor.html",
        {
            "pet": pet,
            "form": form,
        },
    )


@login_required
def edit_ancestor(request, pet_id, ancestor_id):
    """
    Редактирование информации о предке в родословной.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца
        ancestor_id: ID предка

    Returns:
        При GET: страница редактирования с заполненной формой
        При POST: перенаправление на страницу родословной при успешном обновлении
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    ancestor = get_object_or_404(Ancestor, id=ancestor_id, pedigree__pet=pet)
    pedigree = get_object_or_404(Pedigree, pet=pet_id)

    if request.method == "POST":
        form = AncestorForm(request.POST, instance=ancestor)

        if form.is_valid():
            # Проверяем, нет ли уже предка с такими generation и position
            generation = form.cleaned_data["generation"]
            position = form.cleaned_data["position"]

            # Исключаем текущего предка из проверки (чтобы можно было сохранить без изменений)
            existing_ancestor = Ancestor.objects.filter(
                pedigree=pedigree,
                generation=generation,
                position=position
            ).exclude(id=ancestor_id).first()

            if existing_ancestor:
                messages.error(request, "Предок с таким поколением и позицией уже существует в родословной")
            else:
                form.save()
                messages.success(request, "Информация о предке обновлена")
                return redirect("pedigree", pet_id=pet.id)
    else:
        form = AncestorForm(instance=ancestor)

    return render(
        request,
        "profile/edit_ancestor.html",
        {
            "pet": pet,
            "ancestor": ancestor,
            "form": form,
        },
    )


@login_required
def delete_ancestor(request, pet_id, ancestor_id):
    """
    Удаление предка из родословной с подтверждением.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца
        ancestor_id: ID предка

    Returns:
        При GET: страница подтверждения удаления
        При POST: перенаправление на страницу родословной после удаления
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    ancestor = get_object_or_404(Ancestor, id=ancestor_id, pedigree__pet=pet)

    if request.method == "POST":
        ancestor.delete()
        messages.success(request, "Предок удален из родословной")
        return redirect("pedigree", pet_id=pet.id)

    return render(
        request,
        "profile/delete_ancestor.html",
        {
            "pet": pet,
            "ancestor": ancestor,
        },
    )


@login_required
def download_pedigree_pdf(request, pet_id):
    """
    Генерирует PDF-документ с родословной питомца.

    Args:
        request: HttpRequest объект
        pet_id: ID питомца

    Returns:
        HttpResponse с PDF-документом для скачивания, содержащим:
        - информацию о питомце
        - родословное древо по поколениям
        - статус родословной
        - дату генерации
    """
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    pedigree = get_object_or_404(Pedigree, pet=pet)
    ancestors = pedigree.ancestors.all().order_by("generation", "position")

    # Группируем предков по поколениям
    ancestors_by_generation = {}
    for ancestor in ancestors:
        if ancestor.generation not in ancestors_by_generation:
            ancestors_by_generation[ancestor.generation] = []
        ancestors_by_generation[ancestor.generation].append(ancestor)

    # Создаем буфер для PDF
    buffer = io.BytesIO()

    # Регистрируем шрифт
    pdfmetrics.registerFont(TTFont("Arial", "static/fonts/arial.ttf"))

    # Создаем документ
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    # Получаем стандартные стили и создаем свои
    styles = getSampleStyleSheet()

    # Создаем кастомные стили с уникальными именами
    styles.add(
        ParagraphStyle(
            name="PedigreeTitle",
            fontName="Arial",
            fontSize=18,
            leading=22,
            alignment=1,  # 1=center
            spaceAfter=20,
        )
    )

    styles.add(
        ParagraphStyle(
            name="PedigreeHeader",
            fontName="Arial",
            fontSize=14,
            leading=16,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="PedigreeNormal",
            fontName="Arial",
            fontSize=12,
            leading=14,
            spaceAfter=6,
        )
    )

    # Содержимое PDF
    story = []

    # Заголовок
    story.append(Paragraph(f"Родословная {pet.name}", styles["PedigreeTitle"]))

    # Информация о питомце
    pet_info = [
        ["Кличка:", pet.name],
        ["Вид:", pet.get_species_display()],
    ]

    if pet.breed:
        pet_info.append(["Порода:", pet.breed])
    if pedigree.date_of_birth:
        pet_info.append(["Дата рождения:", pedigree.date_of_birth.strftime("%d.%m.%Y")])
    if pedigree.registration_number:
        pet_info.append(["Рег. номер:", pedigree.registration_number])
    if pedigree.color:
        pet_info.append(["Окрас:", pedigree.color])

    pet_info.append(["Владелец:", pet.owner.get_full_name() or pet.owner.username])

    if pedigree.breeder:
        pet_info.append(["Заводчик:", pedigree.breeder])

    # Таблица с информацией о питомце
    pet_table = Table(pet_info, colWidths=[100, 300])
    pet_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Arial"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(pet_table)
    story.append(Spacer(1, 20))

    # Родословное древо
    story.append(Paragraph("Родословное древо", styles["PedigreeHeader"]))

    for generation, ancestors_list in sorted(ancestors_by_generation.items()):
        story.append(Paragraph(f"Поколение {generation}", styles["PedigreeNormal"]))

        # Подготовка данных для таблицы
        ancestor_data = [["Кличка", "Порода", "Рег. номер", "Пол"]]

        for ancestor in ancestors_list:
            ancestor_data.append(
                [
                    ancestor.name,
                    ancestor.breed or "-",
                    ancestor.registration_number or "-",
                    "Самец" if ancestor.is_male else "Самка",
                ]
            )

        # Создаем таблицу
        ancestor_table = Table(ancestor_data, colWidths=[120, 120, 100, 60])
        ancestor_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Arial"),
                    ("FONTNAME", (0, 1), (-1, -1), "Arial"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.lightgrey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        story.append(ancestor_table)
        story.append(Spacer(1, 15))

    # Подпись
    story.append(Spacer(1, 20))
    status = "Подтверждена" if pedigree.is_confirmed else "Предварительная"
    story.append(Paragraph(f"Статус: {status}", styles["PedigreeNormal"]))
    story.append(
        Paragraph(
            f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            ParagraphStyle(name="PedigreeFooter", fontName="Arial", fontSize=8, alignment=2),
        )
    )  # 2=right

    # Собираем PDF
    doc.build(story)

    # Возвращаем PDF как ответ
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="pedigree_{pet.name}.pdf"'
    return response

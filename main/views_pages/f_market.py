"""
Django views для функционала маркетплейса животных.
Включает просмотр, создание, редактирование объявлений о животных,
а также систему лайков и личный кабинет продавца.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.db.models import Q
from main.models import *
from main.forms import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import logging
logger = logging.getLogger(__name__)


def avito_page(request):
    """
    Отображает страницу маркетплейса (заглушка).

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном avito.html
    """
    logger.info("Открыта страница Avito")
    context = {}
    return render(request, "market/avito.html", context)


class AnimalListView(ListView):
    """
    Отображает список объявлений о животных с фильтрацией.

    Attributes:
        model: Модель AnimalListing
        template_name: Шаблон для отображения
        context_object_name: Имя переменной контекста
        paginate_by: Количество элементов на странице

    Methods:
        get_queryset: Возвращает отфильтрованный queryset объявлений
        get_context_data: Добавляет в контекст параметры фильтрации
    """
    model = AnimalListing
    template_name = "market/animal_list.html"
    context_object_name = "animals"
    paginate_by = 12

    def get_queryset(self):
        """
        Фильтрует объявления по параметрам GET-запроса:
        - category: Категория животного
        - type: Тип животного
        - age_group: Возрастная группа (baby, young, adult)
        - min_price/max_price: Диапазон цен
        - free_only: Только бесплатные
        - q: Поисковый запрос

        Returns:
            QuerySet отфильтрованных и активных объявлений
        """
        logger.info("Получение списка объявлений о животных")
        queryset = super().get_queryset().filter(is_active=True)
        params = self.request.GET

        # Применяем фильтры в зависимости от параметров запроса
        if "category" in params:
            category = params["category"]
            if category in dict(AnimalListing.CATEGORY_CHOICES):
                queryset = queryset.filter(category=category)

        if "type" in params:
            animal_type = params["type"]
            if animal_type in dict(AnimalListing.TYPE_CHOICES):
                queryset = queryset.filter(animal_type=animal_type)

        if "age_group" in params:
            age_group = params["age_group"]
            if age_group == "baby":
                queryset = queryset.filter(age__lte=6)
            elif age_group == "young":
                queryset = queryset.filter(age__gt=6, age__lte=24)
            elif age_group == "adult":
                queryset = queryset.filter(age__gt=24)

        if "min_price" in params or "max_price" in params:
            min_price = params.get("min_price", 0)
            max_price = params.get("max_price", 1000000)
            try:
                min_price = float(min_price)
                max_price = float(max_price)
                queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
            except (ValueError, TypeError) as e:
                logger.error(f"Ошибка фильтрации по цене: {str(e)}")

        if "free_only" in params:
            queryset = queryset.filter(is_free=True)

        if "q" in params:
            search_query = params["q"]
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query)
                    | Q(description__icontains=search_query)
                    | Q(breed__icontains=search_query)
                )
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст параметры фильтрации для сохранения состояния формы.

        Returns:
            dict: Контекст с параметрами фильтрации и choices для полей формы
        """
        logger.info("Подготовка контекста для списка объявлений")
        context = super().get_context_data(**kwargs)
        context["category_choices"] = AnimalListing.CATEGORY_CHOICES
        context["type_choices"] = AnimalListing.TYPE_CHOICES
        context["age_group_choices"] = AnimalListing.AGE_GROUP_CHOICES
        # Сохраняем выбранные параметры фильтрации
        context.update({
            "selected_category": self.request.GET.get("category"),
            "selected_type": self.request.GET.get("type"),
            "selected_age_group": self.request.GET.get("age_group"),
            "min_price": self.request.GET.get("min_price", "0"),
            "max_price": self.request.GET.get("max_price", "100000"),
            "search_query": self.request.GET.get("q", ""),
            "free_only": bool(self.request.GET.get("free_only"))
        })
        return context


class AnimalDetailView(DetailView):
    """
    Отображает детальную страницу объявления о животном.

    Attributes:
        model: Модель AnimalListing
        template_name: Шаблон для отображения
        context_object_name: Имя переменной контекста
        pk_url_kwarg: Имя параметра URL для первичного ключа

    Methods:
        get_context_data: Добавляет в контекст похожие объявления
    """
    model = AnimalListing
    template_name = "market/animal_detail.html"
    context_object_name = "animal"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст 4 похожих объявления из той же категории.

        Returns:
            dict: Контекст с деталями объявления и похожими объявлениями
        """
        logger.info(f'Получение деталей объявления о животном {self.kwargs.get("pk")}')
        context = super().get_context_data(**kwargs)
        animal = self.object
        context["related_animals"] = (
            AnimalListing.objects.filter(category=animal.category)
            .exclude(pk=animal.pk)
            .filter(is_active=True)[:4]
        )
        return context


class AnimalCreateView(LoginRequiredMixin, CreateView):
    """
    Обрабатывает создание нового объявления о животном.
    Требует аутентификации пользователя.

    Attributes:
        model: Модель AnimalListing
        form_class: Форма для создания объявления
        template_name: Шаблон для отображения
        success_url: URL для перенаправления после успешного создания

    Methods:
        form_valid: Устанавливает продавца и показывает сообщение об успехе
        form_invalid: Логирует ошибки валидации формы
    """
    model = AnimalListing
    form_class = AnimalListingForm
    template_name = "market/animal_form.html"
    success_url = reverse_lazy("animal_list")

    def form_valid(self, form):
        """
        Устанавливает текущего пользователя как продавца и сохраняет объявление.

        Returns:
            HttpResponseRedirect на success_url
        """
        logger.info(f"Создание нового объявления о животном для пользователя {self.request.user}")
        form.instance.seller = self.request.user
        messages.success(self.request, "Объявление успешно создано!")
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Логирует ошибки при невалидной форме.

        Returns:
            HttpResponse с формой и ошибками
        """
        logger.warning(f"Неверная форма для создания объявления пользователем {self.request.user}")
        return super().form_invalid(form)


class VendorDashboardView_pet_market(LoginRequiredMixin, ListView):
    """
    Отображает личный кабинет продавца с его объявлениями.
    Требует аутентификации пользователя.

    Attributes:
        template_name: Шаблон для отображения
        context_object_name: Имя переменной контекста

    Methods:
        get_queryset: Возвращает объявления текущего пользователя
    """
    template_name = "market/vendor_dashboard_pet_market.html"
    context_object_name = "animals"

    def get_queryset(self):
        """
        Возвращает объявления, созданные текущим пользователем.

        Returns:
            QuerySet объявлений пользователя, отсортированных по дате создания
        """
        logger.info(f"Получение панели продавца для пользователя {self.request.user}")
        return AnimalListing.objects.filter(seller=self.request.user).order_by("-created_at")


class EditAnimalView_pet_market(LoginRequiredMixin, UpdateView):
    """
    Обрабатывает редактирование существующего объявления.
    Требует аутентификации пользователя и проверяет владельца.

    Attributes:
        model: Модель AnimalListing
        form_class: Форма для редактирования
        template_name: Шаблон для отображения
        success_url: URL для перенаправления после успешного обновления

    Methods:
        get_queryset: Ограничивает queryset объявлениями текущего пользователя
        form_valid: Логирует успешное обновление
        form_invalid: Логирует ошибки валидации формы
    """
    model = AnimalListing
    form_class = AnimalListingForm
    template_name = "market/animal_form.html"
    success_url = reverse_lazy("vendor_dashboard_pet_market")

    def get_queryset(self):
        """
        Ограничивает queryset только объявлениями текущего пользователя.

        Returns:
            QuerySet объявлений пользователя
        """
        logger.info(f"Получение объявления для редактирования пользователем {self.request.user}")
        return AnimalListing.objects.filter(seller=self.request.user)

    def form_valid(self, form):
        """
        Логирует успешное обновление объявления.

        Returns:
            HttpResponseRedirect на success_url
        """
        logger.info(f"Обновление объявления {self.object.id} пользователем {self.request.user}")
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Логирует ошибки при невалидной форме.

        Returns:
            HttpResponse с формой и ошибками
        """
        logger.warning(
            f"Неверная форма для редактирования объявления {self.object.id} пользователем {self.request.user}")
        return super().form_invalid(form)


class DeleteAnimalView_pet_market(LoginRequiredMixin, DeleteView):
    """
    Обрабатывает удаление объявления.
    Требует аутентификации пользователя и проверяет владельца.

    Attributes:
        model: Модель AnimalListing
        template_name: Шаблон подтверждения удаления
        success_url: URL для перенаправления после удаления

    Methods:
        get_queryset: Ограничивает queryset объявлениями текущего пользователя
        delete: Логирует факт удаления объявления
    """
    model = AnimalListing
    template_name = "market/animal_confirm_delete_pet_market.html"
    success_url = reverse_lazy("vendor_dashboard_pet_market")

    def get_queryset(self):
        """
        Ограничивает queryset только объявлениями текущего пользователя.

        Returns:
            QuerySet объявлений пользователя
        """
        logger.info(f"Получение объявления для удаления пользователем {self.request.user}")
        return AnimalListing.objects.filter(seller=self.request.user)

    def delete(self, request, *args, **kwargs):
        """
        Логирует удаление объявления перед выполнением.

        Returns:
            HttpResponseRedirect на success_url
        """
        logger.info(f"Удаление объявления {self.get_object().id} пользователем {self.request.user}")
        return super().delete(request, *args, **kwargs)


@login_required
def like_animal_pet_market(request, animal_id):
    """
    Обрабатывает добавление лайка к объявлению (AJAX).
    Требует аутентификации пользователя.

    Args:
        request: HttpRequest объект
        animal_id: ID объявления

    Returns:
        JsonResponse с результатом операции или перенаправление
    """
    try:
        animal = get_object_or_404(AnimalListing, id=animal_id)
        like, created = LikesMarket.objects.get_or_create(user=request.user, animal=animal)
        logger.info(f"Пользователь {request.user} поставил лайк объявлению {animal_id}")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "status": "success",
                "action": "liked",
                "likes_count": animal.likes_pet_market.count(),
                "user_likes_count": request.user.liked_animals_pet_market.count(),
            })

        return redirect(request.META.get("HTTP_REFERER", "animal_list"))
    except Exception as e:
        logger.error(f"Ошибка при постановке лайка объявлению {animal_id} пользователем {request.user}: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})


@login_required
def unlike_animal_pet_market(request, animal_id):
    """
    Обрабатывает удаление лайка с объявления (AJAX).
    Требует аутентификации пользователя.

    Args:
        request: HttpRequest объект
        animal_id: ID объявления

    Returns:
        JsonResponse с результатом операции или перенаправление
    """
    try:
        animal = get_object_or_404(AnimalListing, id=animal_id)
        LikesMarket.objects.filter(user=request.user, animal=animal).delete()
        logger.info(f"Пользователь {request.user} убрал лайк с объявления {animal_id}")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "status": "success",
                "action": "unliked",
                "likes_count": animal.likes_pet_market.count(),
                "user_likes_count": request.user.liked_animals_pet_market.count(),
            })

        return redirect(request.META.get("HTTP_REFERER", "animal_list"))
    except Exception as e:
        logger.error(f"Ошибка при удалении лайка с объявления {animal_id} пользователем {request.user}: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})


@login_required
def liked_animals_pet_market(request):
    """
    Отображает список объявлений, лайкнутых текущим пользователем.
    Требует аутентификации пользователя.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном и списком лайкнутых объявлений
    """
    logger.info(f"Получение списка понравившихся объявлений для пользователя {request.user}")
    liked_animals = AnimalListing.objects.filter(likes_pet_market__user=request.user).order_by(
        "-likes_pet_market__created_at"
    )

    return render(
        request,
        "market/liked_animals_pet_market.html",
        {"liked_animals": liked_animals},
    )

"""
Django views для функционала интернет-магазина кормов для животных.
Включает просмотр товаров, корзину, оформление заказов, избранное и панель продавца.
"""

import logging
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Q, Avg
from main.models import *
from main.forms import *
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin

logger = logging.getLogger(__name__)


class ProductListView(ListView):
    """
    Отображает список товаров с фильтрацией и сортировкой.

    Attributes:
        model: Модель Product
        template_name: Шаблон для отображения
        context_object_name: Имя переменной контекста
        paginate_by: Количество элементов на странице

    Methods:
        get_queryset: Возвращает отфильтрованный queryset товаров
        get_context_data: Добавляет в контекст параметры фильтрации
    """
    model = Product
    template_name = "food/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        """
        Фильтрует товары по параметрам GET-запроса:
        - pet_type: Тип животного
        - category: Категория товара
        - food_type: Тип корма (сухой, влажный и т.д.)
        - search: Поисковый запрос
        - sort: Вариант сортировки (по цене, рейтингу и т.д.)

        Returns:
            QuerySet отфильтрованных товаров
        """
        logger.info("Получение списка продуктов")
        queryset = super().get_queryset()

        # Применяем фильтры
        if pet_type := self.request.GET.get("pet_type"):
            queryset = queryset.filter(pet_type=pet_type)

        if category_slug := self.request.GET.get("category"):
            queryset = queryset.filter(category__slug=category_slug)

        if food_type := self.request.GET.get("food_type"):
            if food_type == "sale":
                queryset = queryset.filter(old_price__isnull=False)
            else:
                queryset = queryset.filter(food_type=food_type)

        if search_query := self.request.GET.get("search"):
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Применяем сортировку
        if sort_by := self.request.GET.get("sort"):
            if sort_by == "price-asc":
                queryset = queryset.order_by("price")
            elif sort_by == "price-desc":
                queryset = queryset.order_by("-price")
            elif sort_by == "rating":
                queryset = queryset.annotate(avg_rating=Avg("reviews__rating")).order_by("-avg_rating")
            elif sort_by == "new":
                queryset = queryset.order_by("-created_at")
        else:
            queryset = queryset.order_by("-rating")

        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст:
        - Параметры фильтрации
        - Списки избранных товаров
        - Количество товаров в корзине

        Returns:
            dict: Контекст с параметрами фильтрации
        """
        logger.info("Подготовка контекста для списка продуктов")
        context = super().get_context_data(**kwargs)

        context.update({
            "pet_type_choices": Product.PET_TYPE_CHOICES,
            "current_pet_type": self.request.GET.get("pet_type"),
            "current_category": self.request.GET.get("category"),
            "current_food_type": self.request.GET.get("food_type"),
            "search_query": self.request.GET.get("search", ""),
            "sort_by": self.request.GET.get("sort", "popular"),
        })

        # Получаем список избранных товаров
        if self.request.user.is_authenticated:
            context["user_favorite_ids"] = list(
                Favorite.objects.filter(user=self.request.user).values_list("product_id", flat=True)
            )
        else:
            context["user_favorite_ids"] = []

        # Получаем количество товаров в корзине
        cart = Cart.objects.filter(
            user=self.request.user if self.request.user.is_authenticated
            else None,
            session_key=self.request.session.session_key if not self.request.user.is_authenticated
            else None
        ).first()
        context["total_items"] = sum(item.quantity for item in cart.cartitem_set.all()) if cart else 0

        return context


class ProductDetailView(DetailView):
    """
    Отображает детальную страницу товара.

    Attributes:
        model: Модель Product
        template_name: Шаблон для отображения
        context_object_name: Имя переменной контекста
        slug_url_kwarg: Имя параметра URL для slug

    Methods:
        get_context_data: Добавляет форму отзыва и список избранных
        post: Обрабатывает отправку отзыва
    """
    model = Product
    template_name = "food/product_detail.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст:
        - Форму отзыва
        - Отзыв текущего пользователя
        - Список избранных товаров
        - Все отзывы о товаре

        Returns:
            dict: Контекст с деталями товара
        """
        logger.info(f'Получение деталей продукта {self.kwargs.get("slug")}')
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        context.update({
            "review_form": ReviewForm(),
            "reviews": product.reviews.all().select_related("user"),
        })

        if self.request.user.is_authenticated:
            context.update({
                "user_review": Review.objects.filter(
                    product=product,
                    user=self.request.user
                ).first(),
                "user_favorite_ids": list(
                    Favorite.objects.filter(user=self.request.user).values_list("product_id", flat=True)
                ),
            })
        else:
            context["user_favorite_ids"] = []

        return context

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает отправку отзыва о товаре.

        Returns:
            Перенаправление на страницу товара с сообщением
        """
        product = self.get_object()
        form = ReviewForm(request.POST)

        if form.is_valid() and request.user.is_authenticated:
            review, created = Review.objects.update_or_create(
                product=product,
                user=request.user,
                defaults=form.cleaned_data
            )
            product.update_rating()
            logger.info(f"Отзыв сохранен для продукта {product.slug} пользователем {request.user.username}")
            messages.success(request, "Ваш отзыв сохранен!")
        else:
            logger.warning(f"Ошибка при сохранении отзыва для продукта {product.slug}")
            messages.error(request, "Ошибка при сохранении отзыва")

        return redirect("product_detail", slug=product.slug)


@login_required
def add_to_cart(request, product_id):
    """
    Добавляет товар в корзину.

    Args:
        request: HttpRequest объект
        product_id: ID товара

    Returns:
        Перенаправление в корзину или список товаров
    """
    try:
        product = get_object_or_404(Product, id=product_id)

        if product.stock <= 0:
            logger.warning(f"Попытка добавить в корзину отсутствующий товар {product_id}")
            messages.error(request, "Этот товар закончился")
            return redirect("product_list")

        # Получаем или создаем корзину
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)

        # Добавляем товар в корзину
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": 1}
        )

        if not created:
            if cart_item.quantity + 1 > product.stock:
                logger.warning(f"Недостаточно товара {product_id} на складе")
                messages.error(request, "Недостаточно товара на складе")
                return redirect("cart_view")
            cart_item.quantity += 1
            cart_item.save()

        logger.info(f"Товар {product_id} добавлен в корзину")
        return redirect("cart_view")
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара {product_id} в корзину: {str(e)}")
        return redirect("product_list")


@login_required
def cart_view(request):
    """
    Отображает содержимое корзины.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном корзины
    """
    logger.info("Открыта страница корзины")
    cart = Cart.objects.filter(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key if not request.user.is_authenticated else None
    ).first()

    context = {
        "cart": cart,
        "cart_items": cart.cartitem_set.all() if cart else [],
        "total_price": sum(item.get_total_price() for item in cart.cartitem_set.all()) if cart else 0,
    }
    return render(request, "food/cart.html", context)


@login_required
def checkout_view(request):
    """
    Обрабатывает оформление заказа.

    Args:
        request: HttpRequest объект

    Returns:
        При успешном оформлении: перенаправление на детали заказа
        При ошибке: форма с сообщениями
    """
    try:
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.cartitem_set.all()

        if not cart_items:
            logger.warning("Попытка оформления заказа с пустой корзиной")
            messages.warning(request, "Ваша корзина пуста")
            return redirect("product_list")

        # Проверяем наличие товаров
        for item in cart_items:
            if item.quantity > item.product.stock:
                logger.warning(f"Недостаточно товара {item.product.name} на складе")
                messages.error(request, f'Товара "{item.product.name}" недостаточно на складе')
                return redirect("cart_view")

        total_price = sum(item.get_total_price() for item in cart_items)

        if request.method == "POST":
            form = CheckoutForm(request.POST)
            if form.is_valid():
                # Создаем заказ
                order = Order.objects.create(
                    user=request.user,
                    total_price=total_price,
                    **form.cleaned_data
                )

                # Создаем позиции заказа и обновляем остатки
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,
                    )
                    item.product.stock -= item.quantity
                    item.product.save()

                cart_items.delete()
                logger.info(f"Заказ успешно оформлен пользователем {request.user.username}")
                return redirect("order_detail")
            else:
                logger.warning("Неверная форма оформления заказа")
        else:
            initial_data = {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
            }
            form = CheckoutForm(initial=initial_data)

        context = {
            "form": form,
            "cart_items": cart_items,
            "total_price": total_price,
        }
        logger.info("Открыта страница оформления заказа")
        return render(request, "food/checkout.html", context)
    except Exception as e:
        logger.error(f"Ошибка при оформлении заказа: {str(e)}")
        return redirect("cart_view")


@login_required
def seller_dashboard(request):
    """
    Отображает панель управления продавца.

    Args:
        request: HttpRequest объект

    Returns:
        HttpResponse с шаблоном панели продавца
    """
    logger.info(f"Открыта панель продавца для пользователя {request.user.username}")
    products = Product.objects.filter(owner=request.user)
    return render(request, "food/seller_dashboard.html", {"products": products})


@login_required
def product_create_view(request):
    """
    Обрабатывает создание нового товара.

    Args:
        request: HttpRequest объект

    Returns:
        При успешном создании: перенаправление в панель продавца
        При ошибке: форма с сообщениями
    """
    try:
        if request.method == "POST":
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                product = form.save(commit=False)
                product.owner = request.user
                product.save()
                logger.info(f"Продукт создан пользователем {request.user.username}")
                return redirect("seller_dashboard")
            else:
                logger.warning("Неверная форма создания продукта")
        else:
            form = ProductForm()
        logger.info("Открыта форма создания продукта")
        return render(request, "food/product_form.html", {"form": form})
    except Exception as e:
        logger.error(f"Ошибка при создании продукта: {str(e)}")
        return redirect("seller_dashboard")


@login_required
def edit_product(request, pk):
    """
    Обрабатывает редактирование товара.

    Args:
        request: HttpRequest объект
        pk: ID товара

    Returns:
        При успешном редактировании: перенаправление в панель продавца
        При ошибке: форма с сообщениями
    """
    try:
        product = get_object_or_404(Product, pk=pk, owner=request.user)
        if request.method == "POST":
            form = ProductForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                logger.info(f"Продукт {pk} обновлен пользователем {request.user.username}")
                return redirect("seller_dashboard")
            else:
                logger.warning(f"Неверная форма редактирования продукта {pk}")
        else:
            form = ProductForm(instance=product)
        logger.info(f"Открыта форма редактирования продукта {pk}")
        return render(
            request,
            "food/product_form.html",
            {"form": form, "title": "Редактировать товар"},
        )
    except Exception as e:
        logger.error(f"Ошибка при редактировании продукта {pk}: {str(e)}")
        return redirect("seller_dashboard")


@login_required
def delete_product(request, pk):
    """
    Обрабатывает удаление товара.

    Args:
        request: HttpRequest объект
        pk: ID товара

    Returns:
        При успешном удалении: перенаправление в панель продавца
        При ошибке: перенаправление в панель продавца с ошибкой
    """
    try:
        product = get_object_or_404(Product, pk=pk, owner=request.user)
        if request.method == "POST":
            product.delete()
            logger.info(f"Продукт {pk} удален пользователем {request.user.username}")
            return redirect("seller_dashboard")
        logger.info(f"Открыта страница подтверждения удаления продукта {pk}")
        return render(request, "food/delete_product.html", {"product": product})
    except Exception as e:
        logger.error(f"Ошибка при удалении продукта {pk}: {str(e)}")
        return redirect("seller_dashboard")


@require_POST
@login_required
def update_cart_item(request, item_id):
    """
    Обновляет количество товара в корзине (AJAX).

    Args:
        request: HttpRequest объект (POST)
        item_id: ID позиции в корзине

    Returns:
        JsonResponse с результатом операции
    """
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        product = cart_item.product

        data = json.loads(request.body.decode("utf-8"))
        quantity = int(data.get("quantity", 1))

        if quantity <= 0:
            logger.warning(f"Попытка установить недопустимое количество {quantity} для товара {item_id}")
            return JsonResponse({"success": False, "error": "Недопустимое количество"}, status=400)

        if quantity > product.stock:
            logger.warning(f"Недостаточно товара {product.id} на складе для количества {quantity}")
            return JsonResponse(
                {
                    "success": False,
                    "error": "Недостаточно товара на складе",
                    "available_quantity": product.stock,
                },
                status=400,
            )

        cart_item.quantity = quantity
        cart_item.save()
        logger.info(f"Количество товара {item_id} в корзине обновлено до {quantity}")
        return JsonResponse(
            {
                "success": True,
                "total_price": str(cart_item.get_total_price()),
                "cart_total": str(cart_item.cart.get_total_price()),
            }
        )
    except CartItem.DoesNotExist:
        logger.error(f"Товар {item_id} не найден в корзине")
        return JsonResponse({"success": False, "error": "Товар не найден"}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при обновлении товара {item_id} в корзине: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
def remove_cart_item(request, item_id):
    """
    Удаляет товар из корзины (AJAX).

    Args:
        request: HttpRequest объект (POST)
        item_id: ID позиции в корзине

    Returns:
        JsonResponse с результатом операции
    """
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart_item.delete()
        logger.info(f"Товар {item_id} удален из корзины")
        return JsonResponse({"success": True, "cart_total": cart_item.cart.get_total_price()})
    except CartItem.DoesNotExist:
        logger.error(f"Товар {item_id} не найден в корзине")
        return JsonResponse({"success": False, "error": "Товар не найден"}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при удалении товара {item_id} из корзины: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def toggle_favorite(request, product_id):
    """
    Добавляет/удаляет товар в избранное.

    Args:
        request: HttpRequest объект
        product_id: ID товара

    Returns:
        Перенаправление на предыдущую страницу
    """
    try:
        product = get_object_or_404(Product, id=product_id)
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)

        if not created:
            favorite.delete()
            logger.info(f"Продукт {product_id} удален из избранного пользователем {request.user.username}")
        else:
            logger.info(f"Продукт {product_id} добавлен в избранное пользователем {request.user.username}")

        return redirect(request.META.get("HTTP_REFERER", "product_list"))
    except Exception as e:
        logger.error(f"Ошибка при переключении избранного для продукта {product_id}: {str(e)}")
        return redirect("product_list")


class FavoriteListView(LoginRequiredMixin, ListView):
    """
    Отображает список избранных товаров.

    Attributes:
        model: Модель Favorite
        template_name: Шаблон для отображения
        context_object_name: Имя переменной контекста

    Methods:
        get_queryset: Возвращает избранные товары пользователя
        get_context_data: Добавляет список ID избранных товаров
    """
    model = Favorite
    template_name = "food/favorite_list.html"
    context_object_name = "favorites"

    def get_queryset(self):
        """
        Возвращает избранные товары текущего пользователя.

        Returns:
            QuerySet избранных товаров с предзагрузкой product
        """
        logger.info(f"Получение списка избранного для пользователя {self.request.user.username}")
        return Favorite.objects.filter(user=self.request.user).select_related("product")

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст список ID избранных товаров.

        Returns:
            dict: Контекст с избранными товарами
        """
        logger.info("Подготовка контекста для списка избранного")
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["favorite_ids"] = Favorite.objects.filter(
                user=self.request.user
            ).values_list("product_id", flat=True)
        return context


def food_page(request):
    logger.info("Открыта страница еды")
    context = {}
    return render(request, "food/food.html", context)


def order_detail(request):
    logger.info("Открыта страница деталей заказа")
    # Получаем все продукты
    products = Product.objects.all()
    context = {
        'products': products,
    }
    return render(request, "food/order_detail.html", context)

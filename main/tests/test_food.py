from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
import json

from main.models import Product, Cart, CartItem, Order, OrderItem, Review, Favorite
from main.forms import ReviewForm, CheckoutForm, ProductForm


class ProductListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # Create a simple image file for testing
        self.test_image = SimpleUploadedFile(
            name="test_image.jpg", content=b"simple image content", content_type="image/jpeg"
        )

        self.product1 = Product.objects.create(
            name="Product 1",
            slug="product-1",
            price=100,
            pet_type="cat",
            stock=10,
            owner=self.user,
            image=self.test_image,
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            slug="product-2",
            price=200,
            pet_type="dog",
            stock=5,
            old_price=250,
            owner=self.user,
            image=self.test_image,
        )
        self.url = reverse("product_list")

    def test_product_list_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product 1")
        self.assertContains(response, "Product 2")

    def test_product_list_filtering(self):
        # Filter by pet type
        response = self.client.get(self.url, {"pet_type": "cat"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product 1")
        self.assertNotContains(response, "Product 2")

        # Filter by food type (sale)
        response = self.client.get(self.url, {"food_type": "sale"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Product 1")
        self.assertContains(response, "Product 2")

    def test_product_list_search(self):
        response = self.client.get(self.url, {"search": "Product 1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product 1")
        self.assertNotContains(response, "Product 2")

    def test_product_list_sorting(self):
        # Sort by price ascending
        response = self.client.get(self.url, {"sort": "price-asc"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(products[0].price, 100)

        # Sort by price descending
        response = self.client.get(self.url, {"sort": "price-desc"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(products[0].price, 200)

    def test_product_list_authenticated_user(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_favorite_ids", response.context)


class ProductDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.test_image = SimpleUploadedFile(
            name="test_image.jpg", content=b"simple image content", content_type="image/jpeg"
        )

        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=100,
            pet_type="cat",
            stock=10,
            owner=self.user,
            image=self.test_image,
        )
        self.url = reverse("product_detail", kwargs={"slug": "test-product"})

    def test_product_detail_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertIsInstance(response.context["review_form"], ReviewForm)

    def test_product_detail_review_post(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.url, {"rating": 5, "comment": "Great product!"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(product=self.product, user=self.user).exists())

    def test_product_detail_review_update(self):
        review = Review.objects.create(product=self.product, user=self.user, rating=3, comment="Average")
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.url, {"rating": 5, "comment": "Updated to great!"})
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)


class CartViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.test_image = SimpleUploadedFile(
            name="test_image.jpg", content=b"simple image content", content_type="image/jpeg"
        )

        self.product = Product.objects.create(
            name="Test Product", slug="test-product", price=100, stock=10, owner=self.user, image=self.test_image
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        self.add_to_cart_url = reverse("add_to_cart", kwargs={"product_id": self.product.id})
        self.cart_view_url = reverse("cart_view")
        self.update_cart_url = reverse("update_cart_item", kwargs={"item_id": self.cart_item.id})
        self.remove_cart_url = reverse("remove_cart_item", kwargs={"item_id": self.cart_item.id})

    def test_add_to_cart(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.add_to_cart_url)
        self.assertEqual(response.status_code, 302)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)

    def test_add_to_cart_new_item(self):
        new_product = Product.objects.create(
            name="New Product", slug="new-product", price=200, stock=5, owner=self.user, image=self.test_image
        )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("add_to_cart", kwargs={"product_id": new_product.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CartItem.objects.filter(product=new_product).exists())

    def test_add_to_cart_out_of_stock(self):
        self.product.stock = 0
        self.product.save()
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.add_to_cart_url)
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Этот товар закончился")

    def test_cart_view(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.cart_view_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")

    def test_update_cart_item(self):
        self.client.login(username="testuser", password="testpass123")
        data = {"quantity": 3}
        response = self.client.post(self.update_cart_url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 3)

    def test_remove_cart_item(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.remove_cart_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com", first_name="Test", last_name="User"
        )

        self.test_image = SimpleUploadedFile(
            name="test_image.jpg", content=b"simple image content", content_type="image/jpeg"
        )

        self.product = Product.objects.create(
            name="Test Product", slug="test-product", price=100, stock=10, owner=self.user, image=self.test_image
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        self.checkout_url = reverse("checkout")

    def test_checkout_view_get(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], CheckoutForm)

    def test_checkout_view_post_valid(self):
        self.client.login(username="testuser", password="testpass123")
        data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
            "payment_method": "card",
            "delivery_method": "courier",
            "notes": "Test note",
        }
        response = self.client.post(self.checkout_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_checkout_view_post_invalid(self):
        self.client.login(username="testuser", password="testpass123")
        data = {
            "first_name": "",  # Invalid - required field
            "last_name": "User",
            "email": "test@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
            "payment_method": "card",
            "delivery_method": "courier",
            "notes": "Test note",
        }
        response = self.client.post(self.checkout_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_checkout_empty_cart(self):
        self.cart_item.delete()
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Ваша корзина пуста")


class FavoriteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.test_image = SimpleUploadedFile(
            name="test_image.jpg", content=b"simple image content", content_type="image/jpeg"
        )

        self.product = Product.objects.create(
            name="Test Product", slug="test-product", price=100, stock=10, owner=self.user, image=self.test_image
        )
        self.toggle_favorite_url = reverse("toggle_favorite", kwargs={"product_id": self.product.id})
        self.favorite_list_url = reverse("favorite_list")

    def test_toggle_favorite_add(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.toggle_favorite_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Favorite.objects.filter(user=self.user, product=self.product).exists())

    def test_toggle_favorite_remove(self):
        Favorite.objects.create(user=self.user, product=self.product)
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.toggle_favorite_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Favorite.objects.filter(user=self.user, product=self.product).exists())

    def test_favorite_list_view(self):
        Favorite.objects.create(user=self.user, product=self.product)
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.favorite_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")


class SellerDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.test_image = SimpleUploadedFile(
            name="test_image.jpg", content=b"simple image content", content_type="image/jpeg"
        )

        self.product = Product.objects.create(
            name="Test Product", slug="test-product", price=100, stock=10, owner=self.user, image=self.test_image
        )
        self.seller_dashboard_url = reverse("seller_dashboard")
        self.product_create_url = reverse("product_create")
        self.product_edit_url = reverse("edit_product", kwargs={"pk": self.product.id})
        self.product_delete_url = reverse("delete_product", kwargs={"pk": self.product.id})

    def test_seller_dashboard(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.seller_dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")

    def test_product_create_get(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.product_create_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], ProductForm)

    # def test_product_create_post_valid(self):
    #     self.client.login(username='testuser', password='testpass123')
    #     data = {
    #         'name': 'New Product',
    #         'price': 200,
    #         'stock': 5,
    #         'pet_type': 'cat',
    #         'description': 'Test description'
    #     }
    #     response = self.client.post(self.product_create_url, data)
    #     self.assertEqual(response.status_code, 302)
    #     self.assertTrue(Product.objects.filter(name='New Product').exists())

    def test_product_edit_get(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.product_edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], ProductForm)

    # def test_product_edit_post(self):
    #     self.client.login(username='testuser', password='testpass123')
    #     data = {
    #         'name': 'Updated Product',
    #         'price': 150,
    #         'stock': 8,
    #         'pet_type': 'dog',
    #         'description': 'Updated description'
    #     }
    #     response = self.client.post(self.product_edit_url, data)
    #     self.assertEqual(response.status_code, 302)
    #     self.product.refresh_from_db()
    #     self.assertEqual(self.product.name, 'Updated Product')

    def test_product_delete_confirm(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.product_delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")

    def test_product_delete_post(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.product_delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class EcommerceFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='buyer',
            password='secret123',
            role='buyer',
        )
        self.category = Category.objects.create(name='Home', slug='home')
        self.product = Product.objects.create(
            name='Sample Mug',
            slug='sample-mug',
            description='A premium ceramic mug',
            price=19.99,
            stock=5,
            category=self.category,
        )

    def test_home_page_lists_products(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sample Mug')

    def test_buyer_can_create_order_from_cart(self):
        self.client.login(username='buyer', password='secret123')
        self.client.post(reverse('add_to_cart', args=[self.product.pk]), {'quantity': 1})

        checkout_response = self.client.get(reverse('checkout'))
        self.assertEqual(checkout_response.status_code, 200)

        order_response = self.client.post(reverse('checkout'), {
            'full_name': 'Buyer One',
            'address': '123 Demo Street',
            'city': 'Testville',
            'phone': '1234567890',
        })

        self.assertEqual(order_response.status_code, 302)
        self.assertEqual(self.user.orders.count(), 1)

    def test_seller_can_create_product_with_category(self):
        seller = get_user_model().objects.create_user(
            username='seller',
            password='secret123',
            role='seller',
        )
        self.client.login(username='seller', password='secret123')

        response = self.client.post(reverse('add_product'), {
            'name': 'Desk Lamp',
            'slug': 'desk-lamp',
            'description': 'A bright desk lamp',
            'price': '29.99',
            'stock': 7,
            'category': self.category.pk,
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(slug='desk-lamp').exists())
        created_product = Product.objects.get(slug='desk-lamp')
        self.assertEqual(created_product.category, self.category)
        self.assertEqual(created_product.seller, seller)

    def test_guest_cannot_add_to_cart(self):
        response = self.client.post(reverse('add_to_cart', args=[self.product.pk]), {'quantity': 1})

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        self.assertEqual(self.client.session.get('cart', {}), {})

    def test_seller_cannot_add_to_cart(self):
        seller = get_user_model().objects.create_user(
            username='seller-two',
            password='secret123',
            role='seller',
        )
        self.client.login(username='seller-two', password='secret123')

        response = self.client.post(reverse('add_to_cart', args=[self.product.pk]), {'quantity': 1})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get('cart', {}), {})
        self.assertEqual(seller.role, 'seller')

    def test_logout_redirects_to_login(self):
        self.client.login(username='buyer', password='secret123')
        response = self.client.get(reverse('logout'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

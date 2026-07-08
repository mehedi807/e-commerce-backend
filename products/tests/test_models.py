from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from products.constants import ProductStatus
from products.models import Category, Product


class CategoryModelTests(TestCase):
    """Tests for the Category model fields, constraints, and relationships."""

    def setUp(self):
        self.root = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices',
        )

    def test_create_category_success(self):
        self.assertEqual(self.root.name, 'Electronics')
        self.assertEqual(self.root.slug, 'electronics')
        self.assertEqual(self.root.description, 'Electronic devices')
        self.assertIsNone(self.root.parent)

    def test_category_slug_unique(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name='Electronics Division',
                slug='electronics',
            )

    def test_category_parent_child_relationship(self):
        child = Category.objects.create(
            name='Phones',
            slug='phones',
            parent=self.root,
        )

        self.assertEqual(child.parent, self.root)
        self.assertIn(child, self.root.children.all())

    def test_category_cascade_delete(self):
        child = Category.objects.create(
            name='Laptops',
            slug='laptops',
            parent=self.root,
        )
        grandchild = Category.objects.create(
            name='Gaming Laptops',
            slug='gaming-laptops',
            parent=child,
        )

        child_id = child.id
        grandchild_id = grandchild.id

        child.delete()

        self.assertFalse(Category.objects.filter(id=child_id).exists())
        self.assertFalse(Category.objects.filter(id=grandchild_id).exists())
        self.assertTrue(Category.objects.filter(id=self.root.id).exists())

    def test_category_null_parent_for_root(self):
        self.assertIsNone(self.root.parent)
        self.assertIsNone(self.root.parent_id)

    def test_category_str_returns_name(self):
        self.assertEqual(str(self.root), 'Electronics')

    def test_category_ordering_by_name(self):
        Category.objects.all().delete()
        c1 = Category.objects.create(name='Wearables', slug='wearables')
        c2 = Category.objects.create(name='Accessories', slug='accessories')
        c3 = Category.objects.create(name='Laptops', slug='laptops')

        categories = list(Category.objects.all())
        self.assertEqual(categories, [c2, c3, c1])

    def test_category_has_timestamps(self):
        self.assertIsNotNone(self.root.created_at)
        self.assertIsNotNone(self.root.updated_at)

    def test_category_description_defaults_to_empty(self):
        cat = Category.objects.create(name='Books', slug='books')
        self.assertEqual(cat.description, '')


class ProductModelTests(TestCase):
    """Tests for the Product model fields, constraints, and relationships."""

    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
        )
        self.product = Product.objects.create(
            name='iPhone 16',
            sku='PHONE-IP16',
            description='Latest iPhone',
            price=Decimal('999.99'),
            stock=50,
            status=ProductStatus.ACTIVE,
            category=self.category,
        )

    def test_create_product_success(self):
        self.assertEqual(self.product.name, 'iPhone 16')
        self.assertEqual(self.product.sku, 'PHONE-IP16')
        self.assertEqual(self.product.price, Decimal('999.99'))
        self.assertEqual(self.product.stock, 50)
        self.assertEqual(self.product.status, ProductStatus.ACTIVE)
        self.assertEqual(self.product.category, self.category)

    def test_product_sku_unique(self):
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name='Apple iPhone 16 Pro',
                sku='PHONE-IP16',
                price=Decimal('1099.99'),
                stock=15,
            )

    def test_product_default_status_active(self):
        product = Product.objects.create(
            name='Logitech MX Master 3S',
            sku='MOUSE-MX3S',
            price=Decimal('99.99'),
        )
        self.assertEqual(product.status, ProductStatus.ACTIVE)

    def test_product_default_stock_zero(self):
        product = Product.objects.create(
            name='Sony WH-1000XM5',
            sku='HEAD-XM5',
            price=Decimal('349.99'),
        )
        self.assertEqual(product.stock, 0)

    def test_product_str_format(self):
        self.assertEqual(str(self.product), 'iPhone 16 (PHONE-IP16)')

    def test_product_category_set_null_on_delete(self):
        product_id = self.product.id
        self.category.delete()

        self.product.refresh_from_db()
        self.assertIsNone(self.product.category)
        self.assertTrue(Product.objects.filter(id=product_id).exists())

    def test_product_category_optional(self):
        product = Product.objects.create(
            name='Kindle Paperwhite',
            sku='EBOOK-KINDLE',
            price=Decimal('139.99'),
            stock=25,
        )
        self.assertIsNone(product.category)

    def test_product_status_choices_valid(self):
        self.product.status = ProductStatus.ACTIVE
        self.product.full_clean()

        self.product.status = ProductStatus.INACTIVE
        self.product.full_clean()

    def test_product_status_choices_invalid(self):
        self.product.status = 'invalid_status'

        with self.assertRaises(ValidationError):
            self.product.full_clean()

    def test_product_ordering_by_created_at_desc(self):
        p2 = Product.objects.create(
            name='Dell XPS 15',
            sku='LAPTOP-XPS15',
            price=Decimal('1899.99'),
        )
        products = list(Product.objects.all())
        self.assertEqual(products, [p2, self.product])

    def test_product_has_timestamps(self):
        self.assertIsNotNone(self.product.created_at)
        self.assertIsNotNone(self.product.updated_at)

    def test_product_non_positive_price_raises_validation_error(self):
        """Price must be strictly positive per business rule; zero/negative should fail validation."""
        invalid_prices = [Decimal('-10.00'), Decimal('0.00')]

        for price in invalid_prices:
            with self.subTest(price=price):
                product = Product(
                    name='Samsung Galaxy S24',
                    sku='PHONE-S24',
                    price=price,
                    stock=5,
                )
                with self.assertRaises(ValidationError) as ctx:
                    product.full_clean()
                self.assertIn('price', ctx.exception.message_dict)

    def test_product_description_defaults_to_empty(self):
        product = Product.objects.create(
            name='Apple AirTag',
            sku='TRACKER-TAG',
            price=Decimal('29.00'),
        )
        self.assertEqual(product.description, '')

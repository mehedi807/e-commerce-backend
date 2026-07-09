from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from authentication.models import User
from orders.models import Order
from orders.services import order_create, order_mark_paid
from products.constants import ProductStatus
from products.models import Category, Product


class Command(BaseCommand):
    help = 'Seed admin user, categories, and sample products.'

    def handle(self, *args, **options):
        self._create_admin_user()
        customer = self._create_customer_user()
        categories = self._create_categories()
        self._create_products(categories)
        self._create_sample_orders(customer)
        self.stdout.write(self.style.SUCCESS('Seeding completed successfully.'))

    def _create_admin_user(self):
        email = 'admin@example.com'
        if User.objects.filter(email=email).exists():
            self.stdout.write(f'Admin user "{email}" already exists, skipping.')
            return

        User.objects.create_superuser(
            email=email,
            password='admin123',
            first_name='Admin',
            last_name='User',
        )
        self.stdout.write(self.style.SUCCESS(f'Created admin user: {email}'))

    def _create_categories(self) -> dict[str, Category]:
        category_tree = {
            'Electronics': {
                'children': {
                    'Phones': {
                        'children': {
                            'Smartphones': {},
                        },
                    },
                    'Laptops': {},
                    'Accessories': {},
                },
            },
            'Clothing': {
                'children': {
                    'Men': {},
                    'Women': {},
                },
            },
            'Books': {},
        }

        created = {}

        def _create_recursive(tree, parent=None):
            for name, data in tree.items():
                cat, was_created = Category.objects.get_or_create(
                    name=name,
                    defaults={'slug': slugify(name), 'parent': parent},
                )
                if was_created:
                    self.stdout.write(f'  Created category: {name}')
                else:
                    self.stdout.write(f'  Category "{name}" already exists, skipping.')

                created[name] = cat

                children = data.get('children', {})
                if children:
                    _create_recursive(children, parent=cat)

        _create_recursive(category_tree)
        return created

    def _create_products(self, categories: dict[str, Category]):
        products = [
            {
                'name': 'iPhone 16 Pro',
                'sku': 'PHONE-IP16PRO',
                'description': 'Apple iPhone 16 Pro with A18 Pro chip.',
                'price': Decimal('1199.99'),
                'stock': 50,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Smartphones'),
            },
            {
                'name': 'Samsung Galaxy S25 Ultra',
                'sku': 'PHONE-SGS25U',
                'description': 'Samsung Galaxy S25 Ultra with Snapdragon 8 Elite.',
                'price': Decimal('1299.99'),
                'stock': 35,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Smartphones'),
            },
            {
                'name': 'MacBook Pro 16"',
                'sku': 'LAPTOP-MBP16',
                'description': 'Apple MacBook Pro 16-inch with M4 Max chip.',
                'price': Decimal('2499.99'),
                'stock': 20,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Laptops'),
            },
            {
                'name': 'Dell XPS 15',
                'sku': 'LAPTOP-DXPS15',
                'description': 'Dell XPS 15 with Intel Core Ultra 9.',
                'price': Decimal('1799.99'),
                'stock': 15,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Laptops'),
            },
            {
                'name': 'AirPods Pro 3',
                'sku': 'ACC-APP3',
                'description': 'Apple AirPods Pro 3 with advanced noise cancellation.',
                'price': Decimal('249.99'),
                'stock': 100,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Accessories'),
            },
            {
                'name': 'USB-C Hub 10-in-1',
                'sku': 'ACC-USBC10',
                'description': 'Multi-port USB-C hub with HDMI, SD card, and Ethernet.',
                'price': Decimal('59.99'),
                'stock': 200,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Accessories'),
            },
            {
                'name': 'Classic Fit Cotton T-Shirt',
                'sku': 'CLO-MEN-TS01',
                'description': '100% organic cotton crew neck t-shirt.',
                'price': Decimal('29.99'),
                'stock': 300,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Men'),
            },
            {
                'name': 'Slim Fit Jeans',
                'sku': 'CLO-WMN-JN01',
                'description': 'High-waisted slim fit stretch jeans.',
                'price': Decimal('69.99'),
                'stock': 150,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Women'),
            },
            {
                'name': 'The Pragmatic Programmer',
                'sku': 'BOOK-PP20',
                'description': 'Classic programming book by David Thomas and Andrew Hunt.',
                'price': Decimal('49.99'),
                'stock': 80,
                'status': ProductStatus.ACTIVE,
                'category': categories.get('Books'),
            },
            {
                'name': 'Discontinued Widget',
                'sku': 'MISC-DW01',
                'description': 'A product that has been discontinued.',
                'price': Decimal('9.99'),
                'stock': 0,
                'status': ProductStatus.INACTIVE,
                'category': None,
            },
        ]

        for product_data in products:
            _, was_created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults=product_data,
            )
            if was_created:
                self.stdout.write(f'  Created product: {product_data["name"]}')
            else:
                self.stdout.write(f'  Product "{product_data["name"]}" already exists, skipping.')

    def _create_customer_user(self) -> User:
        email = 'customer@example.com'
        user, was_created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
            }
        )
        if was_created:
            user.set_password('customerpassword123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created customer user: {email}'))
        else:
            self.stdout.write(f'Customer user "{email}" already exists, skipping.')
        return user

    def _create_sample_orders(self, customer: User):

        if Order.objects.filter(user=customer).exists():
            self.stdout.write('  Sample orders already exist, skipping.')
            return

        try:
            macbook = Product.objects.get(sku='LAPTOP-MBP16')
            hub = Product.objects.get(sku='ACC-USBC10')
            iphone = Product.objects.get(sku='PHONE-IP16PRO')
            airpods = Product.objects.get(sku='ACC-APP3')
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR('  Required products for orders not found, skipping.'))
            return

        # Order 1: Pending
        order1 = order_create(
            user=customer,
            items=[
                {'product_id': macbook.id, 'quantity': 1},
                {'product_id': hub.id, 'quantity': 2},
            ]
        )
        self.stdout.write(self.style.SUCCESS(f'  Created pending Order #{order1.id}'))

        # Order 2: Paid (and stock reduced)
        order2 = order_create(
            user=customer,
            items=[
                {'product_id': iphone.id, 'quantity': 1},
                {'product_id': airpods.id, 'quantity': 1},
            ]
        )
        order_mark_paid(order=order2)
        self.stdout.write(self.style.SUCCESS(f'  Created paid Order #{order2.id} (Stock reduced)'))


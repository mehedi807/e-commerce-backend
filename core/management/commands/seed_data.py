from decimal import Decimal

from django.core.management.base import BaseCommand

from authentication.models import User
from products.models import Category, Product
from products.constants import ProductStatus


class Command(BaseCommand):
    help = 'Seed admin user, categories, and sample products.'

    def handle(self, *args, **options):
        self._create_admin_user()
        categories = self._create_categories()
        self._create_products(categories)
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
                    defaults={'parent': parent},
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

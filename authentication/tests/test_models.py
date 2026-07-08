from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from authentication.models import User


class UserManagerTests(TestCase):
    """Tests for UserManager.create_user and create_superuser."""

    def test_create_user_success(self):
        user = User.objects.create_user(
            email='alice.vance@shop.com',
            password='P@ssw0rd123!',
            first_name='Alice',
            last_name='Vance',
        )

        self.assertEqual(user.email, 'alice.vance@shop.com')
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.last_name, 'Vance')
        self.assertTrue(user.check_password('P@ssw0rd123!'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_normalizes_email(self):
        """Email normalization should only lowercase the domain portion of the address."""
        user = User.objects.create_user(
            email='Alice@SHOP.COM',
            password='P@ssw0rd123!',
            first_name='Alice',
            last_name='Vance',
        )

        self.assertEqual(user.email, 'Alice@shop.com')

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                password='P@ssw0rd123!',
                first_name='Alice',
                last_name='Vance',
            )

    def test_create_user_duplicate_email_raises(self):
        User.objects.create_user(
            email='duplicate.customer@shop.com',
            password='ValidPassword1!',
            first_name='First',
            last_name='Customer',
        )

        with self.assertRaises(ValidationError):
            User.objects.create_user(
                email='duplicate.customer@shop.com',
                password='AnotherPassword2!',
                first_name='Second',
                last_name='Customer',
            )

    def test_create_superuser_success(self):
        admin = User.objects.create_superuser(
            email='admin.security@shop.com',
            password='AdminSecurePass199!',
            first_name='Admin',
            last_name='Manager',
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_create_superuser_not_staff_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='invalid.admin@shop.com',
                password='AdminSecurePass199!',
                first_name='Invalid',
                last_name='Staff',
                is_staff=False,
            )

    def test_create_superuser_not_superuser_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='invalid.admin@shop.com',
                password='AdminSecurePass199!',
                first_name='Invalid',
                last_name='Staff',
                is_superuser=False,
            )


class UserModelTests(TestCase):
    """Tests for the User model fields, constraints, and behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='shop.customer@shop.com',
            password='CustomerPass123!',
            first_name='Shop',
            last_name='Customer',
        )

    def test_str_returns_email(self):
        self.assertEqual(str(self.user), 'shop.customer@shop.com')

    def test_ordering_by_created_at_desc(self):
        user2 = User.objects.create_user(
            email='new.registrant@shop.com',
            password='CustomerPass123!',
            first_name='New',
            last_name='Registrant',
        )
        users = list(User.objects.all())
        self.assertEqual(users, [user2, self.user])

    def test_has_created_at_timestamp(self):
        self.assertIsNotNone(self.user.created_at)

    def test_has_updated_at_timestamp(self):
        self.assertIsNotNone(self.user.updated_at)

    def test_default_is_active_true(self):
        self.assertTrue(self.user.is_active)

    def test_default_is_staff_false(self):
        self.assertFalse(self.user.is_staff)

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_required_fields(self):
        self.assertEqual(User.REQUIRED_FIELDS, ['first_name', 'last_name'])

    def test_password_is_hashed(self):
        self.assertNotEqual(self.user.password, 'CustomerPass123!')

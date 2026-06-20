from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from expense_app.admin import ExpenseAdmin, CategoryAdmin
from expense_app.models import Expense, Category
from django.db import transaction
from django.db.models import ProtectedError

class AdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )
        self.client.force_login(self.admin_user)

    def test_expense_admin_display(self):
        ma = ExpenseAdmin(Expense, self.site)
        self.assertIn('amount', ma.list_display)
        self.assertIn('category', ma.list_display)
        self.assertIn('date', ma.list_display)
        self.assertIn('user', ma.list_display)

    def test_category_admin_display(self):
        ma = CategoryAdmin(Category, self.site)
        self.assertIn('name', ma.list_display)

    def test_category_delete_restriction(self):
        self.test_category_delete_restriction_model_level()

    def test_category_delete_restriction_model_level(self):
        category = Category.objects.create(name='Test Category')
        expense = Expense.objects.create(
            user=self.admin_user,
            amount=100,
            category=category,
            date='2024-01-15'
        )
        try:
            with transaction.atomic():
                category.delete()
            self.fail("Категория была удалена, хотя должна быть защищена")
        except ProtectedError:
            pass
        self.assertTrue(Category.objects.filter(id=category.id).exists())

    def test_expense_admin_filtering(self):
        ma = ExpenseAdmin(Expense, self.site)
        self.assertIn('category', ma.list_filter)
        self.assertIn('date', ma.list_filter)
        self.assertIn('user', ma.list_filter)
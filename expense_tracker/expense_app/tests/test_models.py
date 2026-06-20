from django.test import TestCase
from django.contrib.auth.models import User
from expense_app.models import Expense, Category, Tag, ExpenseTemplate

class ExpenseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.category = Category.objects.create(name='Продукты')
        self.tag = Tag.objects.create(name='Супермаркет')
        
    def test_expense_creation(self):
        expense = Expense.objects.create(
            user=self.user,
            amount=1000,
            category=self.category,
            date='2024-01-15',
            description='Покупка продуктов'
        )
        expense.tags.add(self.tag)
        self.assertEqual(expense.amount, 1000)
        self.assertEqual(expense.category.name, 'Продукты')
        self.assertIn(self.tag, expense.tags.all())
        
    def test_expense_string_representation(self):
        expense = Expense.objects.create(
            user=self.user,
            amount=500,
            category=self.category,
            date='2024-01-20'
        )
        expected_str = f'Расход {expense.id}: 500 руб. - Продукты'
        self.assertEqual(str(expense), expected_str)
        
class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(name='Транспорт')
        self.assertEqual(category.name, 'Транспорт')
        self.assertEqual(str(category), 'Транспорт')
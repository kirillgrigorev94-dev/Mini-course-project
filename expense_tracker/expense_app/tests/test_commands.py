from django.core.management import call_command
from django.test import TestCase
from django.conf import settings
import os
from expense_app.models import Expense, User, Category
from io import StringIO
from datetime import date

class ExportExpensesCommandTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        # Создаём категорию
        category = Category.objects.create(name='Продукты')
        Expense.objects.create(
            user=self.user,
            amount=1000,
            category=category,
            date='2024-01-01'
        )

    def test_export_without_monthly(self):
        call_command('export_expenses_to_csv')
        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports', 'csv')
        os.makedirs(export_dir, exist_ok=True)
        today = date.today().strftime('%Y%m%d')
        expected_file = f'Расходы_{self.user.username}_{today}.csv'
        filepath = os.path.join(export_dir, expected_file)
        self.assertTrue(os.path.exists(filepath))

    def test_export_with_monthly(self):
        call_command('export_expenses_to_csv', '--monthly')
        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports', 'csv')
        os.makedirs(export_dir, exist_ok=True)
        today = date.today().strftime('%Y%m%d')
        expected_file = f'Расходы_ежемесячные_{self.user.username}_{today}.csv'
        filepath = os.path.join(export_dir, expected_file)
        self.assertTrue(os.path.exists(filepath))

class GenerateStatisticsCommandTest(TestCase):
    def test_generate_statistics(self):
        out = StringIO()
        call_command('generate_statistics', stdout=out)
        output = out.getvalue()
        self.assertIn('Статистика сгенерирована', output)
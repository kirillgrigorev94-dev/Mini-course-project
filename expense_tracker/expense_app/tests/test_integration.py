import os
from django.conf import settings
from datetime import date
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from expense_app.models import Expense, ExpenseTemplate, Category, User

class ExpenseIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.category = Category.objects.create(name='Продукты')
        self.client.login(username='testuser', password='testpass')

    def test_full_expense_workflow(self):
        # 1. Создание шаблона расхода
        template_data = {
            'name': 'Еженедельная покупка',
            'amount': 2000,
            'category': self.category.id,
            'description': 'Продукты на неделю'
        }
        response = self.client.post(reverse('create_expense_template'), template_data)
        self.assertEqual(response.status_code, 302)
        template = ExpenseTemplate.objects.get(name='Еженедельная покупка')

        # 2. Использование шаблона для создания расхода
        response = self.client.get(reverse('add_expense_from_template', args=[template.id]))
        self.assertEqual(response.status_code, 200)

        # 3. Добавление расхода через шаблон
        expense_data = {
            'amount': 2000,
            'category': self.category.id,
            'date': '2024-01-25',
            'description': 'Покупка по шаблону'
        }
        response = self.client.post(reverse('add_expense'), expense_data)
        self.assertEqual(response.status_code, 302)

        # 4. Проверка в списке расходов
        response = self.client.get(reverse('expenses_list'))
        self.assertEqual(response.status_code, 200)

        # Основной чек: проверяем данные в контексте
        if 'expenses' in response.context:
            expenses = response.context['expenses']
            self.assertTrue(any(e.description == 'Покупка по шаблону' for e in expenses))
            self.assertTrue(any(e.amount == 2000 for e in expenses))
        else:
            # Резервный чек: ищем сумму и категорию в HTML
            self.assertContains(response, '2000')
            self.assertContains(response, 'Продукты')

        # 5. Фильтрация
        response = self.client.get(f'{reverse("expenses_list")}?min_amount=1500')
        self.assertContains(response, '2000')

    def test_export_workflow(self):
        # Создаём несколько расходов
        Expense.objects.create(
            user=self.user,
            amount=1000,
            category=self.category,
            date='2024-01-10'
        )
        Expense.objects.create(
            user=self.user,
            amount=500,
            category=self.category,
            date='2024-01-15'
        )

        # Запускаем команду экспорта
        call_command('export_expenses_to_csv', '--monthly')

        # Проверяем, что файл создан
        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports', 'csv')
        today = date.today().strftime('%Y%m%d')
        expected_file = f'расходы_{self.user.username}_{today}.csv'
        filepath = os.path.join(export_dir, expected_file)
        self.assertTrue(os.path.exists(filepath))
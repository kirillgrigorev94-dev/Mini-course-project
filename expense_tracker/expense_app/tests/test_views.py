from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from expense_app.models import Expense, Category

class ExpensesViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.category = Category.objects.create(name='Развлечения')
        self.client.login(username='testuser', password='testpass')

    def test_expenses_list_view(self):
        response = self.client.get(reverse('expenses_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expense_app/expenses_list.html')

    def test_add_expense_view(self):
        response = self.client.get(reverse('add_expense'))
        self.assertEqual(response.status_code, 200)

    def test_add_expense_post(self):
        data = {
            'amount': 500,
            'category': self.category.id,
            'date': '2024-01-20',
            'description': 'Тест через форму'
        }
        response = self.client.post(reverse('add_expense'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(amount=500).exists())

    def test_edit_expense_view(self):
        expense = Expense.objects.create(
            user=self.user,
            amount=300,
            category=self.category,
            date='2024-01-25'
        )
        response = self.client.get(reverse('edit_expense', args=[expense.id]))
        self.assertEqual(response.status_code, 200)

    def test_delete_expense_view(self):
        expense = Expense.objects.create(
            user=self.user,
            amount=400,
            category=self.category,
            date='2024-01-26'
        )
        response = self.client.post(reverse('delete_expense', args=[expense.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Expense.objects.filter(id=expense.id).exists())
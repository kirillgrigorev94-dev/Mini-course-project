from django.test import TestCase
from expense_app.forms import ExpenseForm
from expense_app.models import Category

class ExpenseFormTest(TestCase):
    def setUp(self):
        # Создаём категорию для тестов
        self.category = Category.objects.create(name='Продукты')

    def test_form_with_valid_data(self):
        form_data = {
            'amount': 1000,
            'category': self.category.id,
            'date': '2024-01-15',
            'description': 'Покупка продуктов'
        }
        form = ExpenseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_with_negative_amount(self):
        form_data = {
            'amount': -100,  # Отрицательная сумма
            'category': self.category.id,
            'date': '2024-01-15'
        }
        form = ExpenseForm(data=form_data)
        self.assertFalse(form.is_valid())  # Форма должна быть невалидной
        self.assertIn('amount', form.errors)  # Ошибка должна быть в поле amount

        self.assertEqual(
            form.errors['amount'][0],
            'Сумма не может быть отрицательной.'
        )

    def test_form_with_empty_data(self):
        form = ExpenseForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)  # Ожидаем 3 ошибки
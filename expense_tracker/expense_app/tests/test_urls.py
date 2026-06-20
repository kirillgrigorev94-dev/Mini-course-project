from django.test import SimpleTestCase
from django.urls import reverse, resolve
from expense_app.views import (
    expenses_list,
    add_expense,
    edit_expense,
    delete_expense,
    expense_templates_list,
    create_expense_template,
    edit_expense_template,
    delete_expense_template
)

class UrlsTest(SimpleTestCase):
    def test_expenses_list_url_resolves(self):
        url = reverse('expenses_list')
        self.assertEqual(url, '/expenses/')
        resolver = resolve('/expenses/')
        self.assertEqual(resolver.func, expenses_list)

    def test_add_expense_url_resolves(self):
        url = reverse('add_expense')
        self.assertEqual(url, '/add_expense/')
        resolver = resolve('/add_expense/')
        self.assertEqual(resolver.func, add_expense)

    def test_edit_expense_url_resolves(self):
        url = reverse('edit_expense', args=[1])
        self.assertEqual(url, '/edit_expense/1/')
        resolver = resolve('/edit_expense/1/')
        self.assertEqual(resolver.func, edit_expense)
        self.assertEqual(resolver.kwargs['pk'], 1)

    def test_delete_expense_url_resolves(self):
        url = reverse('delete_expense', args=[1])
        self.assertEqual(url, '/delete_expense/1/')
        resolver = resolve('/delete_expense/1/')
        self.assertEqual(resolver.func, delete_expense)
        self.assertEqual(resolver.kwargs['pk'], 1)
    def test_templates_list_url_resolves(self):
        url = reverse('expense_templates_list')
        self.assertEqual(url, '/templates/')
        resolver = resolve('/templates/')
        self.assertEqual(resolver.func, expense_templates_list)
    def test_create_expense_template_url_resolves(self):
        url = reverse('create_expense_template')
        self.assertEqual(url, '/templates/create/')
        resolver = resolve('/templates/create/')
        self.assertEqual(resolver.func, create_expense_template)
    def test_edit_expense_template_url_resolves(self):
        url = reverse('edit_expense_template', args=[1])
        self.assertEqual(url, '/templates/edit/1/')
        resolver = resolve('/templates/edit/1/')
        self.assertEqual(resolver.func, edit_expense_template)
        self.assertEqual(resolver.kwargs['pk'], 1)
    def test_delete_expense_template_url_resolves(self):
        url = reverse('delete_expense_template', args=[1])
        self.assertEqual(url, '/templates/delete/1/')
        resolver = resolve('/templates/delete/1/')
        self.assertEqual(resolver.func, delete_expense_template)
        self.assertEqual(resolver.kwargs['pk'], 1)
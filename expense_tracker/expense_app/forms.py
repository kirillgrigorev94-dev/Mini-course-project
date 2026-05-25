from django import forms
from .models import Expense

# Форма для добавления/редактирования расходов на основе модели Expense
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense  # Указываем модель, к которой привязана форма
        fields = ['amount', 'category', 'date', 'description']  # Перечисляем поля модели, которые будут отображаться в форме

        widgets = {
            # Настраиваем виджет для поля 'date': используем HTML5‑виджет выбора даты
            'date': forms.DateInput(attrs={'type': 'date'}),
            # Настраиваем виджет для поля 'description': текстовая область с высотой в 3 строки
            'description': forms.Textarea(attrs={'rows': 3}),
        }
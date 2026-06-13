from django import forms
from .models import Expense, Tag

# Форма для добавления/редактирования расходов на основе модели Expense
class ExpenseForm(forms.ModelForm):
    """
    Форма для добавления и редактирования расходов.
    
    Основана на модели 'Expense', включает поле выбора тегов в виде чекбоксов.

    Поля:
        amount (DecimalField): Сумма расходов.
        category (ForeignKey): Категория расхода.
        date (DateField): Дата расхода (виджет - HTML5-выбор даты).
        description (TextField): Комментарий к расходу (текстовая область, 3 строки).
        tags (ModelMultipleChoiceField): Теги расхода (множественный выбор, чекбоксы).
        
    Виджеты:
        'date': HTML5-виджет выбора даты.
        'description': Текстовая область с высотой 3 строки.
        
    """
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Теги'
    )
    
    class Meta:
        model = Expense  # Указываем модель, к которой привязана форма
        fields = ['amount', 'category', 'date', 'description', 'tags']  # Перечисляем поля модели, которые будут отображаться в форме

        widgets = {
            # Настраиваем виджет для поля 'date': используем HTML5‑виджет выбора даты
            'date': forms.DateInput(attrs={'type': 'date'}),
            # Настраиваем виджет для поля 'description': текстовая область с высотой в 3 строки
            'description': forms.Textarea(attrs={'rows': 3}),
        }
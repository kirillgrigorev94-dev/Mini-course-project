from django import forms
from .models import Expense, Tag, ExpenseTemplate, get_category_spent_this_month

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
            'amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            # Настраиваем виджет для поля 'date': используем HTML5‑виджет выбора даты
            'date': forms.DateInput(attrs={'type': 'date'}),
            # Настраиваем виджет для поля 'description': текстовая область с высотой в 3 строки
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        # Извлекаем user из kwargs, если передан
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount < 0:
            raise forms.ValidationError('Сумма не может быть отрицательной.')
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        category = cleaned_data.get('category')

        # Теперь self.user доступен благодаря __init__
        if not self.user or not category or amount is None:
            return cleaned_data

        limit = category.monthly_limit
        if not limit:
            return cleaned_data

        # Считаем уже потраченное за месяц
        spent_before = get_category_spent_this_month(self.user, category)

        # Если это редактирование существующего расхода, вычитаем его старую сумму
        if self.instance and self.instance.pk:
            spent_before -= self.instance.amount

        new_total = spent_before + amount

        if new_total > limit:
            self.add_error(
                'amount',
                f'Превышение месячного лимита категории "{category.name}": '
                f'лимит {limit} руб., уже потрачено {spent_before} руб. '
                f'(с учётом этого расхода будет {new_total} руб.).'
            )

        return cleaned_data
        
class ExpenseTemplateForm(forms.ModelForm):
    """
    Форма для создания и редактирования шаблонов расходов (ExpenseTemplate).
    
    Включает поле множественного выбора тегов с чекбоксами и текстовое поле
    
    Описание с высотой в 3 строки.
    """
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Теги'
    )
    
    class Meta:
        model = ExpenseTemplate
        fields = ['name', 'amount', 'category', 'description', 'tags']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount < 0:
            raise forms.ValidationError('Сумма в шаблоне не может быть отрицательной.')
        return amount
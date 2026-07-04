# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from datetime import date

# Модель категории расходов
class Category(models.Model):
    # Название категории (до 100 символов)
    name = models.CharField(max_length=100, verbose_name='Название категории')
    monthly_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Месячный лимит (руб.)'
    )

    def __str__(self):
        # Возвращает название категории при выводе объекта
        return self.name

# Модель тегов    
class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название тега')
    
    def __str__(self):
        return self.name

# Модель расхода
class Expense(models.Model):
    # Связь с пользователем (при удалении пользователя удаляются и его расходы)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    # Сумма расхода (максимум 10 цифр, 2 после запятой)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    # Связь с категорией (удаление категории запрещено, если есть связанные расходы)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория')
    # Дата расхода
    date = models.DateField(verbose_name='Дата')
    description = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    # Связь с тегом многие ко многим
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='Теги')
    
    def clean(self):
        super().clean()
        if self.amount is not None and self.amount < 0:
            raise ValidationError({'amount': 'Сумма не может быть отрицательной.'})

    class Meta:
        # Сортировка расходов по дате (новые сверху)
        ordering = ['-date']

    def __str__(self):
        # Строковое представление расхода: сумма и название категории
        return f'Расход {self.id}: {self.amount} руб. - {self.category.name}'
    
class ExpenseTemplate(models.Model):
    """
    Модель шаблона расхода.
    
    Хранит предопределённые настройки для быстрого создания записей о расходах.
    
    Поля:
        - user: пользователь, которому принадлежит шаблон;
        - name: название шаблона;
        - amount: сумма расхода;
        - category: категория расхода;
        - description: комментарий к шаблону;
        - tags: теги, связанные с шаблоном;
        - created_at: дата и время создания шаблона.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    name = models.CharField(max_length=100, verbose_name='Название шаблона')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория')
    description = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='Теги')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount < 0:
            raise ValidationError({'amount': 'Сумма не может быть отрицательной.'})

    def __str__(self):
        return self.name
    
def get_category_spent_this_month(user, category):
    """
    Возвращает сумму расходов пользователя за текущий календарный месяц
    по данной категории: с 1-го числа по сегодня включительно.
    """
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    result = Expense.objects.filter(
        user=user,
        category=category,
        date__gte=first_day_of_month,
        date__lte=today,
    ).aggregate(total=Sum('amount'))['total']

    return result if result is not None else 0
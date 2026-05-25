from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

# Модель категории расходов
class Category(models.Model):
    # Название категории (до 100 символов)
    name = models.CharField(max_length=100, verbose_name='Название категории')

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

    class Meta:
        # Сортировка расходов по дате (новые сверху)
        ordering = ['-date']

    def __str__(self):
        # Строковое представление расхода: сумма и название категории
        return f'{self.amount} руб. - {self.category.name}'
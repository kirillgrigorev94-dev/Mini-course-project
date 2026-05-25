from django.contrib import admin
from .models import Category, Expense, Tag

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 20

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление категорий, если они связаны с расходами
        if obj and Expense.objects.filter(category=obj).exists():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'category', 'date', 'description', 'get_tags')
    list_filter = ('category', 'date', 'user', 'tags')
    search_fields = ('description', 'category__name', 'tags_name')
    date_hierarchy = 'date'
    list_per_page = 25

    # Настройка полей формы в админке
    fieldsets = (
        (None, {
            'fields': ('user', 'amount')
        }),
        ('Детали расхода', {
            'fields': ('category', 'date', 'description', 'tags'),
            'classes': ('collapse',)
        }),
    )

    # Оптимизация запросов к БД
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category')

    # Кастомное отображение суммы
    def amount_formatted(self, obj):
        return f'{obj.amount} руб.'
    amount_formatted.short_description = 'Сумма'
    
    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = 'Теги'

    # Добавляем колонку с форматированной суммой в список
    list_display += ('amount_formatted',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
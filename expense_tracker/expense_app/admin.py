from django.contrib import admin
from .models import Category, Expense, Tag, ExpenseTemplate

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Кастомная админ-панель для модели 'Category'.
    
    Особенности:
        - Запрещает удаление категорий, связанных с расходами.
        - Предоставляет поиск по названию категории.
        - Ограничивает количество отображаемых записей на странице.

    Атрибуты:
        list_display (tuple): Поля, отображаемые в списке объектов.
        search_fields (tuple): Поля для поиска.
        list_per_page (int): Количество записей на одной странице 
        
    Методы:
        has_delete_permission(request, obj): Проверяет, можно ли удалить категорию.
    
    """
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
    
    def save_model(self, request, obj, form, change):
        # Вызываем валидацию модели перед сохранением
        obj.full_clean() # запустит метод clean()
        super().save_model(request, obj, form, change)

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
    
@admin.register(ExpenseTemplate)
class ExpenseTemplateAdmin(admin.ModelAdmin):
    """Административный интерфейс для управления шаблонами расходов."""
    
    list_display = ('name', 'user', 'amount', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    fieldsets = (
        ('Основная информация', {'fields': ('user', 'name')}),
        ('Детали расхода', {'fields': ('amount', 'category', 'description')}),
        ('Теги', {'fields': ('tags',), 'classes': ('collapse',)}),
    )
    
    def save_model(self, request, obj, form, change):
        # Вызываем валидацию модели перед сохранением
        obj.full_clean() # запустит метод clean()
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Ограничивает видимость объектов: суперпользователи видят все, обычные — только свои.

        Args:
            request: HTTP‑запрос.

        Returns:
            QuerySet: отфильтрованный набор объектов ExpenseTemplate.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def has_change_permission(self, request, obj = None):
        """
        Проверяет право пользователя на изменение объекта.

        Суперпользователи могут изменять любые объекты, обычные пользователи —
        только принадлежащие им.

        Args:
            request: HTTP‑запрос.
            obj: объект ExpenseTemplate для изменения (может быть None).

        Returns:
            bool: True, если изменение разрешено, иначе False.
        """
        
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj = None):
        """
        Проверяет право пользователя на удаление объекта.

        Суперпользователи могут удалять любые объекты, обычные пользователи —
        только принадлежащие им.

        Args:
            request: HTTP‑запрос.
            obj: объект ExpenseTemplate для удаления (может быть None).

        Returns:
            bool: True, если удаление разрешено, иначе False.
        """
        
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_delete_permission(request, obj)
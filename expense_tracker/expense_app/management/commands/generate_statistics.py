from django.core.management.base import BaseCommand
from django.conf import settings
from expense_app.models import Expense, Category
from django.db.models import Sum
from datetime import date, timedelta
import os
import csv

class Command(BaseCommand):
    help = 'Генерация отчёта статистики в CSV файл (сохраняется в expense_tracker/exports/csv)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--weekly',
            action='store_true',
            help='Статистика за последнюю неделю (по умолчанию - за всё время)',
        )

    def handle(self, *args, **options):
        # 1. Определяем даты
        end_date = date.today()
        if options['weekly']:
            start_date = end_date - timedelta(days=7)
            report_type = "weekly"
            self.stdout.write(self.style.SUCCESS('Генерация недельной статистики...'))
        else:
            start_date = None
            report_type = "all_time"
            self.stdout.write(self.style.SUCCESS('Генерация общей статистики...'))

        # 2. Получаем данные по категориям
        categories = Category.objects.all()
        csv_data = []
        # Заголовок CSV
        csv_data.append(['Категория', 'Потрачено (руб)', 'Дата начала', 'Дата конца', 'Тип отчёта'])

        for category in categories:
            qs = Expense.objects.filter(category=category)
            
            if start_date:
                qs = qs.filter(date__gte=start_date, date__lte=end_date)
            
            total = qs.aggregate(total=Sum('amount'))['total'] or 0
            
            csv_data.append([
                category.name,
                total,
                start_date.strftime('%Y-%m-%d') if start_date else 'Начало времён',
                end_date.strftime('%Y-%m-%d'),
                report_type
            ])

        # 3. ОПРЕДЕЛЕНИЕ ПУТИ СОХРАНЕНИЯ
        # Находим папку, где лежит manage.py (корень проекта expense_tracker)
        # __file__ указывает на этот скрипт (generate_statistics.py)
        # .. -> expense_app, .. -> expense_tracker (корень)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Формируем путь: expense_tracker/exports/csv
        export_folder = os.path.join(project_root, 'exports', 'csv')
        
        # Создаем папки, если их нет
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)
            self.stdout.write(self.style.WARNING(f'Папка создана: {export_folder}'))

        # Имя файла с датой
        timestamp = end_date.strftime('%Y%m%d')
        filename = f"Расходы_статистика_{report_type}_{timestamp}.csv"
        filepath = os.path.join(export_folder, filename)

        # 4. Запись файла
        try:
            # Используем utf-8-sig, чтобы Excel корректно открывал кириллицу
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Статистика успешно сохранена: {filepath}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при сохранении файла: {e}'))
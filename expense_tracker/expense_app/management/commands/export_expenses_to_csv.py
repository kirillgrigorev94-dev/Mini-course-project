from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from expense_app.views import get_filtered_expenses, generate_expense_csv_content
from datetime import date
import os
from django.conf import settings

class Command(BaseCommand):
    """
    Команда Django management для экспорта расходов всех пользователей в CSV-формат.
    
    Позволяет экспортировать расходы с опциональной фильтрацией за последний месяц.
    
    Атрибуты:
        help (str): Описание команды для справки (`python manage.py help`).

    Методы:
        add_arguments(parser): Добавляет аргументы командной строки.
        handle(*args, **options): Основная ллогика выполнения команды.
        create_fake_request(user, options): Создаёт фиктивный HTTP-запрос для фильтрации данных.
        
    """
    help = 'Экспорт расходов всех пользователей в CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--monthly',
            action='store_true',
            help='Экспорт за последний месяц',
        )

    def handle(self, *args, **options):
        # Папка для экспорта
        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports', 'csv')
        os.makedirs(export_dir, exist_ok=True)

        users = User.objects.all()
        for user in users:
            fake_request = self.create_fake_request(user, options)
            expenses = get_filtered_expenses(user, fake_request)

            # Генерируем CSV
            csv_content = generate_expense_csv_content(expenses)

            # Сохраняем на диск
            today = date.today().strftime('%Y%m%d')
            if options['monthly']:
                filename = f"Расходы_ежемесячные_{user.username}_{today}.csv"
            else:
                filename = f"Расходы_{user.username}_{today}.csv"
            
            filepath = os.path.join(export_dir, filename)

            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                f.write(csv_content)
            self.stdout.write(self.style.SUCCESS(f'Сохранён: {filepath}'))

    def create_fake_request(self, user, options):
        """Создаёт фиктивный request с учётом опций команды"""
        class FakeRequest:
            def __init__(self, user, is_monthly):
                self.user = user
                self.GET = {}
                if is_monthly:
                    # Фильтр для ежемесячного экспорта
                    self.GET['date__gte'] = date(date.today().year, date.today().month, 1)
        return FakeRequest(user, options.get('monthly', False))
from django.core.management.base import BaseCommand
from ... import statistics  # Импорт вашей функции статистики

class Command(BaseCommand):
    help = 'Генерация отчёта статистики'

    def add_arguments(self, parser):
        parser.add_argument(
            '--weekly',
            action='store_true',
            help='Статистика за последнюю неделю',
        )

    def handle(self, *args, **options):
        # Логика генерации статистики
        self.stdout.write(self.style.SUCCESS('Статистика сгенерирована'))
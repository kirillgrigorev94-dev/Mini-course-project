import schedule
import time
from datetime import datetime
import logging
from django.core.management import call_command
from django.conf import settings
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def export_monthly_report():
    """Функция для ежемесячного экспорта расходов в CSV"""
    try:
        logger.info("Запуск ежемесячного экспорта отчётов")
        call_command('export_expenses_to_csv', '--monthly')
        logger.info("Ежемесячный экспорт выполнен успешно")
    except Exception as e:
        logger.error(f"Ошибка при экспорте: {e}")

def generate_statistics_report():
    """Функция для еженедельной генерации статистики"""
    try:
        logger.info("Генерация недельного отчёта статистики")
        call_command('generate_statistics', '--weekly')
        logger.info("Недельный отчёт статистики сгенерирован")
    except Exception as e:
        logger.error(f"Ошибка генерации статистики: {e}")

def cleanup_old_data():
    """Очистка старых временных файлов"""
    try:
        logger.info("Очистка старых данных")
        # Пример: удаление файлов старше 30 дней
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                # Логика удаления старых файлов
        logger.info("Очистка завершена")
    except Exception as e:
        logger.error(f"Ошибка очистки данных: {e}")

def run_scheduler():
    """Запуск планировщика"""
    # Ежемесячный экспорт 1‑го числа в 09:00
    schedule.every().month.on(1).at("09:00").do(export_monthly_report)

    # Еженедельный отчёт по статистике по понедельникам в 10:00
    schedule.every().monday.at("10:00").do(generate_statistics_report)

    # Ежедневная очистка в 02:00
    schedule.every().day.at("02:00").do(cleanup_old_data)
    
    # Тестовый интервал: каждые 2 минуты
    # schedule.every(2).minutes.do(export_monthly_report)

    # Тестовая задача каждую минуту (для отладки)
    schedule.every(1).minutes.do(lambda: logger.info("Тестовая задача выполнена"))

    logger.info("Планировщик запущен. Ожидание задач...")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту
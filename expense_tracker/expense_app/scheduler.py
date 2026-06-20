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
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def export_monthly_report():
    """
    Запоскает ежемесячный экспорт расходов в CSV через Django management command.
    
    Выполняется только 1-го числа каждого месяца в 09:00.
    
    Логирует:
        - начало выполнения задачи;
        - успешное завершение;
        - ошибки (если возникли).
        
    Использует:
        'Django.core.management.call_command' для вызова команды 'export_expenses_to_csv --monthly'.
        'logging' для записи событий в файл 'scheduler.log' и консоль.
        
    Raises:
        Exception: Логируется как ошибка с описанием проблемы.
    
    """
    today = datetime.now().date()
    if today.day == 1:
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
        
def run_every_two_minutes():
    """Задача, выполняемая каждые 2 минуты."""
    try:
        logger.info("Запуск задачи каждые 2 минуты")
        # Здесь можно вызвать существующую команду или добавить свою логику
        call_command('export_expenses_to_csv') # Пример вызова существующей команды
        logger.info("Задача каждые 2 минуты выполнена успешно")
    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи каждые 2 минуты: {e}")

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
    # Ежемесячный экспорт - запускается ежедневно, но выполняется 1‑го числа
    schedule.every().day.at("09:00").do(export_monthly_report)

    # Еженедельный отчёт по статистике по понедельникам в 10:00
    schedule.every().monday.at("10:00").do(generate_statistics_report)

    # Ежедневная очистка в 23:00
    schedule.every().day.at("23:00").do(cleanup_old_data)
    
    # Тестовый интервал: каждые 2 минуты
    # schedule.every(2).minutes.do(run_every_two_minutes)

    # Тестовая задача каждую минуту (для отладки)
    # schedule.every(1).minutes.do(lambda: logger.info("Тестовая задача выполнена"))

    logger.info("Планировщик запущен. Ожидание задач...")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту
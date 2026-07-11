Expense accounting system
Your expenses will be located here.
What you will receive after registration:
Complete control over your expenses
Visual statistics in graph form
Data export option
Convenient interface for daily use

Технологии
Python (3.10+)
Django (4.2+)
Bootstrap 5 (CSS/JS)
HTML5, CSS3, JavaScript
CSV (экспорт данных)
Matplotlib/Pandas (генерация графиков для статистики)

Создание и активация виртуального окружения

python -m venv myenv
myenv\Scripts\activate

Установка зависимостей


pip install -r requirements.txt

Миграции и создание суперпользователя

python manage.py migrate
python manage.py createsuperuser

Запуск сервера разработки

python manage.py runserver
Открой в браузере: http://127.0.0.1:8000/
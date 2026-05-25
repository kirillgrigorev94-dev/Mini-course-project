from django.urls import path
from . import views

# Список маршрутов (URL‑паттернов) для приложения учёта расходов
urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    # Список расходов пользователя
    path('expenses/', views.expenses_list, name='expenses_list'),
    # Добавление нового расхода
    path('add/', views.add_expense, name='add_expense'),
    # Редактирование расхода (по pk)
    path('edit/<int:pk>/', views.edit_expense, name='edit_expense'),
    # Удаление расхода (по pk)
    path('delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    # Статистика расходов с графиком
    path('statistics/', views.statistics, name='statistics'),
    # Экспорт в CSV (старый endpoint)
    path('export-to-csv/', views.export_to_csv, name='export_to_csv'),
    # Новый маршрут для экспорта в PDF
    path('export-to-pdf/', views.export_to_pdf, name='export_to_pdf'),
    # Страница авторизации
    path('login/', views.user_login, name='login'),
    # Выход из системы
    path('logout/', views.user_logout, name='logout'),
    # Скачивание CSV с расходами
    path('download-csv/', views.download_csv, name='download_csv'),
]
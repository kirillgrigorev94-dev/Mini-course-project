import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Используем неинтерактивный бэкенд для серверной среды
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from .models import Expense, Category
from .forms import ExpenseForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import csv
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.colors import CMYKColor

def get_filtered_expenses(user, request):
    """Получает отфильтрованные расходы пользователя"""
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    keyword = request.GET.get('keyword')

    expenses = Expense.objects.filter(user=user)

    if min_amount:
        try:
            min_amount = float(min_amount)
            expenses = expenses.filter(amount__gte=min_amount)
        except ValueError:
            pass
    if max_amount:
        try:
            max_amount = float(max_amount)
            expenses = expenses.filter(amount__lte=max_amount)
        except ValueError:
            pass
    if keyword:
        expenses = expenses.filter(description__icontains=keyword)

    return expenses

# Главная страница приложения (доступна только авторизованным пользователям)
def index(request):
    return render(request, 'expense_app/index.html')

# Отображение списка расходов текущего пользователя
@login_required
def expenses_list(request):
    export_format = request.GET.get('export')

    # Получаем отфильтрованные расходы
    expenses = get_filtered_expenses(request.user, request)

    if export_format == 'csv':
        return export_to_csv(request)
    elif export_format == 'pdf':
        return export_to_pdf(request, expenses)

    context = {
        'expenses': expenses,
        'min_amount': request.GET.get('min_amount'),
        'max_amount': request.GET.get('max_amount'),
        'keyword': request.GET.get('keyword'),
    }
    return render(request, 'expense_app/expenses_list.html', context)

# Экспорт расходов в CSV-файл
@login_required
def export_to_csv(request):
    """Экспорт расходов в CSV-файл"""
    # Получаем отфильтрованные расходы
    expenses = get_filtered_expenses(request.user, request)

    # Создаём HTTP‑ответ с правильным content-type
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="расходы.csv"'

    # Настраиваем кодировку для корректного отображения кириллицы
    response.write('\ufeff'.encode('utf-8'))  # BOM для Excel

    writer = csv.writer(response)

    # Записываем заголовок CSV
    writer.writerow(['Дата', 'Категория', 'Сумма (руб.)', 'Комментарий'])

    # Записываем данные расходов
    for expense in expenses:
        writer.writerow([
            expense.date.strftime('%d.%m.%Y'),
            expense.category.name,
            str(expense.amount),
            expense.description
        ])

    return response

@login_required
def export_to_pdf(request, expenses):
    """Экспорт расходов в PDF-файл с улучшенным форматированием и корректной таблицей"""

    try:
        # Регистрируем шрифт для поддержки кириллицы
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSansBold', 'DejaVuSans-Bold.ttf'))

        # Создаём PDF с полями 20 мм со всех сторон
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        left_margin = 20 * mm
        top_margin = 20 * mm
        p.translate(left_margin, top_margin)  # Сдвигаем содержимое внутрь полей

        # Шапка отчёта
        p.setFont("DejaVuSansBold", 18)
        p.drawString(0, height - top_margin - 30, "Мои расходы")

        p.setFont("DejaVuSans", 12)
        p.drawString(0, height - top_margin - 60, f"Пользователь: {request.user.username}")
        p.drawString(0, height - top_margin - 80, f"Дата экспорта: {timezone.now().strftime('%d.%m.%Y %H:%M')}")
        p.drawString(0, height - top_margin - 100, f"Количество записей: {expenses.count()}")

        # Горизонтальная линия под шапкой
        p.line(0, height - top_margin - 110, width - 40 * mm, height - top_margin - 110)

        # Параметры таблицы
        y_position = height - top_margin - 140
        headers = ['№', 'Дата', 'Категория', 'Сумма (руб.)', 'Комментарий']
        col_widths = [30, 80, 160, 90, 160]  # Ширина колонок в мм
        col_positions = [sum(col_widths[:i]) for i in range(len(col_widths))]

        # Заголовки таблицы с заливкой и рамками
        p.setFont("DejaVuSansBold", 11)
        p.setFillColor(CMYKColor(0, 0, 0, 0.2))  # Светло‑серая заливка для заголовков
        for i, header in enumerate(headers):
            p.rect(col_positions[i], y_position, col_widths[i], 20, fill=1)  # Фон ячейки
            # Вертикальные линии для заголовков
            if i < len(headers) - 1:
                p.line(col_positions[i + 1], y_position, col_positions[i + 1], y_position - 20)
        # Горизонтальная линия внизу заголовков
        p.line(0, y_position - 20, sum(col_widths), y_position - 20)
        for i, header in enumerate(headers):
            p.setFillColor(CMYKColor(0, 0, 0, 1))  # Чёрный текст
            p.drawCentredString(col_positions[i] + col_widths[i] / 2, y_position + 5, header)

        y_position -= 20

        # Данные расходов с переносом текста в комментариях
        total_amount = 0
        line_height = 50  # Высота строки в пунктах

        for idx, expense in enumerate(expenses, start=1):
            if y_position < 50:  # Проверка на конец страницы
                p.showPage()
                p.translate(left_margin, top_margin)
                y_position = height - top_margin - 60
                # Повторяем заголовки таблицы с рамками
                for i, header in enumerate(headers):
                    p.rect(col_positions[i], y_position, col_widths[i], 20, fill=1)
                    if i < len(headers) - 1:
                        p.line(col_positions[i + 1], y_position, col_positions[i + 1], y_position - 20)
                p.line(0, y_position - 20, sum(col_widths), y_position - 20)
                for i, header in enumerate(headers):
                    p.setFillColor(CMYKColor(0, 0, 0, 1))
                    p.drawCentredString(col_positions[i] + col_widths[i] / 2, y_position + 5, header)
                y_position -= 20

            # Рисуем рамку для текущей строки
            p.rect(0, y_position - line_height, sum(col_widths), line_height)  # Внешняя рамка строки

            # Рисуем внутренние вертикальные разделители для строки данных
            for i in range(1, len(col_positions)):
                p.line(col_positions[i], y_position, col_positions[i], y_position - line_height)

            # Данные строки
            row_data = [
                str(idx),
                expense.date.strftime('%d.%m.%Y'),
                expense.category.name,
                f"{expense.amount:,.2f}".replace(',', ' '),
                expense.description or ''
            ]

            # Отрисовка данных с переносом комментариев
            for i, data in enumerate(row_data):
                x = col_positions[i]
                y = y_position - line_height + 30

                if i == 4:  # Комментарий — переносим текст
                    text = p.beginText(x + 4, y)
                    text.setFont("DejaVuSans", 9)
                    words = data.split()
                    current_line = []
                    for word in words:
                        test_line = ' '.join(current_line + [word])
                        if p.stringWidth(test_line, "DejaVuSans", 9) < col_widths[i] - 12:  # Увеличенный отступ для надёжности
                            current_line.append(word)
                        else:
                            if current_line:
                                text.textLine(' '.join(current_line))
                                current_line = [word]
                    if current_line:
                        text.textLine(' '.join(current_line))
                    p.drawText(text)
                else:  # Остальные колонки — простой вывод
                    if i == 3:  # Сумма — выравнивание по правому краю
                        p.drawRightString(x + col_widths[i] - 6, y, data)  # Увеличенный отступ от правого края
                    else:
                        p.drawString(x + 6, y, data)  # Увеличенный отступ от левого края

            total_amount += expense.amount
            y_position -= line_height

        # Итоговая строка с рамкой и выделением
        if y_position >= 50:
            p.setFont("DejaVuSansBold", 12)
            p.setFillColor(CMYKColor(0, 0, 0, 0.5))  # Тёмно‑серая заливка
            p.rect(sum(col_widths) - col_widths[-2] - col_widths[-1], y_position - line_height,
                   col_widths[-2] + col_widths[-1], line_height, fill=1)
            p.setFillColor(CMYKColor(0, 0, 0, 1))  # Чёрный текст
            p.drawString(sum(col_widths) - col_widths[-2] - col_widths[-1] + 2,
                         y_position - line_height + 3, "ОБЩАЯ СУММА:")
            p.drawRightString(sum(col_widths) - 4, y_position - line_height + 3,
                             f"{total_amount:,.2f} руб.".replace(',', ' '))
        
        # Нижний колонтитул
        p.saveState()
        p.setFont("DejaVuSans", 8)
        p.setFillColor(CMYKColor(0, 0, 0, 0.3))  # Светло‑серый цвет
        p.drawString(0, 20, f"Сформировано: {timezone.now().strftime('%d.%m.%Y %H:%M')}")
        p.restoreState()

        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type='application/pdf')
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="расходы_{timestamp}.pdf"'
        return response

    except Exception as e:
        messages.error(request, f'Ошибка при создании PDF: {e}')
        return redirect('expenses_list')

# Добавление нового расхода
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user  # Привязываем расход к текущему пользователю
            expense.save()
            messages.success(request, 'Расход успешно добавлен!')
            return redirect('expenses_list')
    else:
        form = ExpenseForm()
    return render(
        request,
        'expense_app/add_expense.html',
        {'form': form}
    )
    
# Редактирование расхода
@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Расход успешно обновлён!')
            return redirect('expenses_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(
        request,
        'expense_app/edit_expense.html',
        {'form': form, 'expense': expense}
    )
    
# Удаление расхода
@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Расход удалён!')
        return redirect('expenses_list')

    return render(
        request,
        'expense_app/delete_expense.html',
        {'expense': expense}
    )

@login_required
def download_csv(request):
    # Проверяем, есть ли подготовленные данные в сессии
    csv_data = request.session.get('export_data')
    filename = request.session.get('export_filename')

    if not csv_data or not filename:
        messages.error(request, 'Файл для скачивания не найден. Пожалуйста, подготовьте экспорт заново.')
        return redirect('index')

    # Создаём HTTP‑ответ с CSV
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Очищаем данные из сессии после скачивания
    del request.session['export_data']
    del request.session['export_filename']
    # Удаляем флаг успешного экспорта
    if 'export_success' in request.session:
        del request.session['export_success']

    return response

    
@login_required
def statistics(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Фильтруем расходы по пользователю и категории
    expenses = Expense.objects.filter(user=request.user).select_related('category')

    # Применяем фильтрацию по датам, если указаны
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    # Если данных нет, возвращаем пустой контекст
    if not expenses.exists():
        context = {
            'category_stats': {},
            'total_sum': 0,
            'category_percentages': {},
            'graphic': None,
            'start_date': start_date,
            'end_date': end_date,
            'no_data': True
        }
        return render(request, 'expense_app/statistics.html', context)

    # Преобразуем данные в DataFrame для анализа
    data = []
    for expense in expenses:
        data.append({
            'category': expense.category.name if expense.category else 'Без категории',
            'amount': float(expense.amount),
            'date': expense.date
        })
    df = pd.DataFrame(data)

    # Группируем по категориям и считаем суммы
    category_stats = df.groupby('category')['amount'].sum()
    total_sum = category_stats.sum()

    # Рассчитываем доли в процентах
    if total_sum > 0:
        category_percentages = (category_stats / total_sum * 100).round(1)
    else:
        category_percentages = pd.Series()

    # Строим график распределения расходов
    try:
        plt.figure(figsize=(10, 6))
        if len(category_stats) > 0:
            plt.pie(
                category_stats,
                labels=category_stats.index,
                autopct='%1.1f%%'
            )
            plt.title('Распределение расходов по категориям')
            # Сохраняем график в base64 для передачи в шаблон
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            graphic = base64.b64encode(image_png).decode('utf-8')
        else:
            graphic = None
    except Exception as e:
        print(f'Ошибка при построении графика: {e}')
        graphic = None

    plt.close()  # Закрываем фигуру, освобождая память
    context = {
        'category_stats': category_stats.to_dict() if not category_stats.empty else {},
        'total_sum': total_sum,
        'category_percentages': category_percentages.to_dict() if not category_percentages.empty else {},
        'graphic': graphic,
        'start_date': start_date,
        'end_date': end_date,
        'no_data': False
    }
    return render(request, 'expense_app/statistics.html', context)

# Авторизация пользователя
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'expense_app/login.html', {'form': form})


# Выход пользователя из системы
def user_logout(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('login')
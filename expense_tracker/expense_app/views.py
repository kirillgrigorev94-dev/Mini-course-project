import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Используем неинтерактивный бэкенд для серверной среды
import matplotlib.pyplot as plt
import json
import base64
import csv
from io import BytesIO
from .models import Expense, Category, Tag, get_category_spent_this_month
from .forms import ExpenseForm, ExpenseTemplate, ExpenseTemplateForm
from datetime import date
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.colors import CMYKColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, LongTable, TableStyle, Paragraph, Spacer


def get_filtered_expenses(user, request):
    """
    Получает отфильтрованные расходы пользователя на основе параметров GET-запроса.
    
    Поддерживает фильтрацию по:
        - сумме (минимальная/максимальная);
        - ключевому слову в описании;
        - тегу;
        - диапазону дат (через дополнительные параметры).
    
    Args:
        user (User): Объект пользователя, чьи расходы нужно отфильтровать.
        request (HttpRequest): HTTP-запрос с параметрами фильтрации в 'request.GET'.
        
    Returns:
        QuerySet: Отфильтрованный набор объектов 'Expense'.
        
    Raises:
        ValueError: Если параметры 'min_amount' или 'max_amount' не могут быть преобразованны в число.
        
    """
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    keyword = request.GET.get('keyword', '').strip()

    expenses = Expense.objects.filter(user=user)
    tag_id = request.GET.get('tag')
    
    if tag_id:
        try:
            tag_id = int(tag_id)
            expenses = expenses.filter(tags__id=tag_id)
        except ValueError:
            pass

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
    tag_id = request.GET.get('tag')

    # Получаем отфильтрованные расходы (включая фильтрацию по тегам)
    expenses = get_filtered_expenses(request.user, request)

    if export_format == 'csv':
        return export_to_csv(request, expenses)  # Передаём отфильтрованные данные
    elif export_format == 'pdf':
        return export_to_pdf(request, expenses)  # Передаём отфильтрованные данные
    
# --- ДОБАВЛЕНО: расчёт лимитов по категориям ---
    categories_data = []
    for category in Category.objects.all():
        spent = get_category_spent_this_month(request.user, category)
        limit = category.monthly_limit
        percent = 0.0
        status = 'ok'  # ok / warning / over
        if limit and limit > 0:
            percent = min(100.0, (spent / limit) * 100)
            if percent >= 100:
                status = 'over'
            elif percent >= 80:
                status = 'warning'
        else:
            # Если лимита нет — считаем как «без лимита», статус нейтральный
            status = 'no_limit'

        categories_data.append({
            'category': category,
            'spent': spent,
            'limit': limit,
            'percent': percent,
            'status': status,
        })

    # Настройка пагинации
    paginator = Paginator(expenses, 10) # 10 записей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    all_tags = Tag.objects.all()

    context = {
        'expenses': page_obj,
        'min_amount': request.GET.get('min_amount'),
        'max_amount': request.GET.get('max_amount'),
        'keyword': request.GET.get('keyword'),
        'all_tags': all_tags,
        'tag_id': tag_id,
        'paginator': paginator,
        'page_obj': page_obj,
        'categories_data': categories_data,
    }
    return render(request, 'expense_app/expenses_list.html', context)

# Экспорт расходов в CSV-файл
@login_required
def export_to_csv(request, expenses):
    """
    Экспортирует заданный набор расходов в CSV-файл с кодировкой UTF-8.
    
    Добавляет BOM для корректного отображения кириллицы в Excel.
    
    Args:
        request (HttpRequest): HTTP-запрос (требуется авторизация).
        expenses (QuerySet): Набор объектов 'Expense' для экспорта.
        
    Returns:
        HttpResponse: Ответ с CSV-файлом для скачивания.
            - Content-Type: 'text/csv; charset=utf-8'.
            - Заголовок 'Content-Disposition' для принудительного скачивания.
    
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="расходы.csv"'

    # BOM для корректного отображения в Excel
    response.write('\ufeff'.encode('utf-8'))

    writer = csv.writer(response)
    writer.writerow(['Дата', 'Категория', 'Сумма (руб.)', 'Комментарий', 'Теги'])

    for expense in expenses:
        tags_list = [tag.name for tag in expense.tags.all()]
        writer.writerow([
            expense.date.strftime('%d.%m.%Y'),
            expense.category.name,
            f"{expense.amount:.2f}",
            expense.description,
            ', '.join(tags_list)
        ])

    return response

@login_required
def export_to_pdf(request, expenses):
    """Экспорт расходов в PDF с корректной таблицей (перенос текста, повтор заголовков)"""

    try:
        # Регистрация шрифта с кириллицей
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSansBold', 'DejaVuSans-Bold.ttf'))

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        # Стили для текста
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='HeaderBold',
            parent=styles['Normal'],
            fontName='DejaVuSansBold',
            fontSize=18,
            spaceAfter=10,
            leading=22
        ))
        styles.add(ParagraphStyle(
            name='SubHeader',
            parent=styles['Normal'],
            fontName='DejaVuSans',
            fontSize=12,
            spaceAfter=5,
            leading=16
        ))
        
        # Отдельный стиль для колонки "Комментарии"
        comment_style = ParagraphStyle(
            name='Comment',
            parent=styles['Normal'],
            fontName='DejaVuSans',
            fontSize=9,
            leading=11,
            alignment=4,
            wordWrap='CJK'
        )

        elements = []

        # Шапка документа
        elements.append(Paragraph("Мои расходы", styles['HeaderBold']))
        elements.append(Paragraph(f"Пользователь: {request.user.username}", styles['SubHeader']))
        elements.append(Paragraph(f"Дата экспорта: {timezone.now().strftime('%d.%m.%Y %H:%M')}", styles['SubHeader']))
        elements.append(Paragraph(f"Количество записей: {expenses.count()}", styles['SubHeader']))
        elements.append(Spacer(1, 10))

        # Подготовка данных таблицы
        headers = ['№', 'Дата', 'Категория', 'Сумма (руб.)', 'Комментарий']
        data = [headers]

        total_amount = 0
        for idx, expense in enumerate(expenses, start=1):
            row = [
                str(idx),
                expense.date.strftime('%d.%m.%Y'),
                expense.category.name,
                f"{expense.amount:,.2f}".replace(',', ' '),
                Paragraph(expense.description or '', comment_style)
            ]
            data.append(row)
            total_amount += expense.amount

        # Ширина колонок (в пунктах; A4 ~595 pt, с отступами остаётся ~555 pt)
        col_widths = [25, 70, 110, 90, 226]

        # Создаём LongTable (умеет разбивать по страницам и повторять заголовки)
        table = LongTable(data, colWidths=col_widths, repeatRows=1)

        # Стилизация таблицы
        table.setStyle(TableStyle([
            # Заливка шапки
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightsalmon),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.lightgoldenrodyellow),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSansBold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

            # Выравнивание данных
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (3, -1), 'LEFT'),          # №, Дата, Категория, Сумма — влево
            ('ALIGN', (4, 1), (-1, -1), 'LEFT'),        # Комментарий — влево
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),

            # Сетка
            ('GRID', (0, 0), (-1, -1), 0.5, colors.green),

            # Отступы внутри ячеек
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))

        # Перенос длинных строк в комментарии работает автоматически благодаря LongTable
        elements.append(table)

        # Итоговая строка (добавляем как отдельный блок под таблицей)
        total_style = ParagraphStyle(
            name='Total',
            parent=styles['Normal'],
            fontName='DejaVuSansBold',
            fontSize=12,
            alignment=1,  # по центру
            leading=16,
            spaceBefore=10
        )
        elements.append(Paragraph(
            f"ОБЩАЯ СУММА: {total_amount:,.2f} руб.".replace(',', ' '),
            total_style
        ))

        # Нижний колонтитул через onPage
        def add_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('DejaVuSans', 8)
            canvas.setFillColor(colors.Color(0, 0, 0, 0.3))
            canvas.drawString(
                doc.leftMargin,
                20,
                f"Сформировано: {timezone.now().strftime('%d.%m.%Y %H:%M')}"
            )
            canvas.restoreState()

        doc.build(elements, onLaterPages=add_footer)

        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type='application/pdf')
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="расходы_{timestamp}.pdf"'
        return response

    except Exception as e:
        import logging
        logging.exception("Ошибка при создании PDF")
        messages.error(request, f'Ошибка при создании PDF: {e}')
        return redirect('expenses_list')

# Добавление нового расхода
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        form.user = request.user  # передаём пользователя в форму для валидации лимитов
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user  # Привязываем расход к текущему пользователю
            expense.save()
            form.save_m2m() # Сохраняем связь с тегами
            messages.success(request, 'Расход успешно добавлен!')
            return redirect('expenses_list')
    else:
        form = ExpenseForm()
        form.user = request.user
    return render(request, 'expense_app/add_expense.html', {'form': form})
    
# Редактирование расхода
@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        form.user = request.user
        if form.is_valid():
            form.save()
            messages.success(request, 'Расход успешно обновлён!')
            return redirect('expenses_list')
    else:
        form = ExpenseForm(instance=expense)
        form.user = request.user
    return render(request, 'expense_app/edit_expense.html', {'form': form, 'expense': expense})
    
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
            'categories_data': [],
            'start_date': start_date,
            'end_date': end_date,
            'no_data': True
        }
        return render(request, 'expense_app/statistics.html', context)

    # Преобразуем данные в DataFrame для анализа (график)
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

    # --- ДОБАВЛЕНО: расчёт лимитов по всем категориям (текущий месяц) ---
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    categories_data = []
    for category in Category.objects.all():
        # Считаем потраченное за текущий месяц по категории
        qs = Expense.objects.filter(
            user=request.user,
            category=category,
            date__gte=first_day_of_month,
            date__lte=today,
        )
        total = qs.aggregate(total=Sum('amount'))['total'] or 0
        spent = total

        limit = category.monthly_limit
        percent = 0.0
        status_text = ""
        status_class = "bg-secondary"  # нейтральный

        if limit and limit > 0:
            percent = min(100.0, (spent / limit) * 100)
            if percent >= 100:
                status_text = "Превышение лимита"
                status_class = "bg-danger text-white"
            elif percent >= 80:
                status_text = "Приближение к лимиту"
                status_class = "bg-warning text-dark"
            else:
                status_text = "В пределах лимита"
                status_class = "bg-success text-white"
        else:
            status_text = "Лимит не установлен"
            status_class = "bg-light text-dark"

        categories_data.append({
            "category": category,
            "spent": spent,
            "limit": limit,
            "percent": percent,
            "status_text": status_text,
            "status_class": status_class,
        })

    context = {
        'category_stats': category_stats.to_dict() if not category_stats.empty else {},
        'total_sum': total_sum,
        'category_percentages': category_percentages.to_dict() if not category_percentages.empty else {},
        'graphic': graphic,
        'categories_data': categories_data,
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

@login_required
def run_scheduled_tasks(request):
    """Ручное выполнение запланированных задач (для админов)"""
    if not request.user.is_staff:
        return HttpResponseForbidden()

    from .scheduler import export_monthly_report, generate_statistics_report

    task_name = request.GET.get('task')
    if task_name == 'export':
        export_monthly_report()
    elif task_name == 'stats':
        generate_statistics_report()

    messages.success(request, 'Запланированные задачи выполнены')
    return redirect('admin:index')

@login_required
def expense_templates_list(request):
    """
    Отображает список шаблонов расходов текущего пользователя.
    
    Args:
        request (HttpRequest): HTTP-запрос с информацией о пользователе.
        
    Returns:
        HttpResponse: HTML-страница со списком шаблонов расходов (шаблон expense_app/expense_templates_list.html),
        содержащая контекст с переменной 'templates' (набор объектов ExpenseTemplate).
    """
    
    templates = ExpenseTemplate.objects.filter(user=request.user)
    return render(request, 'expense_app/expense_templates_list.html', {'templates': templates})

@login_required
def create_expense_template(request):
    """
    Создаёт новый шаблон расхода для текущего пользователя
    
    При GET-запросе отображает пустую форму для создания шаблона
    При POST-запросе обрабатывает отправленную форму: если данные валидны,
    сохраняет новый шаблон (привязывая его к текущему пользователю) и перенаправляет
    на страницу со списком шаблонов; в противном случае повторно отображает форму с ошибками.
    
    Args:
        request (HttpRequest): HTTP-запрос. При POST-запросе содержит данные формы ExpenseTemplateForm.
        
    Returns:
        HttpResponse:
            - При GET: HTML-страница с формой создания шаблона (шаблон expense_app/create_expense_template.html),
            содержащая контекст с переменной 'form' (пустая форма ExpenseTemplateForm).
            - При POST и успешной валидации: перенаправление на страницу списка шаблонов (URL 'expense_templates_list'),
            с отображением сообщения об успехе.
            - При POST  и неудачной валидации: HTML-страница с формой, заполненной отправленными данными и сообщениями об ошибках.
    """
    
    if request.method == 'POST':
        form = ExpenseTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            messages.success(request, 'Шаблон успешно создан!')
            return redirect('expense_templates_list')
    else:
        form = ExpenseTemplateForm()
    return render(request, 'expense_app/create_expense_template.html', {'form': form})

@login_required
def edit_expense_template(request, pk):
    template = get_object_or_404(ExpenseTemplate, id=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Шаблон успешно обновлён!')
            return redirect('expense_templates_list')
    else:
        form = ExpenseTemplateForm(instance=template)
    return render(request, 'expense_app/edit_expense_template.html', {'form': form, 'template': template})

@login_required
def delete_expense_template(request, pk):
    template = get_object_or_404(ExpenseTemplate, id=pk, user=request.user)
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Шаблон удалён!')
        return redirect('expense_templates_list')
    return render(request, 'expense_app/delete_expense_template.html', {'template': template})

@login_required
def add_expense_form_template(request, template_id):
    """
    Добавляет расход на основе выбранного шаблона.

    Получает шаблон расхода по ID (для текущего пользователя), при GET‑запросе
    отображает форму создания расхода, предварительно заполненную данными из шаблона.
    При POST‑запросе обрабатывает отправленную форму: если данные валидны,
    сохраняет новый расход (привязывая его к текущему пользователю) и перенаправляет
    на страницу со списком расходов; в противном случае повторно отображает форму с ошибками.

    Args:
        request (HttpRequest): HTTP‑запрос. При POST‑запросе содержит данные формы ExpenseForm.
        template_id (int): ID шаблона расхода (ExpenseTemplate), используемого для предварительного заполнения формы.

    Returns:
        HttpResponse:
            - При GET: HTML‑страница с формой добавления расхода (шаблон expense_app/add_expense.html),
              содержащая контекст с переменными:
                * 'form' — форма ExpenseForm, предварительно заполненная данными из шаблона;
                * 'template' — объект ExpenseTemplate, используемый для заполнения формы.
            - При POST и успешной валидации: перенаправление на страницу списка расходов (URL 'expenses_list'),
              с отображением сообщения об успехе.
            - При POST и неудачной валидации: HTML‑страница с формой, заполненной отправленными данными и сообщениями об ошибках.

    Raises:
        Http404: если шаблон с указанным ID не найден или не принадлежит текущему пользователю.
    """
    
    template = get_object_or_404(ExpenseTemplate, id=template_id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            form.save_m2m() # Сохранение тегов
            messages.success(request, 'Расход успешно добавлен!')
            return redirect('expenses_list')
    else:
        # Предварительно заполняем форму данными из шаблона
        form = ExpenseForm(initial={
            'amount': template.amount,
            'category': template.category,
            'description': template.description,
            'tags': template.tags.all()
        })
    return render(request, 'expense_app/add_expense.html', {'form': form, 'template': template})
import calendar
import csv
import json
import logging
import re
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CategoryForm,
    ProfileUpdateForm,
    TransactionForm,
    UserRegistrationForm,
    UserUpdateForm,
)
from .models import Category, Transaction, add_months

logger = logging.getLogger(__name__)


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info('User registered: %s', user.username)
            messages.success(request, 'Registration successful. Please log in to continue.')
            return redirect('login')
    else:
        form = UserRegistrationForm()

    return render(request, 'app/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user)
    income_total = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    expense_total = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    balance = income_total - expense_total

    today = date.today()
    month_transactions = transactions.filter(date__year=today.year, date__month=today.month)
    month_income = month_transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    month_expense = month_transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0')

    recent_transactions = transactions.order_by('-date', '-time')[:6]
    category_summary = (
        transactions.filter(transaction_type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')[:6]
    )

    chart_labels = []
    income_values = []
    expense_values = []
    for offset in range(-5, 1):
        month_date = add_months(today, offset)
        label = month_date.strftime('%b %Y')
        chart_labels.append(label)

        month_slice = transactions.filter(date__year=month_date.year, date__month=month_date.month)
        income_values.append(float(month_slice.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0))
        expense_values.append(float(month_slice.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0))

    budget_limit = request.user.profile.budget_limit
    budget_progress = 0
    if budget_limit:
        try:
            budget_progress = min(100, int((expense_total / budget_limit) * 100))
        except (TypeError, ZeroDivisionError):
            budget_progress = 0

    pie_labels = [row['category__name'] for row in category_summary]
    pie_values = [float(row['total']) for row in category_summary]
    if not pie_labels:
        pie_labels = ['No expenses']
        pie_values = [1.0]

    bar_labels = pie_labels
    bar_values = pie_values

    date_summary = {}
    for tr in month_transactions:
        day = tr.date
        summary = date_summary.setdefault(day, {'total': 0.0, 'income': 0.0, 'expense': 0.0, 'count': 0})
        total_amount = float(tr.amount)
        summary['total'] += total_amount
        summary['count'] += 1
        if tr.transaction_type == 'income':
            summary['income'] += total_amount
        else:
            summary['expense'] += total_amount

    cal = calendar.Calendar(firstweekday=0)
    month_calendar = []
    for week in cal.monthdatescalendar(today.year, today.month):
        week_row = []
        for day in week:
            week_row.append({
                'date': day,
                'is_current_month': day.month == today.month,
                'stats': date_summary.get(day),
            })
        month_calendar.append(week_row)

    if budget_limit and expense_total > budget_limit:
        logger.warning('User %s exceeded budget: spent=%s limit=%s', request.user.username, expense_total, budget_limit)
        messages.warning(request, 'Your expenses have exceeded your budget limit.')

    logger.info('Dashboard loaded for %s: balance=%s income=%s expense=%s', request.user.username, balance, income_total, expense_total)
    return render(request, 'app/dashboard.html', {
        'income_total': income_total,
        'expense_total': expense_total,
        'balance': balance,
        'month_income': month_income,
        'month_expense': month_expense,
        'recent_transactions': recent_transactions,
        'category_summary': category_summary,
        'chart_labels': chart_labels,
        'income_values': income_values,
        'expense_values': expense_values,
        'pie_labels': pie_labels,
        'pie_values': pie_values,
        'bar_labels': bar_labels,
        'bar_values': bar_values,
        'budget_limit': budget_limit,
        'budget_progress': budget_progress,
        'budget_status': 'danger' if budget_limit and expense_total > budget_limit else 'success',
        'month_calendar': month_calendar,
        'month_name': today.strftime('%B'),
        'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'transaction_form': TransactionForm(user=request.user),
    })


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    transactions = Transaction.objects.filter(user=request.user)
    stats = {
        'income_total': transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0'),
        'expense_total': transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0'),
        'transaction_count': transactions.count(),
    }

    logger.info('Profile page visited by %s', request.user.username)
    return render(request, 'app/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'stats': stats,
    })


@login_required
def transaction_list(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user).select_related('category')
    query = request.GET.get('q', '')
    transaction_type = request.GET.get('type', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if query:
        transactions = transactions.filter(
            Q(notes__icontains=query) | Q(category__name__icontains=query)
        )
    if transaction_type in ['income', 'expense']:
        transactions = transactions.filter(transaction_type=transaction_type)
    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__lte=end_date)

    transactions = transactions.order_by('-date', '-time')

    totals = {
        'income': transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0'),
        'expense': transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0'),
    }

    logger.info('Transaction list viewed by %s: filter=%s start=%s end=%s query=%s', request.user.username, transaction_type, start_date, end_date, query)
    return render(request, 'app/transaction_list.html', {
        'transactions': transactions,
        'totals': totals,
        'query': query,
        'transaction_type': transaction_type,
        'start_date': start_date,
        'end_date': end_date,
    })


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            logger.info('Transaction added by %s: %s %s %s', request.user.username, transaction.transaction_type, transaction.amount, transaction.category.name)
            messages.success(request, 'Transaction added successfully.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(user=request.user)

    return render(request, 'app/transaction_form.html', {'form': form, 'title': 'Add Transaction'})


@login_required
def transaction_update(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            logger.info('Transaction updated by %s: id=%s type=%s amount=%s', request.user.username, transaction.pk, transaction.transaction_type, transaction.amount)
            messages.success(request, 'Transaction updated successfully.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction, user=request.user)

    return render(request, 'app/transaction_form.html', {'form': form, 'title': 'Edit Transaction'})


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        logger.info('Transaction deleted by %s: id=%s amount=%s', request.user.username, transaction.pk, transaction.amount)
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully.')
        return redirect('transaction_list')
    return render(request, 'app/transaction_confirm_delete.html', {'transaction': transaction})


@login_required
def category_list(request):
    categories = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True)).order_by('category_type', 'name')
    return render(request, 'app/category_list.html', {'categories': categories})


@login_required
def category_entries(request, pk):
    category = get_object_or_404(
        Category.objects.filter(Q(user=request.user) | Q(user__isnull=True)),
        pk=pk
    )
    transactions = Transaction.objects.filter(user=request.user, category=category).order_by('-date', '-time')
    return render(request, 'app/category_entries.html', {
        'category': category,
        'transactions': transactions,
    })


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            logger.info('Category created by %s: %s', request.user.username, category.name)
            messages.success(request, 'Category created successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'app/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            logger.info('Category updated by %s: %s', request.user.username, category.name)
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'app/category_form.html', {'form': form, 'title': 'Edit Category'})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        logger.info('Category deleted by %s: %s', request.user.username, category.name)
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('category_list')
    return render(request, 'app/category_confirm_delete.html', {'category': category})


@login_required
def export_transactions_csv(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date', '-time')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Time', 'Type', 'Category', 'Amount', 'Payment Method', 'Notes'])
    for transaction in transactions:
        logger.info('Exporting transaction for %s: %s %s', request.user.username, transaction.pk, transaction.amount)
        writer.writerow([
            transaction.date,
            transaction.time,
            transaction.get_transaction_type_display(),
            transaction.category.name,
            transaction.amount,
            transaction.get_payment_method_display(),
            transaction.notes,
        ])
    return response

@login_required
def process_voice_command(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '').lower()

            # 1. Detect Amount (Extracts the first number found)
            amount_match = re.search(r'\b\d+(\.\d+)?\b', text)
            amount = amount_match.group(0) if amount_match else ""

            # 2. Detect Transaction Type
            transaction_type = 'expense'
            income_keywords = ['received', 'receive', 'salary', 'income', 'earned', 'got', 'credited']
            if any(word in text for word in income_keywords):
                transaction_type = 'income'

            # 3. Detect Category
            category = 'Other'
            categories_map = {
                'Food/Groceries': ['grocery', 'groceries', 'food', 'restaurant', 'meal', 'eat', 'supermarket'],
                'Salary': ['salary', 'paycheck', 'wage'],
                'Transport': ['bus', 'train', 'cab', 'uber', 'transport', 'fuel', 'petrol', 'gas', 'flight'],
                'Shopping': ['shopping', 'clothes', 'bought', 'buy', 'shoes', 'electronics'],
                'Bills': ['bill', 'electricity', 'water', 'rent', 'internet', 'wifi']
            }

            for cat, keywords in categories_map.items():
                if any(keyword in text for keyword in keywords):
                    category = cat
                    break

            # 4. Generate Notes
            notes = text.capitalize()

            return JsonResponse({
                'status': 'success', 'transaction_type': transaction_type, 'amount': amount, 'category': category, 'notes': notes
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)


@login_required
def ai_assistant_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '').lower()
            user = request.user

            # Chat Assistant: Answer Spending Insights
            if 'spend this month' in text or 'spent this month' in text:
                today = date.today()
                total = Transaction.objects.filter(
                    user=user, transaction_type='expense', date__year=today.year, date__month=today.month
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                return JsonResponse({'action': 'chat', 'message': f'You have spent ${total:.2f} this month.'})
            
            elif 'highest expense' in text:
                highest = Transaction.objects.filter(user=user, transaction_type='expense').order_by('-amount').first()
                if highest:
                    return JsonResponse({'action': 'chat', 'message': f'Your highest expense was ${highest.amount} on {highest.category.name}.'})
                return JsonResponse({'action': 'chat', 'message': 'You have no expenses yet.'})
            
            elif 'recent transactions' in text:
                recent = Transaction.objects.filter(user=user).order_by('-date', '-time')[:3]
                if recent:
                    msg = "Here are your recent transactions:<br>" + "<br>".join([f"- {t.date}: ${t.amount} for {t.category.name}" for t in recent])
                    return JsonResponse({'action': 'chat', 'message': msg})
                return JsonResponse({'action': 'chat', 'message': 'No recent transactions found.'})
            
            else:
                # Smart Transaction Detection
                amount_match = re.search(r'\b\d+(\.\d+)?\b', text)
                amount = amount_match.group(0) if amount_match else ""

                transaction_type = 'expense'
                if any(word in text for word in ['received', 'receive', 'salary', 'income', 'earned', 'got', 'credited']):
                    transaction_type = 'income'

                category_id = ""
                categories_map = {
                    'Food': ['grocery', 'groceries', 'food', 'restaurant', 'meal', 'eat', 'supermarket'],
                    'Salary': ['salary', 'paycheck', 'wage'],
                    'Transport': ['bus', 'train', 'cab', 'uber', 'transport', 'fuel', 'petrol', 'gas', 'flight'],
                    'Shopping': ['shopping', 'clothes', 'bought', 'buy', 'shoes', 'electronics'],
                    'Bills': ['bill', 'electricity', 'water', 'rent', 'internet', 'wifi']
                }

                matched_cat_name = None
                for cat, keywords in categories_map.items():
                    if any(keyword in text for keyword in keywords):
                        matched_cat_name = cat
                        break

                if matched_cat_name:
                    cat_obj = Category.objects.filter(Q(user=user) | Q(user__isnull=True), name__icontains=matched_cat_name).first()
                    if cat_obj:
                        category_id = cat_obj.id

                notes = text.capitalize()

                return JsonResponse({
                    'action': 'fill_form',
                    'transaction_type': transaction_type,
                    'amount': amount,
                    'category': category_id,
                    'notes': notes,
                    'message': 'I have filled out the form based on your input! Please review and save.'
                })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

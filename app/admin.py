from django.contrib import admin

from .models import Category, Profile, Transaction


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'budget_limit', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'user', 'created_at')
    list_filter = ('category_type',)
    search_fields = ('name', 'description')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'transaction_type', 'amount', 'payment_method', 'date', 'time')
    list_filter = ('transaction_type', 'payment_method', 'date')
    search_fields = ('notes', 'category__name', 'user__username')

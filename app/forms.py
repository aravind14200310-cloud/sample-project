from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models

from .models import Category, Profile, Transaction


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with that email address already exists.')
        return email


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'phone_number', 'budget_limit']
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone number'}),
            'budget_limit': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Budget limit'}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'transaction_type',
            'category',
            'amount',
            'date',
            'time',
            'payment_method',
            'notes',
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Amount'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Notes'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        user = user or None
        categories = Category.objects.filter(models.Q(user=user) | models.Q(user__isnull=True))
        transaction_type = self.data.get('transaction_type') or self.initial.get('transaction_type')
        if transaction_type in ['income', 'expense']:
            categories = categories.filter(category_type=transaction_type)
        self.fields['category'].queryset = categories

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        transaction_type = cleaned_data.get('transaction_type')
        if category and transaction_type and category.category_type != transaction_type:
            raise forms.ValidationError('Selected category does not match the transaction type.')
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'category_type']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Description'}),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
        }

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Book, Loan


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author', 'isbn', 'genres', 'total_copies',
                  'available_copies')
        widgets = {
            'genres': forms.CheckboxSelectMultiple,
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_copies')
        available = cleaned_data.get('available_copies')
        if total is not None and available is not None:
            if available > total:
                raise forms.ValidationError(
                    'Available copies cannot exceed total copies.'
                )
        return cleaned_data


class AssignLoanForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False, is_active=True),
        label='Member',
        empty_label='Select a member',
    )
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(available_copies__gt=0),
        label='Book',
        empty_label='Select a book',
    )

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        book = cleaned_data.get('book')

        if member and book:
            if book.available_copies <= 0:
                raise forms.ValidationError(
                    'This book has no available copies.'
                )
            if Loan.objects.filter(
                member=member, book=book, is_active=True
            ).exists():
                raise forms.ValidationError(
                    'This member already has an active loan for this book.'
                )
        return cleaned_data

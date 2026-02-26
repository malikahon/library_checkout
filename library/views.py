from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import RegistrationForm
from .models import Book, Loan


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def book_list_view(request):
    books = Book.objects.prefetch_related('genres').all()
    return render(request, 'library/book_list.html', {'books': books})


@login_required
def book_detail_view(request, pk):
    book = get_object_or_404(Book.objects.prefetch_related('genres'), pk=pk)
    has_active_loan = Loan.objects.filter(
        member=request.user, book=book, is_active=True
    ).exists()
    can_checkout = book.available_copies > 0 and not has_active_loan
    return render(request, 'library/book_detail.html', {
        'book': book,
        'has_active_loan': has_active_loan,
        'can_checkout': can_checkout,
    })


@login_required
def book_checkout_view(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=pk)

            if book.available_copies <= 0:
                messages.error(request, 'No copies currently available.')
                return redirect('library:book_detail', pk=pk)

            if Loan.objects.filter(
                member=request.user, book=book, is_active=True
            ).exists():
                messages.error(
                    request, 'You already have this book checked out.'
                )
                return redirect('library:book_detail', pk=pk)

            Loan.objects.create(member=request.user, book=book)
            book.available_copies -= 1
            book.save(update_fields=['available_copies'])

    except Book.DoesNotExist:
        from django.http import Http404
        raise Http404
    except IntegrityError:
        messages.error(request, 'You already have this book checked out.')
        return redirect('library:book_detail', pk=pk)

    messages.success(request, f'You have checked out "{book.title}".')
    return redirect('library:book_detail', pk=pk)


@login_required
def loan_return_view(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        with transaction.atomic():
            loan = (
                Loan.objects
                .select_for_update()
                .select_related('book')
                .get(pk=pk, member=request.user, is_active=True)
            )
            book = Book.objects.select_for_update().get(pk=loan.book_id)

            loan.returned_at = timezone.now()
            loan.is_active = False
            loan.save(update_fields=['returned_at', 'is_active'])

            book.available_copies += 1
            book.save(update_fields=['available_copies'])

    except Loan.DoesNotExist:
        from django.http import Http404
        raise Http404

    messages.success(request, f'You have returned "{book.title}".')
    return redirect('library:my_loans')


@login_required
def my_loans_view(request):
    active_loans = (
        Loan.objects
        .filter(member=request.user, is_active=True)
        .select_related('book')
    )
    past_loans = (
        Loan.objects
        .filter(member=request.user, is_active=False)
        .select_related('book')
    )
    return render(request, 'library/my_loans.html', {
        'active_loans': active_loans,
        'past_loans': past_loans,
    })

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from .forms import AssignLoanForm, BookForm, RegistrationForm
from .mixins import StaffRequiredMixin
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


# ---------------------------------------------------------------------------
# Staff Views — Book Management
# ---------------------------------------------------------------------------

class StaffBookListView(StaffRequiredMixin, ListView):
    model = Book
    template_name = 'library/staff/book_list.html'
    context_object_name = 'books'

    def get_queryset(self):
        return Book.objects.prefetch_related('genres').all()


class StaffBookCreateView(StaffRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'library/staff/book_form.html'
    success_url = reverse_lazy('library:staff_book_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Book "{self.object.title}" has been added.')
        return response


class StaffBookUpdateView(StaffRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'library/staff/book_form.html'
    success_url = reverse_lazy('library:staff_book_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Book "{self.object.title}" has been updated.')
        return response


class StaffBookDeleteView(StaffRequiredMixin, DeleteView):
    model = Book
    template_name = 'library/staff/book_confirm_delete.html'
    success_url = reverse_lazy('library:staff_book_list')

    def form_valid(self, form):
        if self.object.loans.filter(is_active=True).exists():
            messages.error(
                self.request,
                'Cannot delete this book — it has active loans.'
            )
            return redirect('library:staff_book_list')
        messages.success(self.request, f'Book "{self.object.title}" has been deleted.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Staff Views — Loan Management
# ---------------------------------------------------------------------------

class StaffLoanListView(StaffRequiredMixin, ListView):
    model = Loan
    template_name = 'library/staff/loan_list.html'
    context_object_name = 'loans'

    def get_queryset(self):
        qs = Loan.objects.select_related('book', 'member').all()
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'returned':
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        return context


class StaffLoanAssignView(StaffRequiredMixin, FormView):
    form_class = AssignLoanForm
    template_name = 'library/staff/loan_assign.html'
    success_url = reverse_lazy('library:staff_loan_list')

    def form_valid(self, form):
        member = form.cleaned_data['member']
        book = form.cleaned_data['book']

        try:
            with transaction.atomic():
                book_locked = Book.objects.select_for_update().get(pk=book.pk)

                if book_locked.available_copies <= 0:
                    messages.error(self.request, 'No copies currently available.')
                    return redirect('library:staff_loan_assign')

                if Loan.objects.filter(
                    member=member, book=book_locked, is_active=True
                ).exists():
                    messages.error(
                        self.request,
                        'This member already has an active loan for this book.'
                    )
                    return redirect('library:staff_loan_assign')

                Loan.objects.create(member=member, book=book_locked)
                book_locked.available_copies -= 1
                book_locked.save(update_fields=['available_copies'])

        except IntegrityError:
            messages.error(
                self.request,
                'This member already has an active loan for this book.'
            )
            return redirect('library:staff_loan_assign')

        messages.success(
            self.request,
            f'Loan assigned: "{book.title}" to {member.username}.'
        )
        return super().form_valid(form)


class StaffForceReturnView(StaffRequiredMixin, View):

    def post(self, request, pk):
        try:
            with transaction.atomic():
                loan = (
                    Loan.objects
                    .select_for_update()
                    .select_related('book')
                    .get(pk=pk, is_active=True)
                )
                book = Book.objects.select_for_update().get(pk=loan.book_id)

                loan.is_active = False
                loan.returned_at = timezone.now()
                loan.save(update_fields=['is_active', 'returned_at'])

                book.available_copies += 1
                book.save(update_fields=['available_copies'])

        except Loan.DoesNotExist:
            from django.http import Http404
            raise Http404

        messages.success(
            request,
            f'Loan for "{book.title}" by {loan.member.username} has been returned.'
        )
        return redirect('library:staff_loan_list')

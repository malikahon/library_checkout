from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from .forms import AssignLoanForm, BookForm, RegistrationForm
from .mixins import StaffRequiredMixin
from .models import Book, Loan


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        # If there's an explicit ?next= parameter, honour it.
        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, ''),
        )
        if redirect_to:
            return redirect_to
        # Staff users land on Manage Books; members land on the catalogue.
        if self.request.user.is_staff:
            return reverse_lazy('library:staff_book_list')
        return reverse_lazy('library:book_list')


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _execute_checkout(member, book_pk):
    """Atomically create a loan and decrement available copies.

    Must be called inside a ``transaction.atomic()`` block.

    Returns the created ``Loan`` on success.
    Raises ``Book.DoesNotExist`` if the book is missing.
    Raises ``ValueError`` with a user-friendly message on business-rule
    violations (no copies available, duplicate active loan).
    """
    book = Book.objects.select_for_update().get(pk=book_pk)

    if book.available_copies <= 0:
        raise ValueError('No copies currently available.')

    if Loan.objects.filter(member=member, book=book, is_active=True).exists():
        raise ValueError('This member already has an active loan for this book.')

    loan = Loan.objects.create(member=member, book=book)
    book.available_copies -= 1
    book.save(update_fields=['available_copies'])
    return loan


def _execute_return(loan_pk, *, scope_filter=None):
    """Atomically deactivate a loan and restore the book copy.

    Must be called inside a ``transaction.atomic()`` block.

    ``scope_filter`` is an optional dict of extra ``.get()`` kwargs
    (e.g. ``{'member': request.user}``) used to restrict which loans
    the caller is allowed to return.

    Returns the deactivated ``Loan``.
    Raises ``Loan.DoesNotExist`` if no matching active loan is found.
    """
    lookup = {'pk': loan_pk, 'is_active': True}
    if scope_filter:
        lookup.update(scope_filter)

    loan = (
        Loan.objects
        .select_for_update()
        .select_related('book')
        .get(**lookup)
    )
    book = Book.objects.select_for_update().get(pk=loan.book_id)

    loan.is_active = False
    loan.returned_at = timezone.now()
    loan.save(update_fields=['is_active', 'returned_at'])

    book.available_copies += 1
    book.save(update_fields=['available_copies'])
    return loan


# ---------------------------------------------------------------------------
# Public / Member Views
# ---------------------------------------------------------------------------

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
            loan = _execute_checkout(request.user, pk)
    except Book.DoesNotExist:
        raise Http404
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('library:book_detail', pk=pk)
    except IntegrityError:
        messages.error(request, 'You already have this book checked out.')
        return redirect('library:book_detail', pk=pk)

    messages.success(request, f'You have checked out "{loan.book.title}".')
    return redirect('library:book_detail', pk=pk)


@login_required
def loan_return_view(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        with transaction.atomic():
            loan = _execute_return(pk, scope_filter={'member': request.user})
    except Loan.DoesNotExist:
        raise Http404

    messages.success(request, f'You have returned "{loan.book.title}".')
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
                _execute_checkout(member, book.pk)
        except ValueError as exc:
            messages.error(self.request, str(exc))
            return redirect('library:staff_loan_assign')
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
                loan = _execute_return(pk)
        except Loan.DoesNotExist:
            raise Http404

        messages.success(
            request,
            f'Loan for "{loan.book.title}" by {loan.member.username} has been returned.'
        )
        return redirect('library:staff_loan_list')


# ---------------------------------------------------------------------------
# Staff Views — User Management
# ---------------------------------------------------------------------------

class StaffUserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'library/staff/user_list.html'
    context_object_name = 'members'

    def get_queryset(self):
        return (
            User.objects
            .filter(is_staff=False)
            .annotate(active_loan_count=Count('loans', filter=Q(loans__is_active=True)))
            .order_by('-date_joined')
        )

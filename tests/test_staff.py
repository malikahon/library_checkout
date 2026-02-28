"""
Tests for staff-only functionality: book CRUD, loan assignment,
force return, and loan list filtering.
"""

import pytest
from django.urls import reverse

from library.models import Book, Loan


@pytest.mark.django_db
class TestStaffBookCRUD:
    """Tests for staff book create, update, and delete operations."""

    def test_staff_create_book(self, client, staff_user, genre):
        """Staff can create a new book via POST to the add endpoint."""
        client.force_login(staff_user)
        url = reverse('library:staff_book_add')
        data = {
            'title': 'New Book',
            'author': 'New Author',
            'isbn': '9780000000001',
            'total_copies': 5,
            'available_copies': 5,
            'genres': [genre.pk],
        }
        response = client.post(url, data)

        assert response.status_code == 302
        assert Book.objects.filter(title='New Book').exists()
        book = Book.objects.get(title='New Book')
        assert book.author == 'New Author'
        assert book.total_copies == 5

    def test_staff_update_book(self, client, staff_user, book):
        """Staff can update an existing book's fields."""
        client.force_login(staff_user)
        url = reverse('library:staff_book_edit', kwargs={'pk': book.pk})
        data = {
            'title': 'Updated Title',
            'author': book.author,
            'isbn': book.isbn,
            'total_copies': book.total_copies,
            'available_copies': book.available_copies,
            'genres': list(book.genres.values_list('pk', flat=True)),
        }
        response = client.post(url, data)

        assert response.status_code == 302
        book.refresh_from_db()
        assert book.title == 'Updated Title'

    def test_staff_delete_book(self, client, staff_user, book):
        """Staff can delete a book with no active loans."""
        client.force_login(staff_user)
        url = reverse('library:staff_book_delete', kwargs={'pk': book.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert not Book.objects.filter(pk=book.pk).exists()

    def test_staff_delete_book_blocked_by_active_loans(
        self, client, staff_user, book, active_loan
    ):
        """Staff cannot delete a book that has active loans."""
        client.force_login(staff_user)
        url = reverse('library:staff_book_delete', kwargs={'pk': book.pk})
        response = client.post(url)

        assert response.status_code == 302
        # Book must still exist
        assert Book.objects.filter(pk=book.pk).exists()


@pytest.mark.django_db
class TestStaffLoanAssign:
    """Tests for staff loan assignment."""

    def test_staff_loan_assign_creates_loan(self, client, staff_user, member_user, book):
        """Staff can assign a loan on behalf of a member."""
        client.force_login(staff_user)
        url = reverse('library:staff_loan_assign')
        data = {
            'member': member_user.pk,
            'book': book.pk,
        }
        response = client.post(url, data)

        assert response.status_code == 302
        assert Loan.objects.filter(
            member=member_user, book=book, is_active=True
        ).exists()
        book.refresh_from_db()
        assert book.available_copies == 2  # was 3, now 2

    def test_staff_loan_assign_duplicate_rejected(
        self, client, staff_user, member_user, book, active_loan
    ):
        """Staff cannot assign a duplicate active loan for the same
        member and book combination."""
        client.force_login(staff_user)
        url = reverse('library:staff_loan_assign')
        data = {
            'member': member_user.pk,
            'book': book.pk,
        }
        client.post(url, data)

        # The form-level clean() should catch this and re-render or redirect
        assert Loan.objects.filter(
            member=member_user, book=book, is_active=True
        ).count() == 1


@pytest.mark.django_db
class TestStaffForceReturn:
    """Tests for staff force-return functionality."""

    def test_staff_force_return_deactivates_loan(
        self, client, staff_user, book, active_loan
    ):
        """Staff force-return sets the loan inactive and increments
        available_copies."""
        client.force_login(staff_user)
        url = reverse(
            'library:staff_loan_force_return', kwargs={'pk': active_loan.pk}
        )
        response = client.post(url)

        assert response.status_code == 302

        active_loan.refresh_from_db()
        assert active_loan.is_active is False
        assert active_loan.returned_at is not None

        book.refresh_from_db()
        # active_loan fixture decremented from 3 to 2; force-return restores to 3
        assert book.available_copies == 3

    def test_staff_force_return_nonexistent_loan_returns_404(
        self, client, staff_user
    ):
        """Force-returning a non-existent loan yields 404."""
        client.force_login(staff_user)
        url = reverse(
            'library:staff_loan_force_return', kwargs={'pk': 99999}
        )
        response = client.post(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestStaffLoanListFiltering:
    """Tests for loan list status filtering."""

    def test_loan_list_filter_active(
        self, client, staff_user, active_loan
    ):
        """?status=active shows only active loans."""
        client.force_login(staff_user)
        url = reverse('library:staff_loan_list') + '?status=active'
        response = client.get(url)

        assert response.status_code == 200
        loans = response.context['loans']
        assert all(loan.is_active for loan in loans)
        assert len(loans) == 1

    def test_loan_list_filter_returned(
        self, client, staff_user, active_loan
    ):
        """?status=returned shows only returned loans (none in this case)."""
        client.force_login(staff_user)
        url = reverse('library:staff_loan_list') + '?status=returned'
        response = client.get(url)

        assert response.status_code == 200
        loans = response.context['loans']
        assert len(loans) == 0

    def test_loan_list_no_filter_shows_all(
        self, client, staff_user, active_loan
    ):
        """No status filter shows all loans."""
        client.force_login(staff_user)
        url = reverse('library:staff_loan_list')
        response = client.get(url)

        assert response.status_code == 200
        loans = response.context['loans']
        assert len(loans) == 1

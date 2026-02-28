"""
Tests for form validation: BookForm and AssignLoanForm.
"""

import pytest

from library.forms import AssignLoanForm, BookForm
from library.models import Genre  # noqa: F401 — used by fixtures indirectly


@pytest.mark.django_db
class TestBookForm:
    """Tests for BookForm validation logic."""

    def test_rejects_available_copies_exceeding_total(self, genre):
        """BookForm.clean() raises an error when available_copies > total_copies."""
        data = {
            'title': 'Bad Book',
            'author': 'Author',
            'isbn': '9780000000002',
            'total_copies': 2,
            'available_copies': 5,
            'genres': [genre.pk],
        }
        form = BookForm(data=data)
        assert not form.is_valid()
        assert 'Available copies cannot exceed total copies.' in str(form.errors)

    def test_accepts_valid_copies(self, genre):
        """BookForm accepts data where available_copies <= total_copies."""
        data = {
            'title': 'Good Book',
            'author': 'Author',
            'isbn': '9780000000003',
            'total_copies': 5,
            'available_copies': 3,
            'genres': [genre.pk],
        }
        form = BookForm(data=data)
        assert form.is_valid()

    def test_accepts_equal_copies(self, genre):
        """BookForm accepts data where available_copies == total_copies."""
        data = {
            'title': 'Equal Book',
            'author': 'Author',
            'isbn': '9780000000004',
            'total_copies': 3,
            'available_copies': 3,
            'genres': [genre.pk],
        }
        form = BookForm(data=data)
        assert form.is_valid()


@pytest.mark.django_db
class TestAssignLoanForm:
    """Tests for AssignLoanForm validation logic."""

    def test_rejects_duplicate_active_loan(self, member_user, book, active_loan):
        """AssignLoanForm.clean() rejects assignment when the member
        already has an active loan for the same book."""
        data = {
            'member': member_user.pk,
            'book': book.pk,
        }
        form = AssignLoanForm(data=data)
        assert not form.is_valid()
        assert 'already has an active loan' in str(form.errors)

    def test_rejects_book_with_zero_availability(self, member_user, book):
        """AssignLoanForm.clean() rejects assignment when no copies
        are available."""
        book.available_copies = 0
        book.save(update_fields=['available_copies'])

        data = {
            'member': member_user.pk,
            'book': book.pk,
        }
        form = AssignLoanForm(data=data)
        # The queryset filter excludes books with 0 copies, so the form
        # should reject the book choice entirely
        assert not form.is_valid()

    def test_accepts_valid_assignment(self, member_user, book):
        """AssignLoanForm accepts a valid member + available book combo."""
        data = {
            'member': member_user.pk,
            'book': book.pk,
        }
        form = AssignLoanForm(data=data)
        assert form.is_valid()

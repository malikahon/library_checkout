"""
Tests for loan business logic: checkout, return, and duplicate prevention.
"""

import pytest
from django.urls import reverse

from library.models import Book, Loan


@pytest.mark.django_db
class TestCheckout:
    """Tests for the book checkout view."""

    def test_checkout_creates_loan_and_decrements_copies(self, client, member_user, book):
        """A POST to the checkout endpoint creates an active Loan and
        decrements the book's available_copies by 1."""
        client.force_login(member_user)
        url = reverse('library:book_checkout', kwargs={'pk': book.pk})
        response = client.post(url)

        assert response.status_code == 302

        # Verify the loan was created
        loan = Loan.objects.get(member=member_user, book=book)
        assert loan.is_active is True

        # Verify available copies decremented
        book.refresh_from_db()
        assert book.available_copies == 2  # was 3, now 2

    def test_checkout_duplicate_loan_rejected(self, client, member_user, book, active_loan):
        """A user who already has an active loan for a book cannot
        check it out again."""
        client.force_login(member_user)
        url = reverse('library:book_checkout', kwargs={'pk': book.pk})
        response = client.post(url)

        assert response.status_code == 302
        # Only the original loan should exist
        assert Loan.objects.filter(
            member=member_user, book=book, is_active=True
        ).count() == 1


@pytest.mark.django_db
class TestReturn:
    """Tests for the loan return view."""

    def test_return_deactivates_loan_and_increments_copies(
        self, client, member_user, book, active_loan
    ):
        """A POST to the return endpoint sets the loan to inactive,
        records returned_at, and increments available_copies."""
        client.force_login(member_user)
        url = reverse('library:loan_return', kwargs={'pk': active_loan.pk})
        response = client.post(url)

        assert response.status_code == 302

        # Verify the loan is now inactive
        active_loan.refresh_from_db()
        assert active_loan.is_active is False
        assert active_loan.returned_at is not None

        # Verify available copies incremented back
        book.refresh_from_db()
        # Started at 3, active_loan fixture decremented to 2, return brings it back to 3
        assert book.available_copies == 3

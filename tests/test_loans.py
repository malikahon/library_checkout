"""
Tests for loan business logic: checkout, return, duplicate prevention,
zero-availability rejection, and the my-loans view.
"""

import pytest
from django.urls import reverse

from library.models import Loan


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

    def test_checkout_rejected_when_no_copies_available(
        self, client, member_user, book
    ):
        """Checkout is rejected when the book has zero available copies."""
        book.available_copies = 0
        book.save(update_fields=['available_copies'])

        client.force_login(member_user)
        url = reverse('library:book_checkout', kwargs={'pk': book.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert not Loan.objects.filter(member=member_user, book=book).exists()

    def test_checkout_nonexistent_book_returns_404(self, client, member_user):
        """Checking out a non-existent book returns 404."""
        client.force_login(member_user)
        url = reverse('library:book_checkout', kwargs={'pk': 99999})
        response = client.post(url)

        assert response.status_code == 404


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

    def test_return_nonexistent_loan_returns_404(self, client, member_user):
        """Returning a non-existent loan returns 404."""
        client.force_login(member_user)
        url = reverse('library:loan_return', kwargs={'pk': 99999})
        response = client.post(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestMyLoans:
    """Tests for the my-loans view."""

    def test_my_loans_shows_active_and_past_loans(
        self, client, member_user, book, active_loan
    ):
        """The my-loans page separates active loans from past loans."""
        # Return the active loan to create a past loan
        active_loan.is_active = False
        active_loan.returned_at = '2025-01-01T00:00:00Z'
        active_loan.save(update_fields=['is_active', 'returned_at'])

        # Create a new active loan
        Loan.objects.create(member=member_user, book=book)

        client.force_login(member_user)
        url = reverse('library:my_loans')
        response = client.get(url)

        assert response.status_code == 200
        assert len(response.context['active_loans']) == 1
        assert len(response.context['past_loans']) == 1

    def test_my_loans_empty_for_new_user(self, client, member_user):
        """A user with no loans sees empty lists."""
        client.force_login(member_user)
        url = reverse('library:my_loans')
        response = client.get(url)

        assert response.status_code == 200
        assert len(response.context['active_loans']) == 0
        assert len(response.context['past_loans']) == 0

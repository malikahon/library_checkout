"""
Tests for permission enforcement: staff-only routes, POST-only views,
anonymous access denial, and cross-user isolation.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from library.models import Loan


# ---------------------------------------------------------------------------
# Staff-only route protection
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStaffRestriction:
    """Non-staff users must receive 403 on every staff-only view."""

    def test_non_staff_blocked_from_staff_book_list(self, client, member_user):
        client.force_login(member_user)
        url = reverse('library:staff_book_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_non_staff_blocked_from_staff_book_add(self, client, member_user):
        client.force_login(member_user)
        url = reverse('library:staff_book_add')
        response = client.get(url)
        assert response.status_code == 403

    def test_non_staff_blocked_from_staff_book_edit(self, client, member_user, book):
        client.force_login(member_user)
        url = reverse('library:staff_book_edit', kwargs={'pk': book.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_non_staff_blocked_from_staff_book_delete(self, client, member_user, book):
        client.force_login(member_user)
        url = reverse('library:staff_book_delete', kwargs={'pk': book.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_non_staff_blocked_from_staff_loan_list(self, client, member_user):
        client.force_login(member_user)
        url = reverse('library:staff_loan_list')
        response = client.get(url)
        assert response.status_code == 403

    def test_non_staff_blocked_from_staff_loan_assign(self, client, member_user):
        client.force_login(member_user)
        url = reverse('library:staff_loan_assign')
        response = client.get(url)
        assert response.status_code == 403

    def test_non_staff_blocked_from_staff_force_return(
        self, client, member_user, active_loan
    ):
        client.force_login(member_user)
        url = reverse(
            'library:staff_loan_force_return', kwargs={'pk': active_loan.pk}
        )
        response = client.post(url)
        assert response.status_code == 403

    # -- Positive: staff CAN access --

    def test_staff_can_access_staff_book_list(self, client, staff_user, book):
        client.force_login(staff_user)
        url = reverse('library:staff_book_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_staff_can_access_staff_loan_list(self, client, staff_user):
        client.force_login(staff_user)
        url = reverse('library:staff_loan_list')
        response = client.get(url)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Anonymous (unauthenticated) access denial
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAnonymousAccessDenied:
    """Unauthenticated users must be redirected to login for all
    protected endpoints."""

    def test_anonymous_redirected_from_book_list(self, client):
        url = reverse('library:book_list')
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_anonymous_redirected_from_checkout(self, client, book):
        url = reverse('library:book_checkout', kwargs={'pk': book.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_anonymous_redirected_from_loan_return(self, client, active_loan):
        url = reverse('library:loan_return', kwargs={'pk': active_loan.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_anonymous_redirected_from_my_loans(self, client):
        url = reverse('library:my_loans')
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_anonymous_redirected_from_staff_book_list(self, client):
        url = reverse('library:staff_book_list')
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_anonymous_redirected_from_staff_loan_list(self, client):
        url = reverse('library:staff_loan_list')
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url


# ---------------------------------------------------------------------------
# POST-only enforcement
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPostOnlyViews:
    """State-changing views must reject GET requests."""

    def test_checkout_rejects_get(self, client, member_user, book):
        client.force_login(member_user)
        url = reverse('library:book_checkout', kwargs={'pk': book.pk})
        response = client.get(url)
        assert response.status_code == 405

    def test_return_rejects_get(self, client, member_user, active_loan):
        client.force_login(member_user)
        url = reverse('library:loan_return', kwargs={'pk': active_loan.pk})
        response = client.get(url)
        assert response.status_code == 405

    def test_force_return_rejects_get(self, client, staff_user, active_loan):
        client.force_login(staff_user)
        url = reverse(
            'library:staff_loan_force_return', kwargs={'pk': active_loan.pk}
        )
        response = client.get(url)
        assert response.status_code == 405


# ---------------------------------------------------------------------------
# Cross-user isolation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCrossUserIsolation:
    """A member must not be able to return another member's loan."""

    def test_member_cannot_return_other_users_loan(
        self, client, book, active_loan
    ):
        """active_loan belongs to member_user. A different user should get
        404 when trying to return it (the queryset scopes by request.user)."""
        other_user = User.objects.create_user(
            username='other', password='otherpass123'
        )
        client.force_login(other_user)
        url = reverse('library:loan_return', kwargs={'pk': active_loan.pk})
        response = client.post(url)
        assert response.status_code == 404

        # Confirm the loan was NOT returned.
        active_loan.refresh_from_db()
        assert active_loan.is_active is True

"""
Tests for book-related views: list and detail.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestBookList:
    """Tests for the book list (catalogue) view."""

    def test_book_list_shows_books(self, client, member_user, book):
        """An authenticated user can access the book list and see
        the book title in the response."""
        client.force_login(member_user)
        url = reverse('library:book_list')
        response = client.get(url)

        assert response.status_code == 200
        assert book.title.encode() in response.content

    def test_book_list_requires_login(self, client):
        """An unauthenticated user is redirected to the login page."""
        url = reverse('library:book_list')
        response = client.get(url)

        assert response.status_code == 302
        assert '/login/' in response.url


@pytest.mark.django_db
class TestBookDetail:
    """Tests for the book detail view."""

    def test_book_detail_renders(self, client, member_user, book):
        """An authenticated user can view a book's detail page with
        correct context (can_checkout=True when no active loan)."""
        client.force_login(member_user)
        url = reverse('library:book_detail', kwargs={'pk': book.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['book'] == book
        assert response.context['can_checkout'] is True
        assert response.context['has_active_loan'] is False

    def test_book_detail_shows_checkout_disabled_when_already_loaned(
        self, client, member_user, book, active_loan
    ):
        """When the user already has an active loan for this book,
        can_checkout is False and has_active_loan is True."""
        client.force_login(member_user)
        url = reverse('library:book_detail', kwargs={'pk': book.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['has_active_loan'] is True
        assert response.context['can_checkout'] is False

    def test_book_detail_shows_checkout_disabled_when_no_copies(
        self, client, member_user, book
    ):
        """When a book has no available copies, can_checkout is False."""
        book.available_copies = 0
        book.save(update_fields=['available_copies'])

        client.force_login(member_user)
        url = reverse('library:book_detail', kwargs={'pk': book.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['can_checkout'] is False

    def test_book_detail_nonexistent_returns_404(self, client, member_user):
        """Requesting a non-existent book returns 404."""
        client.force_login(member_user)
        url = reverse('library:book_detail', kwargs={'pk': 99999})
        response = client.get(url)

        assert response.status_code == 404

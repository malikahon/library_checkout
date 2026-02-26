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

"""
Tests for user authentication: registration and login.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
class TestRegistration:
    """Tests for the user registration view."""

    def test_register_creates_user(self, client):
        """A valid POST to the register endpoint creates a new user
        and redirects to the login page."""
        url = reverse('library:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'Str0ng!Pass99',
            'password2': 'Str0ng!Pass99',
        }
        response = client.post(url, data)

        assert response.status_code == 302
        assert response.url == reverse('login')
        assert User.objects.filter(username='newuser').exists()

    def test_register_rejects_mismatched_passwords(self, client):
        """Registration fails when passwords do not match —
        re-renders the form (200) and no user is created."""
        url = reverse('library:register')
        data = {
            'username': 'baduser',
            'email': 'bad@example.com',
            'password1': 'Str0ng!Pass99',
            'password2': 'different_pass',
        }
        response = client.post(url, data)

        assert response.status_code == 200
        assert not User.objects.filter(username='baduser').exists()


@pytest.mark.django_db
class TestLogin:
    """Tests for the user login view."""

    def test_login_authenticates_user(self, client, member_user):
        """A valid POST to the login endpoint authenticates the user
        and redirects to LOGIN_REDIRECT_URL (/)."""
        url = reverse('login')
        data = {
            'username': 'member',
            'password': 'testpass123',
        }
        response = client.post(url, data)

        assert response.status_code == 302
        assert response.url == '/'

    def test_login_rejects_wrong_password(self, client, member_user):
        """Login with an incorrect password re-renders the form (200)
        and does not authenticate the user."""
        url = reverse('login')
        data = {
            'username': 'member',
            'password': 'wrongpassword',
        }
        response = client.post(url, data)

        assert response.status_code == 200

import pytest
from django.contrib.auth.models import User

from library.models import Book, Genre, Loan


@pytest.fixture
def member_user(db):
    """A regular (non-staff) authenticated user."""
    return User.objects.create_user(
        username='member',
        email='member@example.com',
        password='testpass123',
    )


@pytest.fixture
def staff_user(db):
    """A staff user with management privileges."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True,
    )


@pytest.fixture
def genre(db):
    """A single Genre instance."""
    return Genre.objects.create(name='Fiction')


@pytest.fixture
def book(db, genre):
    """A Book with 3 total / 3 available copies and one genre."""
    b = Book.objects.create(
        title='Test Book',
        author='Test Author',
        isbn='9781234567890',
        total_copies=3,
        available_copies=3,
    )
    b.genres.add(genre)
    return b


@pytest.fixture
def active_loan(db, member_user, book):
    """An active Loan linking member_user to book.

    Also decrements the book's available_copies to stay consistent.
    """
    loan = Loan.objects.create(member=member_user, book=book)
    book.available_copies -= 1
    book.save(update_fields=['available_copies'])
    return loan

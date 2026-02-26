from django.conf import settings
from django.db import models
from django.db.models import Q


class Genre(models.Model):
    """A lookup/tag model used to categorise books."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Genres'

    def __str__(self):
        return self.name


class Book(models.Model):
    """Represents an individual title in the library catalogue."""

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    genres = models.ManyToManyField(Genre, blank=True, related_name='books')
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        constraints = [
            models.CheckConstraint(
                condition=Q(available_copies__gte=0),
                name='available_copies_non_negative',
            ),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"


class Loan(models.Model):
    """Records a single lending transaction between a Member and a Book."""

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loans',
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='loans',
    )
    checked_out_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-checked_out_at']
        constraints = [
            models.UniqueConstraint(
                fields=['member', 'book'],
                condition=Q(is_active=True),
                name='unique_active_loan_per_member_book',
            ),
        ]

    def __str__(self):
        return f"{self.member.username} — {self.book.title}"

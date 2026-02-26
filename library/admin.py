from django.contrib import admin

from .models import Book, Genre, Loan


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'isbn',
        'total_copies',
        'available_copies',
        'added_at',
    )
    list_filter = ('genres',)
    search_fields = ('title', 'author', 'isbn')
    filter_horizontal = ('genres',)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'member',
        'book',
        'checked_out_at',
        'returned_at',
        'is_active',
    )
    list_filter = ('is_active',)
    search_fields = ('member__username', 'book__title')
    raw_id_fields = ('member', 'book')

from django.core.management.base import BaseCommand

from library.models import Book, Genre


BOOKS = [
    # Fiction
    {
        "title": "The Women",
        "author": "Kristin Hannah",
        "isbn": "9781250178633",
        "genres": ["Fiction", "Historical Fiction"],
        "total_copies": 4,
    },
    {
        "title": "James",
        "author": "Percival Everett",
        "isbn": "9780385550369",
        "genres": ["Fiction", "Historical Fiction"],
        "total_copies": 3,
    },
    {
        "title": "The God of the Woods",
        "author": "Liz Moore",
        "isbn": "9780593472255",
        "genres": ["Fiction", "Mystery", "Thriller"],
        "total_copies": 3,
    },
    {
        "title": "All Fours",
        "author": "Miranda July",
        "isbn": "9781594634642",
        "genres": ["Fiction"],
        "total_copies": 2,
    },
    {
        "title": "The Familiar",
        "author": "Leigh Bardugo",
        "isbn": "9781250878984",
        "genres": ["Fiction", "Fantasy"],
        "total_copies": 3,
    },
    {
        "title": "Intermezzo",
        "author": "Sally Rooney",
        "isbn": "9780374611996",
        "genres": ["Fiction"],
        "total_copies": 4,
    },
    {
        "title": "The Life Impossible",
        "author": "Matt Haig",
        "isbn": "9780593449394",
        "genres": ["Fiction", "Fantasy"],
        "total_copies": 3,
    },
    {
        "title": "Here One Moment",
        "author": "Liane Moriarty",
        "isbn": "9781250343734",
        "genres": ["Fiction", "Mystery"],
        "total_copies": 3,
    },
    {
        "title": "The Frozen River",
        "author": "Ariel Lawhon",
        "isbn": "9780385548588",
        "genres": ["Fiction", "Historical Fiction", "Mystery"],
        "total_copies": 2,
    },
    {
        "title": "Wind and Truth",
        "author": "Brandon Sanderson",
        "isbn": "9780765326386",
        "genres": ["Fiction", "Fantasy"],
        "total_copies": 3,
    },
    # Nonfiction
    {
        "title": "Nexus",
        "author": "Yuval Noah Harari",
        "isbn": "9780593905968",
        "genres": ["Nonfiction", "History", "Science"],
        "total_copies": 4,
    },
    {
        "title": "Be Ready When the Luck Happens",
        "author": "Ina Garten",
        "isbn": "9780385550406",
        "genres": ["Nonfiction", "Biography"],
        "total_copies": 3,
    },
    {
        "title": "The Demon of Unrest",
        "author": "Erik Larson",
        "isbn": "9780385348720",
        "genres": ["Nonfiction", "History"],
        "total_copies": 3,
    },
    {
        "title": "Revenge of the Tipping Point",
        "author": "Malcolm Gladwell",
        "isbn": "9780316575805",
        "genres": ["Nonfiction", "Science"],
        "total_copies": 4,
    },
    {
        "title": "What I Ate in One Year",
        "author": "Stanley Tucci",
        "isbn": "9781668064825",
        "genres": ["Nonfiction", "Biography"],
        "total_copies": 2,
    },
    {
        "title": "Nuclear War: A Scenario",
        "author": "Annie Jacobsen",
        "isbn": "9780593476093",
        "genres": ["Nonfiction", "History", "Science"],
        "total_copies": 3,
    },
    {
        "title": "The Wide Wide Sea",
        "author": "Hampton Sides",
        "isbn": "9780385545716",
        "genres": ["Nonfiction", "History"],
        "total_copies": 2,
    },
    {
        "title": "Onyx Storm",
        "author": "Rebecca Yarros",
        "isbn": "9781649374530",
        "genres": ["Fiction", "Fantasy", "Romance"],
        "total_copies": 5,
    },
    {
        "title": "The Secret History",
        "author": "Donna Tartt",
        "isbn": "9780679410324",
        "genres": ["Fiction", "Mystery", "Thriller"],
        "total_copies": 3,
    },
    {
        "title": "Atomic Habits",
        "author": "James Clear",
        "isbn": "9780735211292",
        "genres": ["Nonfiction", "Self-Help"],
        "total_copies": 5,
    },
]


class Command(BaseCommand):
    help = "Populate the library with NYT bestselling books"

    def handle(self, *args, **options):
        created_books = 0
        skipped_books = 0
        genre_cache = {}

        for book_data in BOOKS:
            genres = []
            for genre_name in book_data["genres"]:
                if genre_name not in genre_cache:
                    genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
                    genre_cache[genre_name] = genre_obj
                genres.append(genre_cache[genre_name])

            copies = book_data["total_copies"]
            book, created = Book.objects.get_or_create(
                title=book_data["title"],
                author=book_data["author"],
                defaults={
                    "isbn": book_data["isbn"],
                    "total_copies": copies,
                    "available_copies": copies,
                },
            )

            if created:
                book.genres.set(genres)
                created_books += 1
                self.stdout.write(f"  Created: {book}")
            else:
                skipped_books += 1
                self.stdout.write(f"  Skipped (already exists): {book}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {created_books} book(s) created, {skipped_books} skipped."
            )
        )

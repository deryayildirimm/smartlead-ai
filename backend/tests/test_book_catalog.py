import pytest
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client

from accounts.models import User
from reading.models import Author, Book, BookAuthor, BookGenre, Genre

pytestmark = pytest.mark.django_db
BOOK_ADD_URL = "/admin/reading/book/add/"


@pytest.fixture
def catalog_form():
    first = Author.objects.create(name="İlk yazar")
    second = Author.objects.create(name="İkinci yazar")
    fantasy = Genre.objects.get(code="fantasy")
    philosophy = Genre.objects.get(code="philosophy")
    return {
        "title": "Deneme kitabı",
        "description": "Yerel katalog denemesi.",
        "original_language": "",
        "author_links-TOTAL_FORMS": "2",
        "author_links-INITIAL_FORMS": "0",
        "author_links-MIN_NUM_FORMS": "0",
        "author_links-MAX_NUM_FORMS": "1000",
        "author_links-0-author": str(first.pk),
        "author_links-0-position": "2",
        "author_links-1-author": str(second.pk),
        "author_links-1-position": "1",
        "genre_links-TOTAL_FORMS": "2",
        "genre_links-INITIAL_FORMS": "0",
        "genre_links-MIN_NUM_FORMS": "0",
        "genre_links-MAX_NUM_FORMS": "1000",
        "genre_links-0-genre": str(fantasy.pk),
        "genre_links-1-genre": str(philosophy.pk),
        "_save": "Kaydet",
    }


@pytest.fixture
def catalog_admin():
    user = User.objects.create_superuser("catalog-admin@example.com", "catalog-test-password-only")
    client = Client()
    client.force_login(user)
    return client


def test_admin_can_save_and_reopen_a_book_with_multiple_authors_and_genres(
    catalog_admin, catalog_form
):
    response = catalog_admin.post(BOOK_ADD_URL, catalog_form)
    assert response.status_code == 302
    book = Book.objects.get(title=catalog_form["title"])
    assert book.original_language == ""
    assert book.description == catalog_form["description"]
    assert list(book.author_links.values_list("author_id", flat=True)) == [
        int(catalog_form["author_links-1-author"]),
        int(catalog_form["author_links-0-author"]),
    ]
    assert set(book.genres.values_list("code", flat=True)) == {"fantasy", "philosophy"}
    assert catalog_admin.get(f"/admin/reading/book/{book.pk}/change/").status_code == 200


@pytest.mark.parametrize("prefix,field", [("author_links", "author"), ("genre_links", "genre")])
def test_duplicate_inline_links_do_not_save_a_partial_book(
    catalog_admin, catalog_form, prefix, field
):
    catalog_form[f"{prefix}-1-{field}"] = catalog_form[f"{prefix}-0-{field}"]
    response = catalog_admin.post(BOOK_ADD_URL, catalog_form)
    assert response.status_code == 200
    assert not Book.objects.exists()
    assert not BookAuthor.objects.exists()
    assert not BookGenre.objects.exists()


@pytest.mark.parametrize("invalid_change", ["duplicate_author", "duplicate_genre", "zero_position"])
def test_database_rejects_invalid_catalog_links(invalid_change):
    book = Book.objects.create(title="Katalog denemesi")
    author = Author.objects.create(name="Deneme yazarı")
    genre = Genre.objects.get(code="fantasy")
    link = BookAuthor.objects.create(book=book, author=author)
    BookGenre.objects.create(book=book, genre=genre)
    with pytest.raises(IntegrityError), transaction.atomic():
        if invalid_change == "duplicate_author":
            BookAuthor.objects.create(book=book, author=author, position=2)
        elif invalid_change == "duplicate_genre":
            BookGenre.objects.create(book=book, genre=genre)
        else:
            BookAuthor.objects.filter(pk=link.pk).update(position=0)


def test_removing_a_book_keeps_authors_and_genres_but_removes_links():
    book = Book.objects.create(title="Silme davranışı denemesi")
    author = Author.objects.create(name="Korunan yazar")
    genre = Genre.objects.get(code="fantasy")
    book.authors.add(author)
    book.genres.add(genre)
    with pytest.raises(ProtectedError):
        author.delete()
    with pytest.raises(ProtectedError):
        genre.delete()
    book.delete()
    assert not BookAuthor.objects.exists()
    assert not BookGenre.objects.exists()
    assert Author.objects.filter(pk=author.pk).exists()
    assert Genre.objects.filter(pk=genre.pk).exists()

"""
Management command: fix_missing_covers
Busca libros sin portada e intenta encontrar una usando Open Library y Google Books.
Solo toca los que NO tienen portada; los demas quedan intactos.

Uso:
    python manage.py fix_missing_covers
    python manage.py fix_missing_covers --dry-run
    python manage.py fix_missing_covers --limit 50
"""
import time
import requests
from urllib.parse import quote
from django.core.management.base import BaseCommand
from django.db.models import Q
from books.models import Book, UserBook, UserBookExternal


class Command(BaseCommand):
    help = 'Busca portadas faltantes y las completa desde Open Library / Google Books'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Solo mostrar, sin modificar')
        parser.add_argument('--limit', type=int, default=0, help='Limitar cantidad (0=todos)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Fix Missing Covers ===\n'))
        total_fixed = 0
        total_failed = 0

        # UserBookExternal sin portada
        self.stdout.write(self.style.HTTP_INFO('\n-- UserBookExternal --'))
        externals = UserBookExternal.objects.filter(
            Q(custom_cover__isnull=True) | Q(custom_cover='')
        ).filter(
            Q(cover_url__isnull=True) | Q(cover_url='')
        ).distinct()
        if limit > 0:
            externals = externals[:limit]
        self.stdout.write(f'  Sin portada: {externals.count()}')

        for book in externals:
            self.stdout.write(f'\n  [{book.id}] "{book.title}" por {book.author}')
            if dry_run:
                continue
            cover_url = self._find_cover(book.title, book.author, book.isbn, book.ol_key)
            if cover_url:
                book.cover_url = cover_url
                book.save(update_fields=['cover_url'])
                self.stdout.write(self.style.SUCCESS(f'    OK'))
                total_fixed += 1
            else:
                self.stdout.write(self.style.WARNING(f'    No encontrada'))
                total_failed += 1
            time.sleep(0.3)

        # UserBook con libro sin portada
        self.stdout.write(self.style.HTTP_INFO('\n-- UserBook --'))
        ub_no_cover = UserBook.objects.filter(
            Q(book__cover_image_url__isnull=True) | Q(book__cover_image_url='')
        ).filter(
            Q(custom_cover__isnull=True) | Q(custom_cover='')
        ).filter(
            Q(ol_cover_url__isnull=True) | Q(ol_cover_url='')
        ).select_related('book', 'book__author').distinct()
        if limit > 0:
            ub_no_cover = ub_no_cover[:limit]
        self.stdout.write(f'  Sin portada: {ub_no_cover.count()}')
        updated_book_ids = set()

        for ub in ub_no_cover:
            book = ub.book
            author_name = book.author.name if book.author else ''
            self.stdout.write(f'\n  [{ub.id}] "{book.title}" por {author_name}')
            if dry_run:
                continue
            if book.id in updated_book_ids:
                if book.cover_image_url:
                    ub.ol_cover_url = book.cover_image_url
                    ub.save(update_fields=['ol_cover_url'])
                    total_fixed += 1
                continue
            cover_url = self._find_cover(book.title, author_name, book.isbn, ub.ol_key)
            if cover_url:
                book.cover_image_url = cover_url
                book.save(update_fields=['cover_image_url'])
                ub.ol_cover_url = cover_url
                ub.save(update_fields=['ol_cover_url'])
                updated_book_ids.add(book.id)
                self.stdout.write(self.style.SUCCESS(f'    OK'))
                total_fixed += 1
            else:
                self.stdout.write(self.style.WARNING(f'    No encontrada'))
                total_failed += 1
            time.sleep(0.3)

        # Books del catalogo sin portada
        self.stdout.write(self.style.HTTP_INFO('\n-- Book (catalogo) --'))
        catalog = Book.objects.filter(
            Q(cover_image_url__isnull=True) | Q(cover_image_url='')
        ).exclude(id__in=updated_book_ids).select_related('author').distinct()
        if limit > 0:
            catalog = catalog[:limit]
        self.stdout.write(f'  Sin portada: {catalog.count()}')

        for book in catalog:
            author_name = book.author.name if book.author else ''
            self.stdout.write(f'\n  [{book.id}] "{book.title}" por {author_name}')
            if dry_run:
                continue
            cover_url = self._find_cover(book.title, author_name, book.isbn)
            if cover_url:
                book.cover_image_url = cover_url
                book.save(update_fields=['cover_image_url'])
                self.stdout.write(self.style.SUCCESS(f'    OK'))
                total_fixed += 1
            else:
                self.stdout.write(self.style.WARNING(f'    No encontrada'))
                total_failed += 1
            time.sleep(0.3)

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Resumen ==='))
        if dry_run:
            self.stdout.write('  Modo DRY RUN (no se modifico nada)')
        else:
            self.stdout.write(self.style.SUCCESS(f'  Arregladas: {total_fixed}'))
            self.stdout.write(self.style.WARNING(f'  Sin resultado: {total_failed}'))

    def _find_cover(self, title, author, isbn=None, ol_key=None):
        if isbn:
            url = f'https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg'
            if self._is_valid_cover(url):
                return url
        if ol_key:
            try:
                resp = requests.get(f'https://openlibrary.org{ol_key}.json', timeout=5)
                if resp.status_code == 200:
                    covers = resp.json().get('covers', [])
                    if covers:
                        cv = f'https://covers.openlibrary.org/b/id/{covers[0]}-M.jpg'
                        if self._is_valid_cover(cv):
                            return cv
            except Exception:
                pass
        try:
            query = quote(f'{title} {author}')
            resp = requests.get(f'https://openlibrary.org/search.json?q={query}&limit=1&fields=cover_i,isbn', timeout=5)
            if resp.status_code == 200:
                docs = resp.json().get('docs', [])
                if docs:
                    cid = docs[0].get('cover_i')
                    if cid:
                        return f'https://covers.openlibrary.org/b/id/{cid}-M.jpg'
        except Exception:
            pass
        try:
            q = quote(f'intitle:{title}+inauthor:{author}')
            resp = requests.get(f'https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=1&fields=items(volumeInfo/imageLinks)', timeout=5)
            if resp.status_code == 200:
                items = resp.json().get('items', [])
                if items:
                    links = items[0].get('volumeInfo', {}).get('imageLinks', {})
                    url = links.get('thumbnail') or links.get('smallThumbnail')
                    if url:
                        return url.replace('http://', 'https://')
        except Exception:
            pass
        return None

    def _is_valid_cover(self, url):
        try:
            resp = requests.head(url, timeout=3, allow_redirects=True)
            cl = int(resp.headers.get('content-length', '0'))
            return resp.status_code == 200 and cl > 1000
        except Exception:
            return False

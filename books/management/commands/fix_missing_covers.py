"""
Management command: fix_missing_covers

Busca libros sin portada en UserBookExternal, UserBook y Book,
e intenta encontrar una portada usando Open Library y Google Books.
Solo toca los que NO tienen portada; los demas quedan intactos.

Uso:
    python manage.py fix_missing_covers              # Procesa todos
    python manage.py fix_missing_covers --dry-run    # Solo muestra cuales faltan
    python manage.py fix_missing_covers --limit 50   # Procesa solo 50
"""

import time
import requests
from urllib.parse import quote
from django.core.management.base import BaseCommand
from books.models import Book, UserBook, UserBookExternal


class Command(BaseCommand):
    help = 'Busca portadas faltantes en la biblioteca y las completa desde Open Library / Google Books'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar libros sin portada, sin modificar nada',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limitar cantidad de libros a procesar (0 = todos)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== Fix Missing Covers ===\n'
        ))

        total_fixed = 0
        total_failed = 0
        total_skipped = 0

        # ── 1. UserBookExternal sin portada ──────────────────────────
        self.stdout.write(self.style.HTTP_INFO(
            '\n── UserBookExternal (libros de Open Library) ──'
        ))
        externals = UserBookExternal.objects.filter(
            custom_cover='',
        ).filter(
            # cover_url vacio o nulo
            cover_url__isnull=True,
        ) | UserBookExternal.objects.filter(
            custom_cover='',
            cover_url='',
        )
        # Tambien incluir los que tienen custom_cover nulo
        externals = externals | UserBookExternal.objects.filter(
            custom_cover__isnull=True,
            cover_url__isnull=True,
        ) | UserBookExternal.objects.filter(
            custom_cover__isnull=True,
            cover_url='',
        )
        externals = externals.distinct()

        if limit > 0:
            externals = externals[:limit]

        self.stdout.write(f'  Encontrados sin portada: {externals.count()}')

        for book in externals:
            self.stdout.write(f'\n  [{book.id}] "{book.title}" por {book.author}')
            if dry_run:
                total_skipped += 1
                continue

            cover_url = self._find_cover(
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                ol_key=book.ol_key,
            )
            if cover_url:
                book.cover_url = cover_url
                book.save(update_fields=['cover_url'])
                self.stdout.write(self.style.SUCCESS(f'    ✓ Portada encontrada'))
                total_fixed += 1
            else:
                self.stdout.write(self.style.WARNING(f'    ✗ No se encontro portada'))
                total_failed += 1

            time.sleep(0.3)  # Rate limiting

        # ── 2. UserBook con libro del catalogo sin portada ───────────
        self.stdout.write(self.style.HTTP_INFO(
            '\n── UserBook (libros del catalogo interno) ──'
        ))
        # UserBooks donde el Book asociado no tiene cover Y el UserBook no tiene custom_cover ni ol_cover_url
        user_books_no_cover = UserBook.objects.filter(
            book__cover_image_url__isnull=True,
            custom_cover='',
            ol_cover_url__isnull=True,
        ) | UserBook.objects.filter(
            book__cover_image_url='',
            custom_cover='',
            ol_cover_url__isnull=True,
        ) | UserBook.objects.filter(
            book__cover_image_url__isnull=True,
            custom_cover__isnull=True,
            ol_cover_url__isnull=True,
        ) | UserBook.objects.filter(
            book__cover_image_url='',
            custom_cover__isnull=True,
            ol_cover_url__isnull=True,
        ) | UserBook.objects.filter(
            book__cover_image_url__isnull=True,
            custom_cover='',
            ol_cover_url='',
        ) | UserBook.objects.filter(
            book__cover_image_url='',
            custom_cover='',
            ol_cover_url='',
        ) | UserBook.objects.filter(
            book__cover_image_url__isnull=True,
            custom_cover__isnull=True,
            ol_cover_url='',
        ) | UserBook.objects.filter(
            book__cover_image_url='',
            custom_cover__isnull=True,
            ol_cover_url='',
        )
        user_books_no_cover = user_books_no_cover.select_related('book', 'book__author').distinct()

        if limit > 0:
            user_books_no_cover = user_books_no_cover[:limit]

        self.stdout.write(f'  Encontrados sin portada: {user_books_no_cover.count()}')

        # Track Book IDs already updated to avoid duplicate API calls
        updated_book_ids = set()

        for ub in user_books_no_cover:
            book = ub.book
            author_name = book.author.name if book.author else ''
            self.stdout.write(f'\n  [{ub.id}] "{book.title}" por {author_name}')

            if dry_run:
                total_skipped += 1
                continue

            # Si ya actualizamos este Book del catalogo, solo actualizar ol_cover_url
            if book.id in updated_book_ids:
                if book.cover_image_url:
                    ub.ol_cover_url = book.cover_image_url
                    ub.save(update_fields=['ol_cover_url'])
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Reutilizando portada del catalogo'))
                    total_fixed += 1
                continue

            cover_url = self._find_cover(
                title=book.title,
                author=author_name,
                isbn=book.isbn,
                ol_key=ub.ol_key,
            )
            if cover_url:
                # Actualizar tanto el Book del catalogo como el UserBook
                book.cover_image_url = cover_url
                book.save(update_fields=['cover_image_url'])
                ub.ol_cover_url = cover_url
                ub.save(update_fields=['ol_cover_url'])
                updated_book_ids.add(book.id)
                self.stdout.write(self.style.SUCCESS(f'    ✓ Portada encontrada'))
                total_fixed += 1
            else:
                self.stdout.write(self.style.WARNING(f'    ✗ No se encontro portada'))
                total_failed += 1

            time.sleep(0.3)

        # ── 3. Books del catalogo sin portada (sin UserBook asociado) ─
        self.stdout.write(self.style.HTTP_INFO(
            '\n── Book (catalogo general) ──'
        ))
        catalog_no_cover = Book.objects.filter(
            cover_image_url__isnull=True
        ) | Book.objects.filter(
            cover_image_url=''
        )
        catalog_no_cover = catalog_no_cover.exclude(
            id__in=updated_book_ids
        ).select_related('author').distinct()

        if limit > 0:
            catalog_no_cover = catalog_no_cover[:limit]

        self.stdout.write(f'  Encontrados sin portada: {catalog_no_cover.count()}')

        for book in catalog_no_cover:
            author_name = book.author.name if book.author else ''
            self.stdout.write(f'\n  [{book.id}] "{book.title}" por {author_name}')

            if dry_run:
                total_skipped += 1
                continue

            cover_url = self._find_cover(
                title=book.title,
                author=author_name,
                isbn=book.isbn,
            )
            if cover_url:
                book.cover_image_url = cover_url
                book.save(update_fields=['cover_image_url'])
                self.stdout.write(self.style.SUCCESS(f'    ✓ Portada encontrada'))
                total_fixed += 1
            else:
                self.stdout.write(self.style.WARNING(f'    ✗ No se encontro portada'))
                total_failed += 1

            time.sleep(0.3)

        # ── Resumen ──────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Resumen ==='))
        if dry_run:
            self.stdout.write(f'  Modo: DRY RUN (no se modifico nada)')
            self.stdout.write(f'  Libros sin portada encontrados: {total_skipped}')
        else:
            self.stdout.write(self.style.SUCCESS(f'  Portadas encontradas y actualizadas: {total_fixed}'))
            self.stdout.write(self.style.WARNING(f'  Sin portada disponible: {total_failed}'))
        self.stdout.write('')

    def _find_cover(self, title, author, isbn=None, ol_key=None):
        """
        Pipeline de busqueda de portada (misma logica que CoverFallbackService en Flutter):
        1. Open Library por ISBN
        2. Open Library por busqueda
        3. Google Books API
        """
        # 1. Open Library por ISBN
        if isbn:
            url = f'https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg'
            if self._is_valid_cover(url):
                return url

        # 2. Open Library por ol_key (cover_id)
        if ol_key:
            try:
                # Intentar obtener cover_id desde la API de Open Library
                api_url = f'https://openlibrary.org{ol_key}.json'
                resp = requests.get(api_url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    covers = data.get('covers', [])
                    if covers:
                        cover_url = f'https://covers.openlibrary.org/b/id/{covers[0]}-M.jpg'
                        if self._is_valid_cover(cover_url):
                            return cover_url
            except Exception as e:
                self.stdout.write(f'    OL key lookup error: {e}')

        # 3. Open Library por busqueda
        try:
            query = quote(f'{title} {author}')
            resp = requests.get(
                f'https://openlibrary.org/search.json?q={query}&limit=1&fields=cover_i,isbn',
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get('docs', [])
                if docs:
                    cover_id = docs[0].get('cover_i')
                    if cover_id:
                        url = f'https://covers.openlibrary.org/b/id/{cover_id}-M.jpg'
                        return url
        except Exception as e:
            self.stdout.write(f'    OL search error: {e}')

        # 4. Google Books API
        try:
            q = quote(f'intitle:{title}+inauthor:{author}')
            resp = requests.get(
                f'https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=1&fields=items(volumeInfo/imageLinks)',
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('items', [])
                if items:
                    links = items[0].get('volumeInfo', {}).get('imageLinks', {})
                    url = links.get('thumbnail') or links.get('smallThumbnail')
                    if url:
                        return url.replace('http://', 'https://')
        except Exception as e:
            self.stdout.write(f'    Google Books error: {e}')

        return None

    def _is_valid_cover(self, url):
        """Verifica que la URL devuelve una imagen real (no un placeholder de 1x1 px)."""
        try:
            resp = requests.head(url, timeout=3, allow_redirects=True)
            content_length = int(resp.headers.get('content-length', '0'))
            return resp.status_code == 200 and content_length > 1000
        except Exception:
            return False

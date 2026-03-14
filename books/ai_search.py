from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json
import urllib.request
import urllib.parse
from openai import OpenAI

_SEARCH_SCHEMA = """{
  "intent": "author|publisher|book|general|isbn|natural_query",
  "canonical_name": "Nombre exacto y canónico del autor/editorial/libro/isbn descubierto",
  "google_books_query": "Consulta perfecta para Google Books (ej: inauthor:\\"Diego Fischer\\" o isbn:\\"9788415594828\\")",
  "language_filter": "es|en|pt|fr|it|de|all (idioma detectado en la consulta, default: all)",
  "reason": "Explicación breve de lo que entendiste"
}"""

_VALID_LANGUAGES = {'es', 'en', 'pt', 'fr', 'it', 'de', 'all'}


def _analyze_search_intent(query: str) -> dict:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_msg = (
        "Eres un experto bibliotecario. El usuario ingresa un término de búsqueda (puede tener errores). "
        "Tu trabajo es clasificar la intención y construir la consulta perfecta para Google Books. "
        "REGLAS:\n"
        "1. Corrige errores ortográficos en nombres de autores y libros.\n"
        "2. Si el usuario menciona un idioma (ej: 'en español', 'in english'), extráelo en language_filter.\n"
        "3. Si dice 'Diego Fisher', el canónico es 'Diego Fischer', intent='author', query='inauthor:\"Diego Fischer\"'.\n"
        "4. Si dice 'Planeta', intent='publisher', query='inpublisher:\"Planeta\"'.\n"
        "5. Si ingresa un número de 10-13 dígitos, intent='isbn', query='isbn:<número>'.\n"
        "6. Para consultas naturales como 'libros de misterio de Agatha Christie', intent='natural_query'.\n"
        "7. Si el usuario NO menciona idioma, language_filter='all'.\n"
        "Devuelve estrictamente JSON válido: " + _SEARCH_SCHEMA
    )

    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': f"Query: {query}"}
            ],
            response_format={'type': 'json_object'},
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI Intent Error: {e}")
        return {}


def _fetch_from_google_books(query: str, max_results: int = 40, lang: str = 'all', start_index: int = 0) -> list:
    """Fetch results from Google Books using a specific query string."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}&maxResults={max_results}&startIndex={start_index}&key={settings.GOOGLE_BOOKS_API_KEY}&printType=books"

    # Apply language restriction only if not 'all'
    if lang and lang != 'all':
        url += f"&langRestrict={lang}"

    results = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            items = data.get('items', [])
            for item in items:
                vol = item.get('volumeInfo', {})
                authors = vol.get('authors', [])

                # Covers
                images = vol.get('imageLinks', {})
                cover = images.get('thumbnail', '')
                if cover:
                    cover = cover.replace('http://', 'https://')
                    if 'zoom=' not in cover:
                        cover += '&zoom=1'

                # Extract ISBN
                identifiers = vol.get('industryIdentifiers', [])
                isbn = None
                for idx in identifiers:
                    if idx.get('type') in ['ISBN_13', 'ISBN_10']:
                        isbn = idx.get('identifier')
                        break

                # Extract Categories
                categories = vol.get('categories', [])
                categories_str = ", ".join(categories) if categories else None

                # Language
                book_language = vol.get('language', '')

                # Pages and Chapters
                page_count = vol.get('pageCount')
                total_chapters = 10
                if page_count and page_count > 0:
                    total_chapters = max(1, page_count // 10)

                results.append({
                    'title': vol.get('title', 'Sin título'),
                    'author': ", ".join(authors) if authors else 'Autor desconocido',
                    'description': vol.get('description', ''),
                    'cover_url': cover,
                    'source': 'google_books',
                    'google_books_id': item.get('id'),
                    'olid': None,
                    'publish_date': vol.get('publishedDate'),
                    'publisher': vol.get('publisher'),
                    'categories': categories_str,
                    'isbn': isbn,
                    'page_count': page_count,
                    'total_chapters': total_chapters,
                    'language': book_language,
                })
    except Exception as e:
        print(f"Google Books API Error: {e}")

    return results


def _deduplicate_books(books: list) -> list:
    """
    Remove duplicate editions of the same book.
    Keeps the version with the best cover and most metadata.
    """
    seen = {}
    for book in books:
        # Normalize title for comparison
        title_key = book['title'].lower().strip()
        # Remove common subtitle patterns for grouping
        for sep in [':', ' - ', ' – ', ' — ']:
            if sep in title_key:
                title_key = title_key.split(sep)[0].strip()

        author_key = book['author'].lower().strip().split(',')[0].strip()
        dedup_key = f"{title_key}|{author_key}"

        if dedup_key not in seen:
            seen[dedup_key] = book
        else:
            existing = seen[dedup_key]
            # Prefer the one with cover, more metadata, and ISBN
            new_score = 0
            old_score = 0
            if book.get('cover_url'):
                new_score += 2
            if existing.get('cover_url'):
                old_score += 2
            if book.get('isbn'):
                new_score += 1
            if existing.get('isbn'):
                old_score += 1
            if book.get('description'):
                new_score += 1
            if existing.get('description'):
                old_score += 1
            if book.get('page_count'):
                new_score += 1
            if existing.get('page_count'):
                old_score += 1

            if new_score > old_score:
                seen[dedup_key] = book

    return list(seen.values())


class AISearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        lang = request.query_params.get('lang', '').strip().lower()
        page = int(request.query_params.get('page', '0'))

        if not query:
            return Response({'metadata': None, 'results': [], 'has_more': False})

        # 1. Ask AI to decipher intent
        intent_data = _analyze_search_intent(query)
        if not intent_data or 'google_books_query' not in intent_data:
            return Response({'metadata': None, 'results': [], 'has_more': False})

        gb_query = intent_data['google_books_query']
        intent_type = intent_data.get('intent', 'general')
        canonical = intent_data.get('canonical_name', query)

        # Determine language: explicit param > AI-detected > 'all'
        ai_lang = intent_data.get('language_filter', 'all')
        effective_lang = lang if lang in _VALID_LANGUAGES else (ai_lang if ai_lang in _VALID_LANGUAGES else 'all')

        # 1.5 Local search in our community catalog
        from django.db.models import Q
        from .models import Book
        local_results = []
        if page == 0:  # Only search local on first page
            local_books_qs = Book.objects.filter(is_community_added=True).filter(
                Q(title__icontains=canonical) | Q(author__name__icontains=canonical) | Q(isbn=canonical)
            )[:5]
            for lb in local_books_qs:
                local_results.append({
                    'title': lb.title,
                    'author': lb.author.name if lb.author else 'Autor desconocido',
                    'description': lb.synopsis or 'Libro agregado por la comunidad.',
                    'cover_url': lb.cover_image_url,
                    'source': 'community',
                    'google_books_id': f"local_{lb.id}",
                    'olid': None,
                    'publish_date': lb.publish_date,
                    'publisher': lb.publisher,
                    'categories': lb.categories,
                    'isbn': lb.isbn,
                    'page_count': lb.page_count,
                    'total_chapters': max(1, lb.page_count // 10) if lb.page_count else 10,
                    'language': '',
                })

        # 2. Fetch from Google Books with pagination
        start_index = page * 40
        books = _fetch_from_google_books(gb_query, max_results=40, lang=effective_lang, start_index=start_index)

        # 3. Deduplicate
        books = _deduplicate_books(books)

        # Merge results, putting local results first
        final_results = local_results + books if page == 0 else books

        # Build metadata header
        metadata = {
            'intent': intent_type,
            'canonical_name': canonical,
            'reason': intent_data.get('reason', ''),
            'language': effective_lang,
        }

        # Check if there might be more results
        has_more = len(books) >= 15  # If we got at least 15 after dedup, there's likely more

        return Response({
            'metadata': metadata,
            'results': final_results,
            'has_more': has_more,
        })

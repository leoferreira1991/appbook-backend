"""
API endpoint to fix missing book covers.
"""
import time, threading, requests as http_requests
from urllib.parse import quote
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Book, UserBook, UserBookExternal

def _is_valid_cover(url):
    try:
        resp = http_requests.head(url, timeout=3, allow_redirects=True)
        cl = int(resp.headers.get('content-length', '0'))
        return resp.status_code == 200 and cl > 1000
    except Exception:
        return False

def _find_cover(title, author, isbn=None, ol_key=None):
    if isbn:
        url = f'https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg'
        if _is_valid_cover(url):
            return url
    if ol_key:
        try:
            resp = http_requests.get(f'https://openlibrary.org{ol_key}.json', timeout=5)
            if resp.status_code == 200:
                covers = resp.json().get('covers', [])
                if covers:
                    cv = f'https://covers.openlibrary.org/b/id/{covers[0]}-M.jpg'
                    if _is_valid_cover(cv):
                        return cv
        except Exception:
            pass
    try:
        query = quote(f'{title} {author}')
        resp = http_requests.get(f'https://openlibrary.org/search.json?q={query}&limit=1&fields=cover_i,isbn', timeout=5)
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
        resp = http_requests.get(f'https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=1&fields=items(volumeInfo/imageLinks)', timeout=5)
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

def _get_books_without_covers():
    from django.db.models import Q
    return UserBookExternal.objects.filter(Q(custom_cover__isnull=True)|Q(custom_cover='')).filter(Q(cover_url__isnull=True)|Q(cover_url='')).distinct()

def _run_fix_covers_background(user_id=None):
    qs = _get_books_without_covers()
    if user_id:
        qs = qs.filter(user_id=user_id)
    fixed = 0
    failed = 0
    for book in qs:
        cover_url = _find_cover(title=book.title, author=book.author, isbn=book.isbn, ol_key=book.ol_key)
        if cover_url:
            book.cover_url = cover_url
            book.save(update_fields=['cover_url'])
            fixed += 1
        else:
            failed += 1
        time.sleep(0.3)
    print(f'[fix_covers] Done: {fixed} fixed, {failed} failed')
    return fixed, failed

class FixMissingCoversView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        mode = request.data.get('mode', 'check')
        scope = request.data.get('scope', 'mine')
        if scope == 'all' and not request.user.is_staff:
            return Response({'error': 'Solo administradores.'}, status=status.HTTP_403_FORBIDDEN)
        user_id = request.user.id if scope == 'mine' else None
        qs = _get_books_without_covers()
        if user_id:
            qs = qs.filter(user_id=user_id)
        missing_count = qs.count()
        if mode == 'check':
            books_info = [{'id':b.id,'title':b.title,'author':b.author,'isbn':b.isbn or '','ol_key':b.ol_key or ''} for b in qs[:50]]
            return Response({'missing_covers': missing_count, 'preview': books_info})
        elif mode == 'fix':
            thread = threading.Thread(target=_run_fix_covers_background, args=(user_id,), daemon=True)
            thread.start()
            return Response({'status':'started','message':f'Buscando portadas para {missing_count} libros...','missing_covers':missing_count})
        elif mode == 'fix-sync':
            if missing_count > 20:
                return Response({'error':f'Demasiados ({missing_count}). Usa mode=fix.'}, status=status.HTTP_400_BAD_REQUEST)
            fixed, failed = _run_fix_covers_background(user_id)
            return Response({'status':'completed','fixed':fixed,'failed':failed,'total_processed':fixed+failed})
        return Response({'error':'mode debe ser check, fix o fix-sync'}, status=status.HTTP_400_BAD_REQUEST)

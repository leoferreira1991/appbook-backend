from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI
import json


SYSTEM_PROMPT = (
    "Eres un experto bibliotecario y crítico literario. Dado un título y autor de un libro, "
    "devuelve información enriquecida en JSON con estos campos:\n"
    "- genre: género principal del libro en español\n"
    "- subgenres: lista de hasta 3 subgéneros en español\n"
    "- synopsis: sinopsis breve del libro en español (3-4 oraciones, sin spoilers)\n"
    "- trivia: un dato curioso sobre el libro o su autor en español\n"
    "- author_bio: biografía breve del autor en español (2-3 oraciones)\n"
    "- author_canonical_name: nombre canónico/correcto del autor "
    "(ej: si el input dice 'Julio Verne', devolver 'Jules Verne')\n"
    "- suggested_page_count: número estimado de páginas si lo conoces, o null\n"
    "- suggested_total_chapters: número estimado de capítulos si lo conoces, o null\n"
    "- year_published: año de primera publicación (string), o null\n"
    "- publisher: editorial más conocida en español si lo sabes, o null\n"
    "- isbn: ISBN-13 si lo conoces, o null\n"
    "- themes: lista de hasta 5 temas/palabras clave del libro en español\n"
    "- ai_review: una reseña breve y equilibrada del libro (3-4 oraciones, en español, "
    "mencionando puntos fuertes y a quién le podría gustar)\n\n"
    "Devuelve SOLO JSON válido, sin markdown ni texto extra."
)


def _enrich_book_record(book, enrichment, force=False):
    """Apply AI enrichment data to a UserBookExternal record."""
    updated = False
    
    # Genre / categories
    genre = enrichment.get('genre', '')
    subgenres = enrichment.get('subgenres', [])
    if genre and (not book.categories or force):
        cats = [genre] + (subgenres if subgenres else [])
        book.categories = ', '.join(cats)
        updated = True
    
    # Synopsis
    synopsis = enrichment.get('synopsis')
    if synopsis and (not book.synopsis or force):
        book.synopsis = synopsis
        updated = True
    
    # Author bio
    author_bio = enrichment.get('author_bio')
    if author_bio and (not book.author_bio or force):
        book.author_bio = author_bio
        updated = True
    
    # Trivia
    trivia = enrichment.get('trivia')
    if trivia and (not book.trivia or force):
        book.trivia = trivia
        updated = True
    
    # AI review
    ai_review = enrichment.get('ai_review')
    if ai_review and (not book.ai_review or force):
        book.ai_review = ai_review
        updated = True
    
    # Themes
    themes = enrichment.get('themes', [])
    if themes and (not book.themes or force):
        book.themes = ', '.join(themes) if isinstance(themes, list) else themes
        updated = True
    
    # Year published
    year = enrichment.get('year_published')
    if year and (not book.year_published or force):
        book.year_published = str(year)
        updated = True
    
    # Publisher
    publisher = enrichment.get('publisher')
    if publisher and (not book.publisher or force):
        book.publisher = publisher
        updated = True
    
    # ISBN
    isbn = enrichment.get('isbn')
    if isbn and (not book.isbn or force):
        book.isbn = str(isbn)
        updated = True
    
    # Page count — update if not set or default
    page_count = enrichment.get('suggested_page_count')
    if page_count and isinstance(page_count, int) and (not book.page_count or book.page_count == 0 or force):
        book.page_count = page_count
        updated = True
    
    # Total chapters — update if default (10) or 0 or not set
    total_chapters = enrichment.get('suggested_total_chapters')
    if total_chapters and isinstance(total_chapters, int) and (book.total_chapters <= 10 or force):
        book.total_chapters = total_chapters
        updated = True
    
    # Author canonical name
    canonical = enrichment.get('author_canonical_name')
    if canonical and canonical != book.author:
        book.author = canonical
        updated = True
    
    if updated:
        book.ai_enriched = True
        book.save()
    
    return updated


def enrich_single_book(book, force=False):
    """Enrich a single book using OpenAI. Returns (success, enrichment_data, error).
    This is the CORE enrichment function used by both individual and bulk endpoints.
    """
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f"Título: {book.title}\nAutor: {book.author}"}
            ],
            response_format={'type': 'json_object'},
            temperature=0.3,
        )
        
        enrichment = json.loads(response.choices[0].message.content)
        book_updated = _enrich_book_record(book, enrichment, force=force)
        
        return True, enrichment, None
    except Exception as e:
        print(f"AI Enrichment Error for '{book.title}': {e}")
        return False, None, str(e)


class AIEnrichmentView(APIView):
    """Enrich a single book using OpenAI."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get('title', '').strip()
        author = request.data.get('author', '').strip()
        book_id = request.data.get('book_id')
        force = request.data.get('force', False)
        
        if not title:
            return Response({'error': 'Title is required'}, status=400)
        
        # If book_id is provided, use the core function directly
        if book_id:
            from .models import UserBookExternal
            try:
                book = UserBookExternal.objects.get(id=int(book_id), user=request.user)
                success, enrichment, error = enrich_single_book(book, force=force)
                if success:
                    return Response({'enrichment': enrichment, 'updated': True})
                else:
                    return Response({'error': error}, status=500)
            except UserBookExternal.DoesNotExist:
                return Response({'error': f'Book {book_id} not found'}, status=404)
        
        # No book_id — just call OpenAI and return results without saving
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': f"Título: {title}\nAutor: {author}"}
                ],
                response_format={'type': 'json_object'},
                temperature=0.3,
            )
            enrichment = json.loads(response.choices[0].message.content)
            return Response({'enrichment': enrichment, 'updated': False})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class AIEnrichAllView(APIView):
    """Enrich ALL books using the EXACT same logic as individual enrichment."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import traceback
        try:
            from .models import UserBookExternal
            
            force = request.data.get('force', False)
            
            # Get books that need enrichment: ai_enriched is False OR NULL
            if force:
                books = list(UserBookExternal.objects.filter(user=request.user))
            else:
                # Include both False AND NULL (books added before ai_enriched field existed)
                from django.db.models import Q
                books = list(UserBookExternal.objects.filter(
                    Q(ai_enriched=False) | Q(ai_enriched__isnull=True),
                    user=request.user
                ))
            
            total = len(books)
            if total == 0:
                return Response({
                    'message': '¡Todos tus libros ya están enriquecidos! 🎉',
                    'enriched': 0,
                    'total': 0,
                })
            
            enriched_count = 0
            errors = []
            
            # Use the SAME enrich_single_book function for each book
            for book in books:
                try:
                    success, enrichment, error = enrich_single_book(book, force=force)
                    if success:
                        enriched_count += 1
                    else:
                        errors.append(f"{book.title}: {error}")
                except Exception as book_err:
                    errors.append(f"{book.title}: {str(book_err)}")
            
            return Response({
                'message': f'Se enriquecieron {enriched_count} de {total} libros.',
                'enriched': enriched_count,
                'total': total,
                'errors': errors[:5],
            })
        except Exception as e:
            print(f"AIEnrichAllView ERROR: {traceback.format_exc()}")
            return Response({
                'error': f'Error interno: {str(e)}',
                'detail': traceback.format_exc()[-500:],
            }, status=500)


class AIReviewView(APIView):
    """Generate an AI-powered book review."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get('title', '').strip()
        author = request.data.get('author', '').strip()
        
        if not title:
            return Response({'error': 'Title is required'}, status=400)
        
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': (
                        "Eres un crítico literario experto. Escribe una reseña del libro en español. "
                        "La reseña debe ser equilibrada, de 4-6 oraciones, sin spoilers. "
                        "Menciona: género, estilo narrativo, puntos fuertes, a quién le gustaría. "
                        "Devuelve JSON con: {\"review\": \"...\", \"rating\": X.X} "
                        "donde rating es de 1.0 a 5.0."
                    )},
                    {'role': 'user', 'content': f"Título: {title}\nAutor: {author}"}
                ],
                response_format={'type': 'json_object'},
                temperature=0.5,
            )
            
            result = json.loads(response.choices[0].message.content)
            return Response(result)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

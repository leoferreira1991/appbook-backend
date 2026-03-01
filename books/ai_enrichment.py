from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI
import json

class AIEnrichmentView(APIView):
    """Enrich book data using OpenAI: genre, synopsis, trivia, author bio."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get('title', '').strip()
        author = request.data.get('author', '').strip()
        
        if not title:
            return Response({'error': 'Title is required'}, status=400)
        
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            system_msg = (
                "Eres un experto bibliotecario y crítico literario. Dado un título y autor de un libro, "
                "devuelve información enriquecida en JSON con estos campos:\n"
                "- genre: género principal del libro en español (ej: Fantasía, Romance, Ciencia Ficción, Terror, Thriller, No Ficción, Historia, Biografía, Autoayuda, Poesía, Aventura, Misterio, Drama, etc)\n"
                "- subgenres: lista de hasta 3 subgéneros en español\n"
                "- synopsis: sinopsis breve del libro en español (2-3 oraciones, sin spoilers)\n"
                "- trivia: un dato curioso sobre el libro o su autor en español\n"
                "- author_bio: biografía breve del autor en español (2-3 oraciones)\n"
                "- author_canonical_name: nombre canónico/correcto del autor "
                "(ej: si el input dice 'Julio Verne', devolver 'Jules Verne')\n"
                "- suggested_page_count: número estimado de páginas si lo conoces, o null\n"
                "- suggested_total_chapters: número estimado de capítulos si lo conoces, o null\n"
                "- year_published: año de primera publicación si lo conoces, o null\n"
                "- themes: lista de hasta 5 temas/palabras clave del libro en español\n"
                "- ai_review: una reseña breve y equilibrada del libro (3-4 oraciones, en español, "
                "mencionando puntos fuertes y a quién le podría gustar)\n\n"
                "Devuelve SOLO JSON válido, sin markdown ni texto extra."
            )
            
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': f"Título: {title}\nAutor: {author}"}
                ],
                response_format={'type': 'json_object'},
                temperature=0.3,
            )
            
            enrichment = json.loads(response.choices[0].message.content)
            
            # Auto-update the book in the user's library if book_id is provided
            book_id = request.data.get('book_id')
            if book_id:
                from .models import UserBookExternal
                update_data = {}
                genre = enrichment.get('genre', '')
                subgenres = enrichment.get('subgenres', [])
                if genre:
                    cats = [genre] + (subgenres if subgenres else [])
                    update_data['categories'] = ', '.join(cats)
                
                page_count = enrichment.get('suggested_page_count')
                if page_count and isinstance(page_count, int):
                    update_data['page_count'] = page_count
                
                total_chapters = enrichment.get('suggested_total_chapters')
                if total_chapters and isinstance(total_chapters, int):
                    update_data['total_chapters'] = total_chapters
                    
                if update_data:
                    UserBookExternal.objects.filter(
                        id=book_id, user=request.user
                    ).update(**update_data)
            
            return Response({
                'enrichment': enrichment,
                'updated': bool(book_id),
            })
            
        except Exception as e:
            print(f"AI Enrichment Error: {e}")
            return Response({'error': str(e)}, status=500)


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

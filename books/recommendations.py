"""
OpenAI-powered recommendations endpoint.
GET /api/books/recommendations/ — returns multiple personalized recommendation sections.
"""
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserBook, UserBookExternal, CachedRecommendation
from django.utils import timezone
import json
from openai import OpenAI
from datetime import timedelta

# JSON schema we ask the model to follow
_REC_SCHEMA = """
{
  "sections": [
    {
      "section_type": "history|author|publisher",
      "title": "...",
      "recommendations": [
        {"title":"...","author":"...","reason":"frase max 12 palabras","genre":"..."}
      ]
    }
  ]
}
"""


def _call_openai(system_msg: str, user_msg: str, temperature: float = 0.8) -> dict:
    """Call OpenAI gpt-4o-mini and return parsed JSON dict."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': system_msg},
            {'role': 'user',   'content': user_msg},
        ],
        response_format={'type': 'json_object'},
        max_tokens=2000,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)


class BookRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        force_refresh = request.query_params.get('refresh') == 'true'
        # 1. Try Cache first
        cache_obj, _ = CachedRecommendation.objects.get_or_create(user=request.user)
        
        # If cache is valid (< 1h), return it immediately
        if not force_refresh and cache_obj.data and cache_obj.updated_at > (timezone.now() - timedelta(hours=6)):
            return Response(cache_obj.data)

        # 2. Gather context
        # Gather both internal and external books for a complete exclusion list
        user_books_ext = list(UserBookExternal.objects.filter(user=request.user).values('title', 'author')[:40])
        user_books_int = list(UserBook.objects.filter(user=request.user).values('book__title', 'book__author')[:20])
        
        owned_titles = []
        for b in user_books_ext:
            owned_titles.append(f"'{b['title']}' de {b['author']}")
        for b in user_books_int:
            owned_titles.append(f"'{b['book__title']}' de {b['book__author']}")

        fav_authors = (getattr(request.user, 'favorite_authors', '') or '').strip()
        fav_publishers = (getattr(request.user, 'favorite_publishers', '') or '').strip()

        if not owned_titles and not fav_authors and not fav_publishers:
            fallback_data = {
                'sections': [{
                    'section_type': 'discovery',
                    'title': '✨ Descubrí clásicos',
                    'recommendations': [
                        {'title': 'Cien años de soledad', 'author': 'Gabriel García Márquez', 'reason': 'Un pilar de la literatura latinoamericana.', 'genre': 'Realismo mágico'},
                        {'title': '1984', 'author': 'George Orwell', 'reason': 'La distopía más influyente del siglo XX.', 'genre': 'Ficción'},
                        {'title': 'El resplandor', 'author': 'Stephen King', 'reason': 'Terror psicológico magistral.', 'genre': 'Horror'}
                    ]
                }]
            }
            return Response(fallback_data)

        system = (
            'Eres un experto bibliotecario. Responde SOLO con JSON válido según el esquema. '
            'REGLA ABSOLUTA INQUEBRANTABLE: en una sección de tipo "author", TODOS y CADA UNO de los libros '
            'DEBEN ser obras escritas por ESE autor específico. "Dos años de vacaciones" es de Jules Verne, NO de Dumas. '
            '"Los tres mosqueteros" es de Dumas, NO de Verne. VERIFICA cada libro antes de incluirlo. '
            'Si tienes la más mínima duda de la autoría, NO incluyas ese libro.'
        )
        
        context_parts = []
        if owned_titles:
            context_parts.append("LIBROS YA LEÍDOS O EN BIBLIOTECA (PROHIBIDOS): " + ", ".join(owned_titles))
        if fav_authors:
            context_parts.append(f"Autores favoritos: {fav_authors}")
        if fav_publishers:
            context_parts.append(f"Editoriales favoritas: {fav_publishers}")
            
        context_text = "\n".join(context_parts)
        
        user_msg = (
            f"Basado en el siguiente perfil:\n{context_text}\n\n"
            "Genera múltiples secciones de recomendaciones (máximo 4 secciones en total).\n"
            "1. Una sección 'history' (8 libros variados) con título '✨ Para vos'.\n"
            "2. Secciones 'author' (6 libros cada una) para hasta 2 de sus autores favoritos.\n"
            "   REGLA CRÍTICA PARA SECCIONES DE AUTOR: cada libro en la sección DEBE ser escrito por ESE autor.\n"
            "   Si la sección es 'Lo mejor de Dumas', SOLO libros de Alexandre Dumas. NUNCA mezclar autores.\n"
            "3. Una sección 'publisher' (6 libros) para su editorial favorita.\n"
        )
        
        if force_refresh:
            user_msg += "NOTICIA: El usuario solicitó refrescar. MUÉSTRALE GÉNEROS Y ESTILOS COMPLETAMENTE DISTINTOS a lo que le has sugerido antes. Ofrécele variedad extrema y autores menos conocidos.\n"

        user_msg += (
            "CRITICAL SYSTEM DIRECTIVE: YOU MUST STRICTLY EXCLUDE ANY BOOK LISTED IN 'LIBROS YA LEÍDOS O EN BIBLIOTECA (PROHIBIDOS)'. DO NOT SUGGEST THEM UNDER ANY CIRCUMSTANCES.\n"
            "CRITICAL: en secciones de tipo 'author', el campo 'author' de TODOS los libros DEBE coincidir exactamente con el autor de la sección.\n"
            "Evita repetir libros. Responde estrictamente con este JSON: " + _REC_SCHEMA
        )

        try:
            temp = 0.85 if force_refresh else 0.6
            data = _call_openai(system, user_msg, temperature=temp)
            # Post-generation validation: remove misattributed books from author sections
            if data.get('sections'):
                for section in data['sections']:
                    if section.get('section_type') == 'author' and section.get('title'):
                        section_title = section['title'].lower()
                        # Extract the author name from section title (e.g. "Lo mejor de Alexandre Dumas")
                        valid_recs = []
                        for rec in section.get('recommendations', []):
                            rec_author = (rec.get('author') or '').lower()
                            # Check if book author matches the section author
                            if rec_author and rec_author in section_title:
                                valid_recs.append(rec)
                            elif any(word in section_title for word in rec_author.split() if len(word) > 3):
                                valid_recs.append(rec)
                            # else: discard the misattributed book
                        section['recommendations'] = valid_recs
            # Post-filter: remove books already in user's library (fuzzy match)
            if data.get('sections') and owned_titles:
                owned_lower = set()
                for ot in owned_titles:
                    # Extract just the title from "'Title' de Author" format
                    try:
                        t = ot.split("'")[1].lower().strip()
                        owned_lower.add(t)
                    except IndexError:
                        pass
                for section in data['sections']:
                    filtered = []
                    for rec in section.get('recommendations', []):
                        rec_title = (rec.get('title') or '').lower().strip()
                        # Exact match or substring match (catches slight variations)
                        is_owned = any(
                            rec_title == ot or ot in rec_title or rec_title in ot
                            for ot in owned_lower
                        )
                        if not is_owned:
                            filtered.append(rec)
                    section['recommendations'] = filtered
            if data.get('sections'):
                # Enrich recommendations with cover URLs from Google Books
                import requests
                for section in data['sections']:
                    for rec in section.get('recommendations', []):
                        if not rec.get('cover_url'):
                            try:
                                q = f"intitle:{rec.get('title','')}+inauthor:{rec.get('author','')}"
                                gb_resp = requests.get(
                                    f"https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=1&fields=items(volumeInfo/imageLinks)",
                                    timeout=3
                                )
                                if gb_resp.status_code == 200:
                                    items = gb_resp.json().get('items', [])
                                    if items:
                                        links = items[0].get('volumeInfo', {}).get('imageLinks', {})
                                        rec['cover_url'] = links.get('thumbnail', links.get('smallThumbnail', ''))
                            except Exception:
                                rec['cover_url'] = ''
                cache_obj.data = data
                cache_obj.updated_at = timezone.now()
                cache_obj.save()
                return Response(data)
        except Exception as e:
            print("OpenAI batched error:", e)
            
        # 4. Global Fallback
        if cache_obj.data:
            return Response(cache_obj.data)
            
        return Response({'sections': []}, status=503)

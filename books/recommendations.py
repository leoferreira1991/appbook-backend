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
        if not force_refresh and cache_obj.data and cache_obj.updated_at > (timezone.now() - timedelta(hours=1)):
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

        system = 'Eres un experto bibliotecario. Responde SOLO con JSON válido según el esquema.'
        
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
            "1. Una sección 'history' (8 libros) 'Para vos'.\n"
            "2. Secciones 'author' (6 libros cada una) para hasta 2 de sus autores favoritos.\n"
            "3. Una sección 'publisher' (6 libros) para su editorial favorita.\n"
        )
        
        if force_refresh:
            user_msg += "NOTICIA: El usuario solicitó refrescar. MUÉSTRALE GÉNEROS Y ESTILOS COMPLETAMENTE DISTINTOS a lo que le has sugerido antes. Ofrécele variedad extrema y autores menos conocidos.\n"

        user_msg += (
            "CRITICAL SYSTEM DIRECTIVE: YOU MUST STRICTLY EXCLUDE ANY BOOK LISTED IN 'LIBROS YA LEÍDOS O EN BIBLIOTECA (PROHIBIDOS)'. DO NOT SUGGEST THEM UNDER ANY CIRCUMSTANCES.\n"
            "Evita repetir libros. Responde estrictamente con este JSON: " + _REC_SCHEMA
        )

        try:
            temp = 0.95 if force_refresh else 0.8
            data = _call_openai(system, user_msg, temperature=temp)
            if data.get('sections'):
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

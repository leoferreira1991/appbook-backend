"""
POST /api/books/suggest-similar/
Given current favorites (authors or publishers), returns AI suggestions for similar ones.
Body: { "type": "author" | "publisher", "current": ["Name1", "Name2"] }
"""
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI
import json


from rest_framework import viewsets
from rest_framework.decorators import action


class SuggestSimilarView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='similar')
    def similar(self, request):
        return self._do_similar(request)

    def create(self, request):
        """Allows POST /api/books/suggest-similar/ to work like the original APIView."""
        return self._do_similar(request)

    def _do_similar(self, request):
        kind = request.data.get('type', 'author')   # 'author' or 'publisher'
        current = request.data.get('current', [])   # list of already-selected names

        if not current:
            # No selections yet — return popular defaults
            if kind == 'author':
                defaults = [
                    'Stephen King', 'Agatha Christie', 'Gabriel García Márquez',
                    'J.K. Rowling', 'George R.R. Martin', 'Isabel Allende',
                    'Haruki Murakami', 'Paulo Coelho',
                ]
            else:
                defaults = [
                    'Planeta', 'Salamandra', 'Anagrama', 'Alianza Editorial',
                    'Random House', 'Penguin Clásicos', 'Paidós', 'Tusquets',
                ]
            return Response({'suggestions': defaults})

        current_str = ', '.join(current)

        if kind == 'author':
            prompt = (
                "Al usuario le gustan estos autores: " + current_str + ".\n"
                "Sugiere exactamente 8 autores diferentes que probablemente también le gusten, "
                "considerando su estilo, género y época. Solo nombres, sin explicaciones.\n"
                'JSON: {"suggestions":["Nombre1","Nombre2",...]}'
            )
        else:
            prompt = (
                "Al usuario le gustan estas editoriales: " + current_str + ".\n"
                "Sugiere exactamente 6 editoriales en español similares en catálogo o estilo. "
                "Solo nombres, sin explicaciones.\n"
                'JSON: {"suggestions":["Editorial1","Editorial2",...]}'
            )

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': 'Eres experto en literatura. Responde SOLO con JSON válido.'},
                    {'role': 'user', 'content': prompt},
                ],
                response_format={'type': 'json_object'},
                max_tokens=300,
                temperature=0.7,
            )
            data = json.loads(response.choices[0].message.content)
            return Response({'suggestions': data.get('suggestions', [])})
        except Exception as e:
            print(f"SuggestSimilar error: {e}")
            return Response({'suggestions': []}, status=500)

    @action(detail=False, methods=['post'], url_path='search-publisher')
    def search_publisher(self, request):
        """Uses AI to find a 'canonical' or real publisher name from a partial user query."""
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'publishers': []})

        prompt = (
            f"El usuario busca la editorial: '{query}'.\n"
            "Devuelve una lista de hasta 5 nombres CANÓNICOS, REALES y completas de editoriales "
            "que coincidan, sean dueñas de la marca o sean variaciones oficiales importantes.\n"
            "Ejemplo: 'alma' -> ['Editorial Alma', 'Alma Europa', 'Alma Editorial'].\n"
            "Ejemplo: 'penguin' -> ['Penguin Random House', 'Penguin Clásicos', 'Penguin Books'].\n"
            "Ejemplo: 'planeta' -> ['Editorial Planeta', 'Grupo Planeta', 'Planeta Cómic'].\n"
            "Solo nombres reales que un usuario usaría para identificar sus libros. Sin explicaciones.\n"
            'JSON: {"publishers":["Nombre1","Nombre2","Nombre3"]}'
        )

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': 'Eres experto en el mercado editorial global. Responde SOLO con JSON válido.'},
                    {'role': 'user', 'content': prompt},
                ],
                response_format={'type': 'json_object'},
                max_tokens=200,
                temperature=0.3,
            )
            data = json.loads(response.choices[0].message.content)
            return Response({'suggestions': data.get('publishers', [])})
        except Exception as e:
            print(f"Publisher Search AI error: {e}")
            return Response({'suggestions': []}, status=500)

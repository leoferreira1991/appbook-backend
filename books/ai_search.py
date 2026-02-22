from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json
import urllib.request
import urllib.parse
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

_SEARCH_SCHEMA = """
{
  "intent": "author|publisher|book|general",
  "canonical_name": "Nombre exacto y canónico del autor/editorial/libro descubierto",
  "google_books_query": "Consulta perfecta para Google Books (ej: inauthor:\\"Diego Fischer\\" o inpublisher:\\"Planeta\\" o intitle:\\"Harry Potter\\")",
  "reason": "Explicación breve de lo que entendiste"
}
"""

def _analyze_search_intent(query: str) -> dict:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_msg = (
        "Eres un experto bibliotecario. El usuario ingresa un término de búsqueda (puede tener errores). "
        "Tu trabajo es clasificar la intención (autor, editorial, libro, o general) y construir la "
        "consulta perfecta (google_books_query) para la API de Google Books. "
        "Por ejemplo, si dice 'Diego Fisher', el canónico es 'Diego Fischer', intent es 'author', "
        "y google_books_query es 'inauthor:\"Diego Fischer\"'. "
        "Si dice 'Planeta', intent es 'publisher' y query es 'inpublisher:\"Planeta\"'. "
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

def _fetch_from_google_books(query: str, max_results: int = 15) -> list:
    """Fetch results from Google Books using a specific query string."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}&maxResults={max_results}&key={settings.GOOGLE_BOOKS_API_KEY}&langRestrict=es"
    
    results = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
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
                        
                results.append({
                    'title': vol.get('title', 'Sin título'),
                    'author': ", ".join(authors) if authors else 'Autor desconocido',
                    'description': vol.get('description', ''),
                    'cover_url': cover,
                    'source': 'google_books',
                    'google_books_id': item.get('id'),
                    'olid': None # We use google_books_id primarily now
                })
    except Exception as e:
        print(f"Google Books API Error: {e}")
        
    return results

class AISearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'metadata': None, 'results': []})
            
        # 1. Ask AI to decipher intent
        intent_data = _analyze_search_intent(query)
        if not intent_data or 'google_books_query' not in intent_data:
            return Response({'metadata': None, 'results': []})
            
        gb_query = intent_data['google_books_query']
        intent_type = intent_data.get('intent', 'general')
        canonical = intent_data.get('canonical_name', query)
        
        # 2. Fetch real data directly from Google Books
        books = _fetch_from_google_books(gb_query, max_results=15)
        
        # Build metadata header
        metadata = {
            'intent': intent_type,
            'canonical_name': canonical,
            'reason': intent_data.get('reason', '')
        }
        
        return Response({'metadata': metadata, 'results': books})


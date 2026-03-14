from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json
from openai import OpenAI

from .models import CachedAuthor, CachedAuthorWork


_AUTHOR_PROFILE_SCHEMA = """{
  "name": "Nombre canónico completo del autor",
  "bio": "Biografía de 3-4 párrafos en español",
  "birth_year": 1890,
  "death_year": 1976,
  "nationality": "Nacionalidad",
  "genres": "Género1, Género2",
  "works": [
    {
      "title": "Título en español (si existe traducción conocida, sino el original)",
      "year": 1920,
      "genre": "Género",
      "original_language": "Idioma original",
      "series_name": "Nombre de la saga (vacío si no aplica)",
      "series_order": 1
    }
  ]
}"""


def _generate_author_profile(author_name: str) -> dict:
    """Use GPT to generate a complete author profile with bibliography."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_msg = (
        "Eres un experto bibliotecario y biógrafo literario. Tu trabajo es generar un perfil completo de un autor. "
        "REGLAS IMPORTANTES:\n"
        "1. Incluye TODAS las obras publicadas del autor (novelas, cuentos publicados como libro, ensayos importantes).\n"
        "2. NO repitas títulos. Cada obra debe aparecer UNA sola vez.\n"
        "3. Si la obra tiene traducción conocida al español, usa el título en español.\n"
        "4. Agrupa las obras por saga cuando corresponda (series_name + series_order).\n"
        "5. La biografía debe ser en español, informativa y de 3-4 párrafos.\n"
        "6. Si el autor está vivo, death_year debe ser null.\n"
        "7. Devuelve estrictamente JSON válido con este schema:\n" + _AUTHOR_PROFILE_SCHEMA
    )

    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': f"Genera el perfil completo del autor: {author_name}"}
            ],
            response_format={'type': 'json_object'},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI Author Profile Error: {e}")
        return {}


def _get_author_photo_url(author_name: str) -> str:
    """Try to get an author photo from Open Library or Wikipedia."""
    import urllib.request
    import urllib.parse

    # Try Open Library author search
    try:
        encoded = urllib.parse.quote(author_name)
        url = f"https://openlibrary.org/search/authors.json?q={encoded}&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            docs = data.get('docs', [])
            if docs:
                key = docs[0].get('key', '')
                if key:
                    return f"https://covers.openlibrary.org/a/olid/{key}-L.jpg"
    except Exception:
        pass

    return ''


def _cache_author_profile(profile_data: dict) -> CachedAuthor:
    """Save the GPT-generated profile to the database cache."""
    author, created = CachedAuthor.objects.update_or_create(
        name=profile_data.get('name', ''),
        defaults={
            'bio': profile_data.get('bio', ''),
            'birth_year': profile_data.get('birth_year'),
            'death_year': profile_data.get('death_year'),
            'nationality': profile_data.get('nationality', ''),
            'genres': profile_data.get('genres', ''),
            'photo_url': profile_data.get('photo_url', ''),
        }
    )

    # Bulk-create works (delete old ones first if updating)
    if not created:
        author.works.all().delete()

    works_data = profile_data.get('works', [])
    works_to_create = []
    seen_titles = set()
    for w in works_data:
        title = w.get('title', '').strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        works_to_create.append(CachedAuthorWork(
            author=author,
            title=title,
            year=w.get('year'),
            genre=w.get('genre', ''),
            original_language=w.get('original_language', ''),
            series_name=w.get('series_name', ''),
            series_order=w.get('series_order'),
        ))

    if works_to_create:
        CachedAuthorWork.objects.bulk_create(works_to_create, ignore_conflicts=True)

    return author


def _serialize_author(author: CachedAuthor) -> dict:
    """Serialize a CachedAuthor to JSON response format."""
    works = author.works.all().order_by('year', 'title')
    return {
        'author': {
            'id': author.id,
            'name': author.name,
            'bio': author.bio,
            'birth_year': author.birth_year,
            'death_year': author.death_year,
            'nationality': author.nationality,
            'photo_url': author.photo_url,
            'genres': author.genres,
        },
        'works': [
            {
                'id': w.id,
                'title': w.title,
                'year': w.year,
                'genre': w.genre,
                'original_language': w.original_language,
                'series_name': w.series_name,
                'series_order': w.series_order,
            }
            for w in works
        ],
        'total_works': works.count(),
    }


class AIAuthorProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        name = request.query_params.get('name', '').strip()
        if not name:
            return Response({'error': 'name parameter required'}, status=400)

        # 1. Check cache first
        try:
            cached = CachedAuthor.objects.get(name__iexact=name)
            if cached.works.exists():
                return Response(_serialize_author(cached))
        except CachedAuthor.DoesNotExist:
            pass

        # 2. Generate with GPT
        profile_data = _generate_author_profile(name)
        if not profile_data or 'name' not in profile_data:
            return Response({'error': 'Could not generate author profile'}, status=404)

        # 3. Get author photo
        photo_url = _get_author_photo_url(profile_data.get('name', name))
        profile_data['photo_url'] = photo_url

        # 4. Cache and return
        author = _cache_author_profile(profile_data)
        # Update photo if we got one
        if photo_url and not author.photo_url:
            author.photo_url = photo_url
            author.save(update_fields=['photo_url'])

        return Response(_serialize_author(author))


class FollowAuthorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        author_name = request.data.get('author_name', '').strip()
        if not author_name:
            return Response({'error': 'author_name required'}, status=400)

        user = request.user
        current = user.favorite_authors or ''
        authors_list = [a.strip() for a in current.split(',') if a.strip()]

        # Check if already following (case-insensitive)
        if any(a.lower() == author_name.lower() for a in authors_list):
            return Response({
                'status': 'already_following',
                'favorite_authors': authors_list,
            })

        authors_list.append(author_name)
        user.favorite_authors = ', '.join(authors_list)
        user.save(update_fields=['favorite_authors'])

        return Response({
            'status': 'followed',
            'favorite_authors': authors_list,
        })

    def delete(self, request):
        author_name = request.data.get('author_name', '').strip()
        if not author_name:
            return Response({'error': 'author_name required'}, status=400)

        user = request.user
        current = user.favorite_authors or ''
        authors_list = [a.strip() for a in current.split(',') if a.strip()]

        # Remove case-insensitive
        authors_list = [a for a in authors_list if a.lower() != author_name.lower()]
        user.favorite_authors = ', '.join(authors_list) if authors_list else ''
        user.save(update_fields=['favorite_authors'])

        return Response({
            'status': 'unfollowed',
            'favorite_authors': authors_list,
        })

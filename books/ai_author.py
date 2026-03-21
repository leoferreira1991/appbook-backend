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
    """Use GPT to generate a complete author profile with full bibliography.
    
    Uses an iterative approach:
    1. First call gets the profile (bio, dates, etc.) + initial batch of works
    2. Subsequent calls send the already-known titles and ask for remaining works
    3. Loop continues until GPT returns < 3 new works or max 8 iterations
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_msg = (
        "Eres un experto bibliotecario y biógrafo literario. Tu trabajo es generar un perfil COMPLETO de un autor "
        "con TODA su bibliografía.\n\n"
        "REGLAS CRÍTICAS:\n"
        "1. DEBES incluir ABSOLUTAMENTE TODAS las obras publicadas del autor.\n"
        "2. NO omitas obras. Si un autor tiene 50 novelas, lista las 50. Si tiene 80, lista las 80.\n"
        "3. NO repitas títulos. Cada obra debe aparecer UNA sola vez.\n"
        "4. Si la obra tiene traducción conocida al español, usa el título en español.\n"
        "5. Agrupa las obras por saga cuando corresponda (series_name + series_order).\n"
        "6. La biografía debe ser en español, informativa y de 3-4 párrafos.\n"
        "7. Si el autor está vivo, death_year debe ser null.\n"
        "8. Incluye: novelas, novelas cortas publicadas como libro, colecciones de cuentos, "
        "y obras de teatro publicadas. NO incluyas cuentos sueltos no publicados como libro.\n\n"
        "⚠️ REGLAS ANTI-ALUCINACIÓN (MUY IMPORTANTE):\n"
        "9. VERIFICA la nacionalidad del autor. NO inventes nacionalidades. "
        "Si el autor nació en Uruguay es Uruguayo, si nació en Argentina es Argentino, etc. "
        "No confundas autores de distintos países.\n"
        "10. Si NO estás seguro de un dato biográfico (año, nacionalidad, etc.), "
        "escribe 'No verificado' en su lugar. NUNCA inventes datos.\n"
        "11. Para autores menos conocidos, sé conservador: es preferible dar menos datos "
        "correctos que muchos datos inventados.\n"
        "12. Los años de nacimiento y fallecimiento deben ser exactos. Si no los conoces, usa null.\n\n"
        "Devuelve estrictamente JSON válido con este schema:\n" + _AUTHOR_PROFILE_SCHEMA
    )

    try:
        # ── Step 1: Get profile + initial batch of works ──
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': (
                    f"Genera el perfil completo del autor: {author_name}\n\n"
                    "IMPORTANTE: Lista TODAS sus obras publicadas, no solo las más famosas. "
                    "Necesito la bibliografía COMPLETA."
                )}
            ],
            response_format={'type': 'json_object'},
            temperature=0.3,
            max_tokens=16000,
        )
        profile = json.loads(response.choices[0].message.content)
        
        works = profile.get('works', [])
        
        # Normalize titles for deduplication
        def normalize(title):
            return title.strip().lower()
        
        all_works = {}
        for w in works:
            title = w.get('title', '').strip()
            if title and normalize(title) not in all_works:
                all_works[normalize(title)] = w
        
        # ── Step 2: Iterative loop to fetch remaining works ──
        MAX_ITERATIONS = 8
        MIN_NEW_WORKS = 3  # Stop if fewer than 3 new works returned
        
        for iteration in range(MAX_ITERATIONS):
            known_titles = [w.get('title', '') for w in all_works.values()]
            
            # If we have fewer than 15, probably not a prolific author — one more try
            # If we have 15+, keep going until GPT has nothing more to add
            if iteration > 0 and len(known_titles) < 15:
                break
            
            continuation_response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': (
                        "Eres un experto bibliotecario. Tu tarea es completar la bibliografía de un autor.\n"
                        "Te voy a dar una lista de obras que YA TENGO. Necesito que me des las que FALTAN.\n"
                        "Devuelve JSON con un array 'works' que contenga SOLO las obras que NO están en mi lista.\n"
                        "Si NO falta ninguna obra, devuelve {\"works\": []}.\n"
                        "Cada obra: {\"title\": \"...\", \"year\": 1920, \"genre\": \"...\", "
                        "\"original_language\": \"...\", \"series_name\": \"...\", \"series_order\": N}\n"
                        "Usa títulos en español cuando exista traducción conocida."
                    )},
                    {'role': 'user', 'content': (
                        f"Autor: {author_name}\n\n"
                        f"Ya tengo estas {len(known_titles)} obras:\n"
                        + "\n".join(f"- {t}" for t in known_titles)
                        + "\n\n¿Cuáles obras publicadas de este autor FALTAN en mi lista? "
                        "Incluye novelas, colecciones de cuentos, novelas cortas, y obras de teatro. "
                        "Si no falta ninguna, devuelve {\"works\": []}."
                    )}
                ],
                response_format={'type': 'json_object'},
                temperature=0.3,
                max_tokens=16000,
            )
            
            extra_data = json.loads(continuation_response.choices[0].message.content)
            extra_works = extra_data.get('works', [])
            
            # Count genuinely new works
            new_count = 0
            for w in extra_works:
                title = w.get('title', '').strip()
                if title and normalize(title) not in all_works:
                    all_works[normalize(title)] = w
                    new_count += 1
            
            print(f"  [{author_name}] Iteration {iteration + 1}: +{new_count} new works (total: {len(all_works)})")
            
            # Stop if we got fewer than MIN_NEW_WORKS new unique works
            if new_count < MIN_NEW_WORKS:
                break
        
        # Replace works in profile with the accumulated complete list
        profile['works'] = list(all_works.values())
        print(f"  [{author_name}] Final bibliography: {len(profile['works'])} works")
        
        return profile
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
            genre=w.get('genre') or '',
            original_language=w.get('original_language') or '',
            series_name=w.get('series_name') or '',
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

    def _find_cached(self, name):
        """Try to find a cached author, with flexible name matching."""
        # 1. Exact case-insensitive match
        try:
            cached = CachedAuthor.objects.get(name__iexact=name)
            if cached.works.exists():
                return cached
        except CachedAuthor.DoesNotExist:
            pass

        # 2. Partial match: "Stephen King" matches "Stephen Edwin King"
        #    Split search name into parts and check if all parts are in the cached name
        name_parts = name.lower().split()
        candidates = CachedAuthor.objects.all()
        for part in name_parts:
            candidates = candidates.filter(name__icontains=part)
        
        if candidates.exists():
            # Return the best match (prefer shortest name = closest match)
            best = min(candidates, key=lambda a: len(a.name))
            if best.works.exists():
                return best

        return None

    def get(self, request):
        name = request.query_params.get('name', '').strip()
        force_refresh = request.query_params.get('refresh', '').lower() == 'true'
        if not name:
            return Response({'error': 'name parameter required'}, status=400)

        # 1. Check cache first — always serve cached data if exists (unless force refresh)
        if not force_refresh:
            cached = self._find_cached(name)
            if cached:
                return Response(_serialize_author(cached))

        # 2. Generate with GPT (only for new authors or explicit refresh)
        try:
            profile_data = _generate_author_profile(name)
        except Exception as e:
            print(f"GPT generation error for '{name}': {e}")
            profile_data = {}

        if not profile_data or 'name' not in profile_data:
            # If we had cached data but refresh failed, return the cached version
            cached = self._find_cached(name)
            if cached:
                return Response(_serialize_author(cached))
            return Response({'error': 'Could not generate author profile'}, status=404)

        # 3. Get author photo
        try:
            photo_url = _get_author_photo_url(profile_data.get('name') or name)
        except Exception:
            photo_url = ''
        profile_data['photo_url'] = photo_url

        # 4. Cache and return
        try:
            author = _cache_author_profile(profile_data)
            if photo_url and not author.photo_url:
                author.photo_url = photo_url
                author.save(update_fields=['photo_url'])
            return Response(_serialize_author(author))
        except Exception as e:
            print(f"Cache error for '{name}': {e}")
            # Return the data directly even if caching fails
            return Response({
                'author': {
                    'name': profile_data.get('name', name),
                    'bio': profile_data.get('bio', ''),
                    'birth_year': profile_data.get('birth_year'),
                    'death_year': profile_data.get('death_year'),
                    'nationality': profile_data.get('nationality', ''),
                    'photo_url': photo_url,
                    'genres': profile_data.get('genres', ''),
                },
                'works': profile_data.get('works', []),
                'total_works': len(profile_data.get('works', [])),
            })


class FollowAuthorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Check if user follows a specific author."""
        author_name = request.query_params.get('name', '').strip()
        if not author_name:
            return Response({'error': 'name parameter required'}, status=400)

        user = request.user
        current = user.favorite_authors or ''
        authors_list = [a.strip().lower() for a in current.split(',') if a.strip()]
        is_following = author_name.lower() in authors_list

        return Response({
            'is_following': is_following,
            'favorite_authors': [a.strip() for a in (user.favorite_authors or '').split(',') if a.strip()],
        })

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

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json
import requests as http_requests
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher

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


_WIKI_HEADERS = {'User-Agent': 'AppBook/1.0 (admin@appbook.com)'}


def _fetch_wikipedia_for_lang(author_name: str, lang: str, bib_suffix: str) -> list:
    """Fetch bibliography text from Wikipedia for a single language. Returns list of text fragments."""
    texts = []
    bib_keywords = ['novels', 'bibliography', 'works', 'short fiction', 'stage works',
                    'plays', 'collections', 'poetry', 'miscellany', 'publications',
                    'bibliografía', 'obras', 'novelas', 'publicaciones', 'cuentos', 'teatro']
    skip_keywords = ['notes', 'references', 'sources', 'see also', 'external', 'notas',
                     'referencias', 'véase', 'enlaces']
    api_url = f'https://{lang}.wikipedia.org/w/api.php'

    try:
        # Try 1: Dedicated bibliography page
        bib_page = f'{author_name}{bib_suffix}'
        r = http_requests.get(api_url, params={
            'action': 'parse', 'page': bib_page,
            'prop': 'sections', 'format': 'json'
        }, headers=_WIKI_HEADERS, timeout=8)
        parse_data = r.json().get('parse', {})

        if parse_data:
            sections = parse_data.get('sections', [])
            for section in sections:
                section_name = section.get('line', '').lower()
                if any(kw in section_name for kw in skip_keywords):
                    continue
                if any(kw in section_name for kw in bib_keywords) or section.get('level') == '2':
                    r2 = http_requests.get(api_url, params={
                        'action': 'parse', 'page': bib_page,
                        'section': section['index'],
                        'prop': 'wikitext', 'format': 'json'
                    }, headers=_WIKI_HEADERS, timeout=8)
                    wikitext = r2.json().get('parse', {}).get('wikitext', {}).get('*', '')
                    if wikitext and len(wikitext) > 50:
                        texts.append(f'[{lang.upper()} - {bib_page} - {section["line"]}]\n{wikitext}')

        # Try 2: Author's main page — bibliography/obras section
        r3 = http_requests.get(api_url, params={
            'action': 'query', 'list': 'search',
            'srsearch': author_name, 'format': 'json', 'srlimit': 1
        }, headers=_WIKI_HEADERS, timeout=8)
        results = r3.json().get('query', {}).get('search', [])
        if results:
            main_page = results[0]['title']
            r4 = http_requests.get(api_url, params={
                'action': 'parse', 'page': main_page,
                'prop': 'sections', 'format': 'json'
            }, headers=_WIKI_HEADERS, timeout=8)
            sections = r4.json().get('parse', {}).get('sections', [])

            for section in sections:
                section_name = section.get('line', '').lower()
                if any(kw in section_name for kw in bib_keywords):
                    r5 = http_requests.get(api_url, params={
                        'action': 'parse', 'page': main_page,
                        'section': section['index'],
                        'prop': 'wikitext', 'format': 'json'
                    }, headers=_WIKI_HEADERS, timeout=8)
                    wikitext = r5.json().get('parse', {}).get('wikitext', {}).get('*', '')
                    if wikitext and len(wikitext) > 100:
                        texts.append(f'[{lang.upper()} - {main_page} - {section["line"]}]\n{wikitext}')
    except Exception as e:
        print(f"  [Wikipedia] Error fetching {lang}: {e}")

    return texts


def _fetch_wikipedia_bibliography(author_name: str) -> str:
    """Fetch bibliography text from Wikipedia (ES + EN) IN PARALLEL.

    Both language fetches run concurrently, cutting total wait time roughly in half.
    """
    all_texts = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_fetch_wikipedia_for_lang, author_name, 'en', ' bibliography'): 'en',
            executor.submit(_fetch_wikipedia_for_lang, author_name, 'es', ''): 'es',
        }
        for future in as_completed(futures):
            try:
                all_texts.extend(future.result())
            except Exception as e:
                print(f"  [Wikipedia] Thread error for {futures[future]}: {e}")

    combined = '\n\n'.join(all_texts)
    if len(combined) > 30000:
        combined = combined[:30000] + '\n... (truncated)'
    return combined


def _generate_author_profile(author_name: str) -> dict:
    """Use Wikipedia + GPT to generate a complete author profile with full bibliography.
    
    Pipeline:
    1. Fetch bibliography text from Wikipedia (ES + EN)
    2. Send Wikipedia text to GPT to extract structured works data
    3. GPT also generates bio, dates, nationality from its own knowledge
    4. Iterative loop asks GPT for any remaining works
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # ── Step 0: Fetch Wikipedia bibliography ──
    wiki_text = _fetch_wikipedia_bibliography(author_name)
    wiki_works = []
    
    if wiki_text:
        print(f"  [{author_name}] Wikipedia bibliography: {len(wiki_text)} chars")
        
        # ── Step 0.5: Dedicated GPT call to extract works from Wikipedia ──
        try:
            wiki_extract_response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': (
                        "Eres un parser de datos. Tu ÚNICA tarea es extraer la lista de LIBROS "
                        "del texto de Wikipedia que te doy.\n\n"
                        "REGLAS:\n"
                        "1. Extrae TODOS los títulos de LIBROS: novelas, novelas cortas y colecciones de cuentos.\n"
                        "2. Traduce los títulos al español cuando exista traducción conocida.\n"
                        "3. NO inventes obras. Solo extrae las que aparecen en el texto.\n"
                        "4. Incluye el año de publicación si aparece.\n"
                        "5. Incluye el género si se puede detectar del contexto.\n"
                        "6. Si la obra pertenece a una serie/saga, indica el nombre de la serie.\n"
                        "7. NO incluyas películas, series de TV, obras de teatro, poesía, ensayos, ni adaptaciones.\n"
                        "8. NO repitas títulos.\n"
                        "9. SOLO incluye LIBROS publicados como tal (novelas, novelas cortas, colecciones de cuentos).\n\n"
                        "Devuelve JSON: {\"works\": [{\"title\": \"...\", \"year\": 1920, \"genre\": \"...\", "
                        "\"original_language\": \"...\", \"series_name\": \"...\", \"series_order\": N}]}"
                    )},
                    {'role': 'user', 'content': (
                        f"Extrae TODAS las obras literarias del autor {author_name} "
                        f"de este texto de Wikipedia:\n\n{wiki_text}"
                    )}
                ],
                response_format={'type': 'json_object'},
                temperature=0.1,
                max_tokens=16000,
            )
            wiki_data = json.loads(wiki_extract_response.choices[0].message.content)
            wiki_works = wiki_data.get('works', [])
            print(f"  [{author_name}] Wikipedia extraction: {len(wiki_works)} works found")
        except Exception as e:
            print(f"  [{author_name}] Wikipedia extraction error: {e}")
    else:
        print(f"  [{author_name}] No Wikipedia bibliography found, using GPT only")

    system_msg = (
        "Eres un experto bibliotecario y biógrafo literario. Tu trabajo es generar un perfil COMPLETO de un autor "
        "con TODA su bibliografía.\n\n"
        "REGLAS CRÍTICAS:\n"
        "1. DEBES incluir ABSOLUTAMENTE TODOS los LIBROS publicados del autor.\n"
        "2. NO omitas libros. Si un autor tiene 50 novelas, lista las 50. Si tiene 80, lista las 80.\n"
        "3. NO repitas títulos. Cada libro debe aparecer UNA sola vez.\n"
        "4. Si la obra tiene traducción conocida al español, usa el título en español.\n"
        "5. Agrupa las obras por saga cuando corresponda (series_name + series_order).\n"
        "6. La biografía debe ser en español, informativa y de 3-4 párrafos.\n"
        "7. Si el autor está vivo, death_year debe ser null.\n"
        "8. SOLO incluye LIBROS: novelas, novelas cortas publicadas como libro, colecciones de cuentos. "
        "NO incluyas obras de teatro, poesía, ensayos, cuentos sueltos no publicados como libro, "
        "ni guiones de cine o TV.\n\n"
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
        # ── Step 1: Get profile + initial batch of works (WITHOUT Wikipedia context) ──
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
        # First, add Wikipedia-extracted works (higher quality source)
        for w in wiki_works:
            title = w.get('title', '').strip()
            if title and normalize(title) not in all_works:
                all_works[normalize(title)] = w
        
        wiki_count = len(all_works)
        # Then add GPT profile works (fills gaps)
        for w in works:
            title = w.get('title', '').strip()
            if title and normalize(title) not in all_works:
                all_works[normalize(title)] = w
        
        print(f"  [{author_name}] Merged: {wiki_count} from Wikipedia + {len(all_works) - wiki_count} new from GPT = {len(all_works)} total")

        # ── Step 2: Iterative loop to fetch remaining works ──
        # Reduced from 4 to 2 max iterations — extra rounds rarely add real works
        # and significantly increase latency (each round = 1.5-3s GPT call)
        MAX_ITERATIONS = 2
        MIN_NEW_WORKS = 2  # Stop if fewer than 2 new works (likely hallucinating)

        # Skip iterations entirely if we already have a rich bibliography from Wikipedia
        if len(all_works) >= 30:
            MAX_ITERATIONS = 0
            print(f"  [{author_name}] Skipping iterations — already have {len(all_works)} works from Wikipedia+GPT")
        elif len(all_works) >= 15:
            MAX_ITERATIONS = 1
            print(f"  [{author_name}] Reducing to 1 iteration — already have {len(all_works)} works")

        for iteration in range(MAX_ITERATIONS):
            known_titles = [w.get('title', '') for w in all_works.values()]
            
            continuation_response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': (
                        "Eres un experto bibliotecario. Tu tarea es completar la lista de LIBROS de un autor.\n"
                        "Te voy a dar una lista de libros que YA TENGO. Necesito que me des los que FALTAN.\n"
                        "IMPORTANTE: Sé exhaustivo. Si el autor tiene 60+ libros y solo veo 20, HAY MUCHOS FALTANTES.\n"
                        "SOLO incluye LIBROS: novelas, novelas cortas, colecciones de cuentos. "
                        "NO incluyas obras de teatro, poesía, ensayos ni guiones.\n"
                        "Devuelve JSON con un array 'works' que contenga SOLO los libros que NO están en mi lista.\n"
                        "Si NO falta ningún libro, devuelve {\"works\": []}.\n"
                        "Cada obra: {\"title\": \"...\", \"year\": 1920, \"genre\": \"...\", "
                        "\"original_language\": \"...\", \"series_name\": \"...\", \"series_order\": N}\n"
                        "Usa títulos en español cuando exista traducción conocida."
                    )},
                    {'role': 'user', 'content': (
                        f"Autor: {author_name}\n\n"
                        f"Ya tengo estos {len(known_titles)} libros:\n"
                        + "\n".join(f"- {t}" for t in known_titles)
                        + "\n\n¿Cuáles LIBROS publicados de este autor FALTAN en mi lista? "
                        "Incluye solo novelas, colecciones de cuentos y novelas cortas. "
                        "NO incluyas obras de teatro, poesía ni ensayos. "
                        "Si no falta ninguno, devuelve {\"works\": []}."
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
            
            # Stop if we got zero genuinely new works
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
        """Try to find a cached author, with safe name matching.

        Uses SequenceMatcher similarity instead of icontains to prevent
        false positives (e.g., searching "King" matching "Stephen King").
        """
        # 1. Exact case-insensitive match (fastest path)
        try:
            cached = CachedAuthor.objects.get(name__iexact=name)
            if cached.works.exists():
                return cached
        except CachedAuthor.DoesNotExist:
            pass

        # 2. Fuzzy match using string similarity (safer than icontains)
        #    Only consider candidates where ALL name parts appear
        name_lower = name.lower().strip()
        name_parts = name_lower.split()

        # Skip fuzzy matching for single short words (too ambiguous)
        if len(name_parts) == 1 and len(name_lower) < 6:
            return None

        candidates = CachedAuthor.objects.all()
        for part in name_parts:
            if len(part) >= 3:  # Only filter on parts with 3+ chars
                candidates = candidates.filter(name__icontains=part)

        if candidates.exists():
            # Score candidates by similarity ratio
            best = None
            best_score = 0.0
            for candidate in candidates[:20]:  # Limit to prevent scanning entire table
                score = SequenceMatcher(None, name_lower, candidate.name.lower()).ratio()
                if score > best_score and candidate.works.exists():
                    best_score = score
                    best = candidate

            # Only return if similarity is high enough (>= 0.7)
            if best and best_score >= 0.7:
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

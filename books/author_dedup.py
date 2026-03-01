from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserBookExternal
import json


def _simple_dedup(authors):
    """Fallback: detect duplicates by normalizing names (no AI needed)."""
    from difflib import SequenceMatcher
    
    groups = []
    used = set()
    
    for i, a in enumerate(authors):
        if a in used:
            continue
        variants = [a]
        for j, b in enumerate(authors):
            if i == j or b in used:
                continue
            # Normalize: lowercase, remove accents
            a_norm = a.lower().strip()
            b_norm = b.lower().strip()
            
            # Check similarity
            ratio = SequenceMatcher(None, a_norm, b_norm).ratio()
            if ratio > 0.7:
                variants.append(b)
        
        if len(variants) > 1:
            # Pick longest name as canonical
            canonical = max(variants, key=len)
            used.update(variants)
            groups.append({'canonical': canonical, 'variants': variants})
    
    return groups


def _ai_dedup(authors):
    """Use OpenAI to detect duplicate authors."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': (
                    "Eres un experto bibliotecario. Te doy una lista de nombres de autores. "
                    "Identifica grupos que son la misma persona con nombres diferentes "
                    "(variaciones de idioma, errores, abreviaciones). "
                    "Para cada grupo, devuelve el nombre canónico más reconocido internacionalmente. "
                    "IMPORTANTE: incluye todas las variantes del nombre en la lista 'variants', "
                    "incluyendo el nombre canónico. "
                    "Devuelve JSON: {\"groups\": [{\"canonical\": \"Nombre\", \"variants\": [\"var1\", \"var2\"]}]}"
                    "Si no hay duplicados: {\"groups\": []}"
                )},
                {'role': 'user', 'content': f"Autores: {json.dumps(authors)}"}
            ],
            response_format={'type': 'json_object'},
            temperature=0.2,
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('groups', [])
    except Exception as e:
        print(f"AI dedup error: {e}")
        return None


class AuthorDedupView(APIView):
    """Detect and merge duplicate authors."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Scan the user's library for potential duplicate authors."""
        user = request.user
        authors = list(
            UserBookExternal.objects.filter(user=user)
            .values_list('author', flat=True)
            .distinct()
        )
        
        if len(authors) < 2:
            return Response({'duplicates': [], 'message': 'No hay suficientes autores para analizar.'})
        
        # Try AI first, fallback to simple comparison
        groups = _ai_dedup(authors)
        if groups is None:
            groups = _simple_dedup(authors)
        
        return Response({
            'total_authors': len(authors),
            'duplicates': groups,
            'message': f'Se encontraron {len(groups)} grupo(s) de posibles duplicados.' if groups else 'No se encontraron duplicados.'
        })

    def post(self, request):
        """Merge author variants into a canonical name."""
        canonical = request.data.get('canonical', '').strip()
        variants = request.data.get('variants', [])
        
        if not canonical or not variants:
            return Response({'error': 'canonical and variants are required'}, status=400)
        
        user = request.user
        updated = 0
        
        for variant in variants:
            if variant != canonical:
                count = UserBookExternal.objects.filter(
                    user=user, author=variant
                ).update(author=canonical)
                updated += count
        
        return Response({
            'canonical': canonical,
            'merged_variants': variants,
            'books_updated': updated,
            'message': f'Se unificaron {updated} libro(s) bajo el autor "{canonical}".'
        })


class AutoMergeAuthorsView(APIView):
    """Auto-detect and merge all duplicates in one step."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        authors = list(
            UserBookExternal.objects.filter(user=user)
            .values_list('author', flat=True)
            .distinct()
        )
        
        if len(authors) < 2:
            return Response({'merged': 0, 'message': 'No hay suficientes autores para analizar.', 'merges': []})
        
        # Try AI first, fallback to simple dedup
        groups = _ai_dedup(authors)
        if groups is None:
            groups = _simple_dedup(authors)
        
        total_updated = 0
        merge_results = []
        
        for group in groups:
            canonical = group.get('canonical', '')
            variants = group.get('variants', [])
            
            group_updated = 0
            for variant in variants:
                if variant != canonical:
                    count = UserBookExternal.objects.filter(
                        user=user, author=variant
                    ).update(author=canonical)
                    group_updated += count
                    total_updated += count
            
            merge_results.append({
                'canonical': canonical,
                'variants': variants,
                'books_updated': group_updated,
            })
        
        return Response({
            'total_groups': len(groups),
            'total_books_updated': total_updated,
            'merges': merge_results,
            'message': f'Se fusionaron {total_updated} libro(s) de {len(groups)} grupo(s) de autores duplicados.' if total_updated > 0 else 'No se encontraron autores duplicados.'
        })

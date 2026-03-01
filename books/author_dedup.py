from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI
from .models import UserBookExternal
import json


class AuthorDedupView(APIView):
    """Detect and merge duplicate authors using AI."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Scan the user's library for potential duplicate authors.
        Returns groups of authors that might be the same person.
        """
        user = request.user
        
        # Get all unique author names from the user's library
        authors = list(
            UserBookExternal.objects.filter(user=user)
            .values_list('author', flat=True)
            .distinct()
        )
        
        if len(authors) < 2:
            return Response({'duplicates': [], 'message': 'No hay suficientes autores para analizar.'})
        
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': (
                        "Eres un experto bibliotecario. Te doy una lista de nombres de autores de la biblioteca de un usuario. "
                        "Identifica grupos de autores que son la misma persona pero con nombres diferentes "
                        "(ej: variaciones de idioma como 'Jules Verne' y 'Julio Verne', abreviaciones, errores tipográficos, etc). "
                        "Para cada grupo, determina el nombre canónico correcto. "
                        "Devuelve estrictamente JSON: {\"groups\": [{\"canonical\": \"Nombre Correcto\", \"variants\": [\"variante1\", \"variante2\"]}]}"
                        "Si no hay duplicados, devolver {\"groups\": []}"
                    )},
                    {'role': 'user', 'content': f"Autores: {json.dumps(authors)}"}
                ],
                response_format={'type': 'json_object'},
                temperature=0.2,
            )
            
            result = json.loads(response.choices[0].message.content)
            groups = result.get('groups', [])
            
            return Response({
                'total_authors': len(authors),
                'duplicates': groups,
                'message': f'Se encontraron {len(groups)} grupo(s) de posibles duplicados.' if groups else 'No se encontraron duplicados.'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def post(self, request):
        """
        Merge author variants into a canonical name.
        Body: {"canonical": "Jules Verne", "variants": ["Julio Verne", "J. Verne"]}
        """
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
        """Detect duplicates and merge them automatically."""
        user = request.user
        
        authors = list(
            UserBookExternal.objects.filter(user=user)
            .values_list('author', flat=True)
            .distinct()
        )
        
        if len(authors) < 2:
            return Response({'merged': 0, 'message': 'No hay suficientes autores para analizar.'})
        
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': (
                        "Eres un experto bibliotecario. Te doy una lista de nombres de autores. "
                        "Identifica grupos que son la misma persona con nombres diferentes "
                        "(variaciones de idioma, errores, abreviaciones). "
                        "Para cada grupo, return el nombre canónico más reconocido internacionalmente. "
                        "Devuelve JSON: {\"groups\": [{\"canonical\": \"Nombre\", \"variants\": [\"var1\", \"var2\"]}]}"
                        "Si no hay duplicados: {\"groups\": []}"
                    )},
                    {'role': 'user', 'content': f"Autores: {json.dumps(authors)}"}
                ],
                response_format={'type': 'json_object'},
                temperature=0.2,
            )
            
            result = json.loads(response.choices[0].message.content)
            groups = result.get('groups', [])
            
            total_updated = 0
            merge_results = []
            
            for group in groups:
                canonical = group.get('canonical', '')
                variants = group.get('variants', [])
                
                for variant in variants:
                    if variant != canonical:
                        count = UserBookExternal.objects.filter(
                            user=user, author=variant
                        ).update(author=canonical)
                        total_updated += count
                
                merge_results.append({
                    'canonical': canonical,
                    'variants': variants,
                })
            
            return Response({
                'total_groups': len(groups),
                'total_books_updated': total_updated,
                'merges': merge_results,
                'message': f'Se fusionaron {total_updated} libro(s) de {len(groups)} grupo(s) de autores duplicados.' if total_updated > 0 else 'No se encontraron autores duplicados.'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

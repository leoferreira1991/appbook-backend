"""
Admin Author Management API.
All endpoints use key-based authentication (no JWT required).
"""
import json
import threading
from django import db as django_db
from django.conf import settings
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import cloudinary.uploader

from .models import CachedAuthor, CachedAuthorWork
from .ai_author import _generate_author_profile, _get_author_photo_url, _cache_author_profile

ADMIN_KEY = 'appbook-admin-2026'


def _check_key(request):
    """Validate admin key from query params or request body."""
    key = request.query_params.get('key', '') or request.data.get('key', '')
    return key == ADMIN_KEY


class AdminAuthorsListView(APIView):
    """List all CachedAuthors with search/pagination, or create a new one."""
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        # Search filter
        search = request.query_params.get('search', '').strip()
        authors = CachedAuthor.objects.annotate(works_count=Count('works'))

        if search:
            authors = authors.filter(
                Q(name__icontains=search) | Q(nationality__icontains=search)
            )

        # Pagination
        page = int(request.query_params.get('page', 0))
        page_size = int(request.query_params.get('page_size', 50))
        total = authors.count()
        authors = authors.order_by('name')[page * page_size:(page + 1) * page_size]

        data = [{
            'id': a.id,
            'name': a.name,
            'bio': a.bio[:200] + '...' if len(a.bio) > 200 else a.bio,
            'birth_year': a.birth_year,
            'death_year': a.death_year,
            'nationality': a.nationality,
            'photo_url': a.photo_url,
            'genres': a.genres,
            'works_count': a.works_count,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'updated_at': a.updated_at.isoformat() if a.updated_at else None,
        } for a in authors]

        return Response({
            'authors': data,
            'total': total,
            'page': page,
            'page_size': page_size,
        })

    def post(self, request):
        """Create a new author manually."""
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'name is required'}, status=400)

        # Check if already exists
        if CachedAuthor.objects.filter(name__iexact=name).exists():
            return Response({'error': f'Author "{name}" already exists'}, status=409)

        author = CachedAuthor.objects.create(
            name=name,
            bio=request.data.get('bio', ''),
            birth_year=request.data.get('birth_year'),
            death_year=request.data.get('death_year'),
            nationality=request.data.get('nationality', ''),
            genres=request.data.get('genres', ''),
        )

        return Response({
            'id': author.id,
            'name': author.name,
            'message': f'Author "{name}" created successfully.',
        }, status=201)


class AdminAuthorDetailView(APIView):
    """Get, update, or delete a single CachedAuthor."""
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, pk):
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        try:
            author = CachedAuthor.objects.get(pk=pk)
        except CachedAuthor.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)

        works = author.works.all().order_by('year', 'title')
        return Response({
            'id': author.id,
            'name': author.name,
            'bio': author.bio,
            'birth_year': author.birth_year,
            'death_year': author.death_year,
            'nationality': author.nationality,
            'photo_url': author.photo_url,
            'genres': author.genres,
            'created_at': author.created_at.isoformat() if author.created_at else None,
            'updated_at': author.updated_at.isoformat() if author.updated_at else None,
            'works': [{
                'id': w.id,
                'title': w.title,
                'year': w.year,
                'genre': w.genre,
                'original_language': w.original_language,
                'series_name': w.series_name,
                'series_order': w.series_order,
            } for w in works],
            'works_count': works.count(),
        })

    def put(self, request, pk):
        """Update author fields."""
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        try:
            author = CachedAuthor.objects.get(pk=pk)
        except CachedAuthor.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)

        # Update only provided fields
        updatable = ['name', 'bio', 'nationality', 'genres', 'photo_url']
        updated_fields = []
        for field in updatable:
            if field in request.data:
                setattr(author, field, request.data[field])
                updated_fields.append(field)

        # Handle integer fields separately
        for int_field in ['birth_year', 'death_year']:
            if int_field in request.data:
                val = request.data[int_field]
                setattr(author, int_field, int(val) if val not in [None, '', 'null'] else None)
                updated_fields.append(int_field)

        if updated_fields:
            author.save()

        return Response({
            'id': author.id,
            'name': author.name,
            'updated_fields': updated_fields,
            'message': 'Author updated successfully.',
        })

    def delete(self, request, pk):
        """Delete author and all associated works."""
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        try:
            author = CachedAuthor.objects.get(pk=pk)
        except CachedAuthor.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)

        name = author.name
        author.delete()  # CASCADE deletes works too
        return Response({'message': f'Author "{name}" deleted successfully.'})


class AdminAuthorEnrichView(APIView):
    """Trigger AI enrichment for a single author.
    
    POST params:
      - works_only (bool, default=true): Only update works, keep profile fields intact
      - wait (bool, default=false): Wait for completion instead of background thread
    """
    permission_classes = []

    def post(self, request, pk):
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        try:
            author = CachedAuthor.objects.get(pk=pk)
        except CachedAuthor.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)

        author_name = author.name
        author_id = author.id
        works_only = str(request.data.get('works_only', request.query_params.get('works_only', 'true'))).lower() in ('true', '1', 'yes')

        def _enrich_bg():
            # Close stale DB connections from previous requests
            django_db.close_old_connections()
            try:
                print(f"🔄 Admin enrich started: {author_name} (pk={author_id}, works_only={works_only})")
                profile_data = _generate_author_profile(author_name)
                if not profile_data or 'name' not in profile_data:
                    print(f"❌ Admin enrich failed (empty GPT): {author_name}")
                    return

                # CRITICAL: Force the profile name to match the DB record
                # GPT may return a different canonical name (e.g. "Diego Fischer Castañeda")
                # which would cause _cache_author_profile to create a duplicate
                profile_data['name'] = author_name

                if works_only:
                    # Only update works — DO NOT touch profile fields
                    author_obj = CachedAuthor.objects.get(pk=author_id)
                    author_obj.works.all().delete()

                    works_data = profile_data.get('works', [])
                    works_to_create = []
                    seen_titles = set()
                    for w in works_data:
                        title = w.get('title', '').strip()
                        if not title or title.lower() in seen_titles:
                            continue
                        seen_titles.add(title.lower())
                        works_to_create.append(CachedAuthorWork(
                            author=author_obj,
                            title=title,
                            year=w.get('year'),
                            genre=w.get('genre') or '',
                            original_language=w.get('original_language') or '',
                            series_name=w.get('series_name') or '',
                            series_order=w.get('series_order'),
                        ))
                    if works_to_create:
                        CachedAuthorWork.objects.bulk_create(works_to_create, ignore_conflicts=True)
                    
                    # Only update photo if author doesn't have one
                    if not author_obj.photo_url:
                        try:
                            photo_url = _get_author_photo_url(author_name)
                            if photo_url:
                                author_obj.photo_url = photo_url
                                author_obj.save(update_fields=['photo_url'])
                        except Exception:
                            pass
                    
                    print(f"✅ Admin enrich (works_only): {author_name} — {len(works_to_create)} works")
                else:
                    # Full enrichment — overwrites everything
                    photo_url = _get_author_photo_url(profile_data.get('name', author_name))
                    profile_data['photo_url'] = photo_url
                    _cache_author_profile(profile_data)
                    print(f"✅ Admin enrich (full): {author_name}")

            except Exception as e:
                import traceback
                print(f"❌ Admin enrich error for {author_name}: {e}")
                traceback.print_exc()
            finally:
                django_db.close_old_connections()

        thread = threading.Thread(target=_enrich_bg, daemon=True)
        thread.start()

        return Response({
            'message': f'AI enrichment started for "{author_name}". Mode: {"works_only" if works_only else "full"}. This runs in background.',
            'author_id': pk,
            'works_only': works_only,
        })


class AdminAuthorPhotoView(APIView):
    """Upload or change author photo via Cloudinary."""
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        try:
            author = CachedAuthor.objects.get(pk=pk)
        except CachedAuthor.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)

        photo = request.FILES.get('photo')
        if not photo:
            return Response({'error': 'No photo file provided'}, status=400)

        try:
            result = cloudinary.uploader.upload(
                photo,
                folder='appbook/author_photos',
                resource_type='image',
                public_id=f'author_{author.id}',
                overwrite=True,
            )
            photo_url = result.get('secure_url', '')
            author.photo_url = photo_url
            author.save(update_fields=['photo_url'])

            return Response({
                'message': 'Photo uploaded successfully.',
                'photo_url': photo_url,
            })
        except Exception as e:
            return Response({'error': f'Upload failed: {str(e)}'}, status=500)


class AdminAuthorWorkView(APIView):
    """Manage individual works for an author."""
    permission_classes = []
    parser_classes = [JSONParser]

    def post(self, request, pk):
        """Add a new work to an author."""
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        try:
            author = CachedAuthor.objects.get(pk=pk)
        except CachedAuthor.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)

        title = request.data.get('title', '').strip()
        if not title:
            return Response({'error': 'title is required'}, status=400)

        work = CachedAuthorWork.objects.create(
            author=author,
            title=title,
            year=request.data.get('year'),
            genre=request.data.get('genre', ''),
            original_language=request.data.get('original_language', ''),
            series_name=request.data.get('series_name', ''),
            series_order=request.data.get('series_order'),
        )

        return Response({
            'id': work.id,
            'title': work.title,
            'message': f'Work "{title}" added to {author.name}.',
        }, status=201)

    def delete(self, request, pk):
        """Delete a specific work by work_id."""
        if not _check_key(request):
            return Response({'error': 'Invalid key'}, status=403)

        work_id = request.query_params.get('work_id') or request.data.get('work_id')
        if not work_id:
            return Response({'error': 'work_id is required'}, status=400)

        try:
            work = CachedAuthorWork.objects.get(pk=work_id, author_id=pk)
        except CachedAuthorWork.DoesNotExist:
            return Response({'error': 'Work not found'}, status=404)

        title = work.title
        work.delete()
        return Response({'message': f'Work "{title}" deleted.'})

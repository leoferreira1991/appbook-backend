"""
Admin panel view — serves the web-based author management UI.
"""
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response


class AdminPanelView(APIView):
    """Serve the admin panel HTML page."""
    permission_classes = []

    def get(self, request):
        key = request.query_params.get('key', '')
        if key != 'appbook-admin-2026':
            return Response({'error': 'Invalid key. Use ?key=appbook-admin-2026'}, status=403)

        return render(request, 'books/admin_authors.html', {'admin_key': key})

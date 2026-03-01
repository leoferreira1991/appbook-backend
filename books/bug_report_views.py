from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.mail import send_mail
from django.conf import settings
import cloudinary.uploader

from .models import BugReport


class BugReportView(APIView):
    """Submit and list bug reports. Sends email notification and saves to DB."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        """List bug reports (filterable by date)."""
        reports = BugReport.objects.filter(user=request.user)
        
        # Optional date filters
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        if from_date:
            reports = reports.filter(created_at__gte=from_date)
        if to_date:
            reports = reports.filter(created_at__lte=to_date)
        
        data = [{
            'id': r.id,
            'description': r.description,
            'category': r.category,
            'screenshot_url': r.screenshot_url,
            'created_at': r.created_at.isoformat(),
            'resolved': r.resolved,
        } for r in reports[:50]]
        
        return Response({'reports': data, 'total': reports.count()})

    def post(self, request):
        description = request.data.get('description', '').strip()
        category = request.data.get('category', 'general')
        screenshot = request.FILES.get('screenshot')
        
        if not description:
            return Response({'error': 'La descripción es obligatoria.'}, status=400)
        
        # Upload screenshot to Cloudinary if provided
        screenshot_url = None
        if screenshot:
            try:
                upload_result = cloudinary.uploader.upload(
                    screenshot,
                    folder='appbook/bug_reports',
                    resource_type='image',
                )
                screenshot_url = upload_result.get('secure_url')
            except Exception as e:
                print(f"Screenshot upload error: {e}")
        
        # Save to database
        report = BugReport.objects.create(
            user=request.user,
            description=description,
            category=category,
            screenshot_url=screenshot_url,
        )
        
        # Build email content
        user = request.user
        subject = f'[AppBook Bug Report] {category.upper()} - de {user.username}'
        
        body = (
            f"🐛 Nuevo reporte de error en AppBook\n"
            f"{'='*50}\n\n"
            f"📋 Categoría: {category}\n"
            f"👤 Usuario: {user.username} ({user.email})\n"
            f"🆔 Report ID: {report.id}\n"
            f"📱 Descripción:\n{description}\n\n"
        )
        
        if screenshot_url:
            body += f"📎 Captura de pantalla: {screenshot_url}\n\n"
        
        body += f"{'='*50}\nEnviado desde AppBook"
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.BUG_REPORT_EMAIL],
                fail_silently=False,
            )
            email_sent = True
        except Exception as e:
            print(f"Email send error: {e}")
            email_sent = False
        
        return Response({
            'success': True,
            'report_id': report.id,
            'email_sent': email_sent,
            'screenshot_url': screenshot_url,
            'message': '¡Gracias! Tu reporte fue enviado.' if email_sent else 'Reporte guardado pero hubo un error al enviar el email.',
        })

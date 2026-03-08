from django.http import HttpResponse


def privacy_policy(request):
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Política de Privacidad - AppBook</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.7; }
  .container { max-width: 720px; margin: 0 auto; padding: 40px 24px; }
  h1 { font-size: 28px; margin-bottom: 8px; color: #6c3ce0; }
  .date { color: #666; font-size: 14px; margin-bottom: 32px; }
  h2 { font-size: 20px; margin-top: 28px; margin-bottom: 12px; color: #333; }
  p, li { font-size: 15px; margin-bottom: 12px; }
  ul { padding-left: 24px; }
  .footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid #ddd; font-size: 13px; color: #888; }
</style>
</head>
<body>
<div class="container">
<h1>📚 Política de Privacidad</h1>
<p class="date">Última actualización: 8 de marzo de 2026</p>

<p>AppBook ("nosotros", "la app") respeta tu privacidad. Esta política describe qué datos recopilamos, cómo los usamos y tus derechos.</p>

<h2>1. Datos que recopilamos</h2>
<ul>
<li><strong>Datos de cuenta:</strong> nombre de usuario, correo electrónico y contraseña (encriptada).</li>
<li><strong>Datos de uso:</strong> libros agregados, progreso de lectura, reseñas, citas y actividad en la comunidad.</li>
<li><strong>Datos del dispositivo:</strong> tipo de dispositivo, sistema operativo y versión de la app (para diagnóstico).</li>
<li><strong>Fotos (opcional):</strong> solo si elegís subir una portada de libro o foto de perfil.</li>
</ul>

<h2>2. Cómo usamos tus datos</h2>
<ul>
<li>Proveer y mejorar la experiencia de la app.</li>
<li>Personalizar recomendaciones de libros con inteligencia artificial.</li>
<li>Mostrar anuncios relevantes a través de Google AdMob.</li>
<li>Enviar notificaciones sobre tus desafíos de lectura (si las habilitás).</li>
</ul>

<h2>3. Publicidad</h2>
<p>Usamos <strong>Google AdMob</strong> para mostrar anuncios. AdMob puede recopilar identificadores del dispositivo y datos de uso para personalizar anuncios. Podés consultar la <a href="https://policies.google.com/privacy" style="color:#6c3ce0">política de privacidad de Google</a>.</p>

<h2>4. Compartir datos</h2>
<p><strong>No vendemos tus datos personales.</strong> Solo compartimos información con:</p>
<ul>
<li><strong>Google AdMob:</strong> para la gestión de publicidad.</li>
<li><strong>Open Library API:</strong> para obtener información de libros (sin datos personales).</li>
</ul>

<h2>5. Almacenamiento y seguridad</h2>
<p>Tus datos se almacenan en servidores seguros (Render + PostgreSQL). Las contraseñas se encriptan con hash seguro. Usamos HTTPS para toda la comunicación.</p>

<h2>6. Tus derechos</h2>
<p>Podés en cualquier momento:</p>
<ul>
<li>Acceder a tus datos desde tu perfil en la app.</li>
<li>Solicitar la eliminación de tu cuenta y datos enviando un email a <strong>appbook.soporte@gmail.com</strong>.</li>
<li>Desactivar la personalización de anuncios desde la configuración de tu dispositivo.</li>
</ul>

<h2>7. Menores de edad</h2>
<p>AppBook no está dirigida a menores de 13 años. No recopilamos intencionalmente datos de menores.</p>

<h2>8. Cambios</h2>
<p>Podemos actualizar esta política. Te notificaremos a través de la app sobre cambios significativos.</p>

<h2>9. Contacto</h2>
<p>Para consultas sobre privacidad: <strong>appbook.soporte@gmail.com</strong></p>

<div class="footer">© 2026 AppBook — Ferreira González</div>
</div>
</body>
</html>"""
    return HttpResponse(html)


def terms_of_service(request):
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Términos de Servicio - AppBook</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.7; }
  .container { max-width: 720px; margin: 0 auto; padding: 40px 24px; }
  h1 { font-size: 28px; margin-bottom: 8px; color: #6c3ce0; }
  .date { color: #666; font-size: 14px; margin-bottom: 32px; }
  h2 { font-size: 20px; margin-top: 28px; margin-bottom: 12px; color: #333; }
  p, li { font-size: 15px; margin-bottom: 12px; }
  ul { padding-left: 24px; }
  .footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid #ddd; font-size: 13px; color: #888; }
</style>
</head>
<body>
<div class="container">
<h1>📖 Términos de Servicio</h1>
<p class="date">Última actualización: 8 de marzo de 2026</p>

<h2>1. Aceptación</h2>
<p>Al usar AppBook aceptás estos términos. Si no estás de acuerdo, no uses la app.</p>

<h2>2. Descripción del servicio</h2>
<p>AppBook es una aplicación gratuita para rastrear lecturas, descubrir libros, participar en desafíos y conectar con otros lectores. El servicio incluye publicidad.</p>

<h2>3. Cuenta de usuario</h2>
<ul>
<li>Sos responsable de mantener la seguridad de tu cuenta.</li>
<li>Debés proporcionar información veraz.</li>
<li>Nos reservamos el derecho de suspender cuentas que violen estos términos.</li>
</ul>

<h2>4. Contenido del usuario</h2>
<p>Al publicar reseñas, citas o comentarios, nos otorgás una licencia no exclusiva para mostrar ese contenido dentro de la app. Sos responsable de tu contenido.</p>

<h2>5. Uso aceptable</h2>
<p>No podés:</p>
<ul>
<li>Publicar contenido ofensivo, ilegal o que viole derechos de terceros.</li>
<li>Intentar acceder sin autorización a otros sistemas o cuentas.</li>
<li>Usar la app para spam o actividades comerciales no autorizadas.</li>
</ul>

<h2>6. Propiedad intelectual</h2>
<p>La información de libros proviene de Open Library y otras fuentes públicas. Las portadas y datos bibliográficos pertenecen a sus respectivos titulares.</p>

<h2>7. Limitación de responsabilidad</h2>
<p>AppBook se proporciona "tal cual". No garantizamos la precisión de la información de libros ni la disponibilidad continua del servicio.</p>

<h2>8. Contacto</h2>
<p><strong>appbook.soporte@gmail.com</strong></p>

<div class="footer">© 2026 AppBook — Ferreira González</div>
</div>
</body>
</html>"""
    return HttpResponse(html)


def support(request):
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Soporte - AppBook</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.7; }
  .container { max-width: 720px; margin: 0 auto; padding: 40px 24px; }
  h1 { font-size: 28px; margin-bottom: 8px; color: #6c3ce0; }
  .subtitle { color: #666; font-size: 16px; margin-bottom: 32px; }
  .card { background: white; border-radius: 16px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .card h2 { font-size: 18px; color: #333; margin-bottom: 8px; }
  .card p { font-size: 15px; color: #555; }
  a { color: #6c3ce0; text-decoration: none; }
  .footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid #ddd; font-size: 13px; color: #888; }
</style>
</head>
<body>
<div class="container">
<h1>🛟 Soporte AppBook</h1>
<p class="subtitle">¿Necesitás ayuda? Estamos para asistirte.</p>

<div class="card">
<h2>📧 Contacto</h2>
<p>Escribinos a <a href="mailto:appbook.soporte@gmail.com"><strong>appbook.soporte@gmail.com</strong></a></p>
</div>

<div class="card">
<h2>🐛 Reportar un error</h2>
<p>Podés reportar errores directamente desde la app: <strong>Perfil → Reportar un error</strong>. Incluí capturas de pantalla y una descripción detallada.</p>
</div>

<div class="card">
<h2>❓ Preguntas frecuentes</h2>
<p><strong>¿Cómo agrego un libro?</strong><br>Desde la pestaña Explorar, buscá por título o autor y tocá "Agregar a mi biblioteca".</p>
<p><strong>¿Cómo funciona la IA?</strong><br>Al ver el detalle de un libro, la app puede enriquecer automáticamente la información con sinopsis, biografía del autor y curiosidades.</p>
<p><strong>¿Puedo eliminar mi cuenta?</strong><br>Sí, escribinos a appbook.soporte@gmail.com y procesamos tu solicitud en 48hs.</p>
</div>

<div class="footer">© 2026 AppBook — Ferreira González</div>
</div>
</body>
</html>"""
    return HttpResponse(html)

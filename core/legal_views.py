from django.http import HttpResponse


def homepage(request):
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AppBook — Tu compañero de lectura inteligente</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Inter', -apple-system, sans-serif; background: #0a0a1a; color: #e0e0f0; overflow-x: hidden; }

  /* Hero */
  .hero {
    min-height: 100vh;
    background: linear-gradient(135deg, #0a0a1a 0%, #1a1040 30%, #2d1b69 60%, #1a1040 100%);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center; padding: 40px 24px; position: relative;
  }
  .hero::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at 30% 20%, rgba(108, 60, 224, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 70% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
  }
  .hero-content { position: relative; z-index: 1; max-width: 800px; }
  .emoji-icon { font-size: 80px; margin-bottom: 24px; filter: drop-shadow(0 0 20px rgba(108,60,224,0.5)); }
  .hero h1 { font-size: 56px; font-weight: 800; background: linear-gradient(135deg, #fff 0%, #c4b5fd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 16px; letter-spacing: -1px; }
  .hero .tagline { font-size: 22px; color: #a78bfa; font-weight: 300; margin-bottom: 40px; }
  .hero .desc { font-size: 17px; color: #9ca3af; line-height: 1.7; max-width: 600px; margin: 0 auto 48px; }

  /* Badges */
  .badges { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; margin-bottom: 48px; }
  .badge { display: inline-flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); padding: 14px 28px; border-radius: 16px; color: #fff; font-weight: 500; font-size: 15px; transition: all 0.3s; cursor: pointer; text-decoration: none; }
  .badge:hover { background: rgba(108,60,224,0.3); border-color: rgba(108,60,224,0.5); transform: translateY(-2px); }
  .badge-icon { font-size: 24px; }

  /* Features */
  .features { padding: 80px 24px; background: linear-gradient(180deg, #0a0a1a 0%, #111127 100%); }
  .features-grid { max-width: 1100px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; }
  .section-title { text-align: center; font-size: 36px; font-weight: 700; margin-bottom: 12px; background: linear-gradient(135deg, #fff, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .section-sub { text-align: center; color: #6b7280; font-size: 16px; margin-bottom: 48px; }
  .feature-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px; padding: 32px; transition: all 0.3s;
  }
  .feature-card:hover { background: rgba(108,60,224,0.08); border-color: rgba(108,60,224,0.2); transform: translateY(-4px); }
  .feature-icon { font-size: 40px; margin-bottom: 16px; }
  .feature-card h3 { font-size: 20px; font-weight: 600; margin-bottom: 10px; color: #f0f0ff; }
  .feature-card p { font-size: 15px; color: #9ca3af; line-height: 1.6; }

  /* How it works */
  .how { padding: 80px 24px; background: #0a0a1a; }
  .steps { max-width: 700px; margin: 0 auto; }
  .step { display: flex; gap: 20px; margin-bottom: 32px; align-items: flex-start; }
  .step-num { min-width: 48px; height: 48px; background: linear-gradient(135deg, #6c3ce0, #8b5cf6); border-radius: 14px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 20px; color: #fff; }
  .step-text h4 { font-size: 18px; font-weight: 600; margin-bottom: 6px; color: #f0f0ff; }
  .step-text p { font-size: 15px; color: #9ca3af; line-height: 1.5; }

  /* Footer */
  .footer { padding: 48px 24px; background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.06); text-align: center; }
  .footer-links { display: flex; gap: 32px; justify-content: center; flex-wrap: wrap; margin-bottom: 24px; }
  .footer-links a { color: #a78bfa; text-decoration: none; font-size: 15px; font-weight: 500; transition: color 0.3s; }
  .footer-links a:hover { color: #c4b5fd; }
  .footer-copy { color: #4b5563; font-size: 13px; }

  /* Responsive */
  @media (max-width: 640px) {
    .hero h1 { font-size: 36px; }
    .hero .tagline { font-size: 18px; }
    .features-grid { grid-template-columns: 1fr; }
    .emoji-icon { font-size: 60px; }
  }

  /* Floating particles */
  .particle { position: absolute; border-radius: 50%; background: rgba(108,60,224,0.3); animation: float 6s infinite ease-in-out; }
  .particle:nth-child(1) { width: 6px; height: 6px; top: 20%; left: 10%; animation-delay: 0s; }
  .particle:nth-child(2) { width: 4px; height: 4px; top: 60%; left: 85%; animation-delay: 2s; }
  .particle:nth-child(3) { width: 8px; height: 8px; top: 40%; left: 70%; animation-delay: 4s; }
  .particle:nth-child(4) { width: 3px; height: 3px; top: 80%; left: 25%; animation-delay: 1s; }
  .particle:nth-child(5) { width: 5px; height: 5px; top: 15%; left: 60%; animation-delay: 3s; }
  @keyframes float { 0%, 100% { transform: translateY(0) scale(1); opacity: 0.5; } 50% { transform: translateY(-20px) scale(1.5); opacity: 1; } }
</style>
</head>
<body>

<section class="hero">
  <div class="particle"></div><div class="particle"></div><div class="particle"></div><div class="particle"></div><div class="particle"></div>
  <div class="hero-content">
    <div class="emoji-icon">📚</div>
    <h1>AppBook</h1>
    <p class="tagline">Tu compañero de lectura inteligente</p>
    <p class="desc">Organizá tu biblioteca personal, descubrí libros con inteligencia artificial, participá en desafíos de lectura y conectá con una comunidad de lectores apasionados.</p>
    <div class="badges">
      <a class="badge" href="#features"><span class="badge-icon">✨</span> Descubrí las funciones</a>
      <a class="badge" href="#how"><span class="badge-icon">📱</span> Cómo funciona</a>
    </div>
  </div>
</section>

<section class="features" id="features">
  <h2 class="section-title">Todo lo que necesitás para leer más</h2>
  <p class="section-sub">Herramientas inteligentes diseñadas para amantes de la lectura</p>
  <div class="features-grid">
    <div class="feature-card">
      <div class="feature-icon">📖</div>
      <h3>Biblioteca Personal</h3>
      <p>Buscá libros por título o autor, agregalos a tu biblioteca y hacé seguimiento de tu progreso de lectura página a página.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🤖</div>
      <h3>Potenciado por IA</h3>
      <p>Enriquecé automáticamente la información de tus libros con sinopsis detalladas, biografías de autores y datos curiosos.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🏆</div>
      <h3>Desafíos de Lectura</h3>
      <p>Creá desafíos personalizados, fijá metas de páginas por día y seguí tu progreso con estadísticas detalladas.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🔍</div>
      <h3>Explorá y Descubrí</h3>
      <p>Encontrá nuevos libros con recomendaciones personalizadas, reseñas de la comunidad y búsqueda inteligente.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">💬</div>
      <h3>Comunidad</h3>
      <p>Conectá con otros lectores, compartí citas memorables, escribí reseñas y descubrí qué están leyendo los demás.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">📊</div>
      <h3>Estadísticas</h3>
      <p>Visualizá tu progreso de lectura, páginas leídas por día, libros completados y más con gráficos intuitivos.</p>
    </div>
  </div>
</section>

<section class="how" id="how">
  <h2 class="section-title">Cómo funciona</h2>
  <p class="section-sub">Empezá a usar AppBook en 3 simples pasos</p>
  <div class="steps">
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-text">
        <h4>Creá tu cuenta</h4>
        <p>Registrate con tu nombre de usuario y email. En segundos tenés tu perfil listo para empezar.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">2</div>
      <div class="step-text">
        <h4>Agregá tus libros</h4>
        <p>Buscá cualquier libro por título o autor y agregalo a tu biblioteca personal. La IA enriquece automáticamente la información.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">3</div>
      <div class="step-text">
        <h4>Leé y compartí</h4>
        <p>Registrá tu progreso, participá en desafíos, escribí reseñas y conectá con otros lectores en la comunidad.</p>
      </div>
    </div>
  </div>
</section>

<footer class="footer">
  <div class="footer-links">
    <a href="/privacy/">Política de Privacidad</a>
    <a href="/terms/">Términos de Servicio</a>
    <a href="/support/">Soporte</a>
    <a href="/delete-account/">Eliminar Cuenta</a>
  </div>
  <p class="footer-copy">© 2026 AppBook — Ferreira González · Hecho con 💜 para lectores</p>
</footer>

</body>
</html>"""
    return HttpResponse(html)

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


def delete_account(request):
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Eliminar Cuenta - AppBook</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.7; }
  .container { max-width: 720px; margin: 0 auto; padding: 40px 24px; }
  h1 { font-size: 28px; margin-bottom: 8px; color: #6c3ce0; }
  .subtitle { color: #666; font-size: 16px; margin-bottom: 32px; }
  .card { background: white; border-radius: 16px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .card h2 { font-size: 18px; color: #333; margin-bottom: 12px; }
  .card p, .card li { font-size: 15px; color: #555; margin-bottom: 8px; }
  ul { padding-left: 24px; }
  a { color: #6c3ce0; text-decoration: none; font-weight: 600; }
  .btn { display: inline-block; background: #6c3ce0; color: white; padding: 12px 32px; border-radius: 12px; font-size: 16px; margin-top: 16px; }
  .footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid #ddd; font-size: 13px; color: #888; }
</style>
</head>
<body>
<div class="container">
<h1>🗑️ Eliminar mi cuenta</h1>
<p class="subtitle">Lamentamos que quieras irte. Aquí te explicamos cómo solicitar la eliminación de tu cuenta y datos.</p>

<div class="card">
<h2>📧 Solicitar eliminación por email</h2>
<p>Enviá un email a <a href="mailto:appbook.soporte@gmail.com">appbook.soporte@gmail.com</a> con el asunto <strong>"Eliminar mi cuenta"</strong> e incluí:</p>
<ul>
<li>Tu nombre de usuario en AppBook</li>
<li>El correo electrónico asociado a tu cuenta</li>
</ul>
<p>Procesaremos tu solicitud en un plazo de <strong>48 horas hábiles</strong>.</p>
</div>

<div class="card">
<h2>📋 ¿Qué datos se eliminan?</h2>
<ul>
<li>Tu perfil de usuario y credenciales</li>
<li>Tu biblioteca de libros y progreso de lectura</li>
<li>Tus reseñas, citas y comentarios</li>
<li>Tu participación en desafíos de lectura</li>
<li>Tus interacciones en la comunidad (likes, follows)</li>
</ul>
<p><strong>Todos tus datos se eliminan permanentemente y no pueden recuperarse.</strong></p>
</div>

<div class="card">
<h2>⏱️ Plazo de eliminación</h2>
<p>Los datos se eliminan dentro de los <strong>30 días</strong> posteriores a la confirmación de tu solicitud.</p>
</div>

<div class="footer">© 2026 AppBook — Ferreira González</div>
</div>
</body>
</html>"""
    return HttpResponse(html)

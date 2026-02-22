"""
Seed script to create test data for the AppBook project.
Run with: venv/bin/python3 manage.py shell < seed_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Avoid running setup twice if already configured
import django
django.setup()

from users.models import User
from books.models import Author, Series, Book, ReadingProgress

# Create admin/superuser if not exists
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@booktracker.com',
        'is_staff': True,
        'is_superuser': True,
        'is_booktoker': True,
        'bio': 'El administrador de AppBook. Amante de la fantasia epica.',
        'social_links': {
            'tiktok': 'https://tiktok.com/@booktracker',
            'instagram': 'https://instagram.com/booktracker',
        }
    }
)
if created:
    admin.set_password('admin1234')
    admin.save()
    print(f'[✓] Superuser creado: admin / admin1234')
else:
    print(f'[i] Superuser ya existia: admin')

# Create test user
test_user, created = User.objects.get_or_create(
    username='testlector',
    defaults={
        'email': 'test@booktracker.com',
        'bio': 'Lectora apasionada de sagas de fantasia.',
        'is_booktoker': True,
        'social_links': {
            'instagram': 'https://instagram.com/testlector',
        }
    }
)
if created:
    test_user.set_password('test1234')
    test_user.save()
    print(f'[✓] Usuario de prueba creado: testlector / test1234')
else:
    print(f'[i] Usuario de prueba ya existia: testlector')

# Authors
brandon, _ = Author.objects.get_or_create(
    name='Brandon Sanderson',
    defaults={'bio': 'Autor americano de fantasia epica, conocido por su world-building detallado y sistemas de magia unicos.'}
)
tolkien, _ = Author.objects.get_or_create(
    name='J.R.R. Tolkien',
    defaults={'bio': 'Padre de la fantasia moderna, creador de la Tierra Media.'}
)
rothfuss, _ = Author.objects.get_or_create(
    name='Patrick Rothfuss',
    defaults={'bio': 'Autor de la Cronica del Asesino de Reyes, una de las mejores sagas de fantasia modernas.'}
)
print('[✓] Autores creados/verificados')

# Series
stormlight, _ = Series.objects.get_or_create(
    name='El Archivo de las Tormentas',
    defaults={'description': 'La epica saga de Brandon Sanderson ambientada en Roshar.'}
)
print('[✓] Saga creada/verificada')

# Books
b1, created = Book.objects.get_or_create(
    title='El Camino de los Reyes',
    defaults={
        'author': brandon,
        'series': stormlight,
        'series_number': 1,
        'synopsis': 'Tres caminos convergen en el mundo de Roshar, un mundo azotado por tormentas magicas...',
        'purchase_links': [
            {'store_name': 'Amazon', 'url': 'https://www.amazon.com.ar/s?k=El+Camino+de+los+Reyes'},
            {'store_name': 'Mercado Libre', 'url': 'https://www.mercadolibre.com.ar/camino-de-los-reyes'},
        ]
    }
)
if created:
    print(f'[✓] Libro creado: {b1.title}')

b2, created = Book.objects.get_or_create(
    title='El Nombre del Viento',
    defaults={
        'author': rothfuss,
        'synopsis': 'La extraordinaria historia de Kvothe, contada de su propia mano...',
        'purchase_links': [
            {'store_name': 'Amazon', 'url': 'https://www.amazon.com.ar/s?k=El+Nombre+del+Viento'},
        ]
    }
)
if created:
    print(f'[✓] Libro creado: {b2.title}')

b3, created = Book.objects.get_or_create(
    title='El Senor de los Anillos',
    defaults={
        'author': tolkien,
        'synopsis': 'La historia de Frodo y la Comunidad del Anillo en su viaje para destruir el Unico Anillo.',
        'purchase_links': [
            {'store_name': 'Amazon', 'url': 'https://www.amazon.com.ar/s?k=El+Senor+de+los+Anillos'},
        ]
    }
)
if created:
    print(f'[✓] Libro creado: {b3.title}')

# Reading progress for test user
progress, created = ReadingProgress.objects.get_or_create(
    user=test_user,
    book=b1,
    defaults={
        'current_chapter': 12,
        'total_chapters': 75,
        'is_finished': False,
    }
)
if created:
    print(f'[✓] Progreso de lectura creado: {test_user.username} leyendo {b1.title} - Cap 12/75')

print('\n=== Seed completado exitosamente! ===')
print(f'\nPuedes iniciar sesion con:')
print(f'  Admin:  admin / admin1234')
print(f'  Lector: testlector / test1234')
print(f'\nAPI disponible en: http://127.0.0.1:8000/api/')
print(f'  Libros:    GET /api/books/books/')
print(f'  Autores:   GET /api/books/authors/')
print(f'  Progreso:  GET /api/books/my-progress/')

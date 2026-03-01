"""
Management command to create 10 fictional reader users + 5 editorial profiles.
All fictional users auto-follow the main user.
Run: python manage.py seed_fake_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from books.models import UserBookExternal
from social.models import SocialProfile
import random

User = get_user_model()

FAKE_READERS = [
    {
        'username': 'maria_lectora',
        'first_name': 'María',
        'bio': '📚 Amante de las novelas históricas y los clásicos. Leo 2 libros por semana.',
        'favorite_authors': 'Ken Follett, Isabel Allende, Gabriel García Márquez',
        'favorite_publishers': 'Planeta, Salamandra',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=maria',
        'books': [
            {'title': 'Los pilares de la tierra', 'author': 'Ken Follett', 'status': 'read', 'categories': 'Novela histórica'},
            {'title': 'Cien años de soledad', 'author': 'Gabriel García Márquez', 'status': 'read', 'categories': 'Ficción, Realismo mágico'},
            {'title': 'La casa de los espíritus', 'author': 'Isabel Allende', 'status': 'reading', 'categories': 'Ficción'},
            {'title': 'El amor en los tiempos del cólera', 'author': 'Gabriel García Márquez', 'status': 'want_to_read', 'categories': 'Ficción'},
            {'title': 'Un mundo sin fin', 'author': 'Ken Follett', 'status': 'read', 'categories': 'Novela histórica'},
        ],
    },
    {
        'username': 'carlos_scifi',
        'first_name': 'Carlos',
        'bio': '🚀 Ciencia ficción es mi pasión. Asimov, Clarke, Dick. Si es del espacio, lo leo.',
        'favorite_authors': 'Isaac Asimov, Arthur C. Clarke, Philip K. Dick',
        'favorite_publishers': 'Minotauro, Nova',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=carlos',
        'books': [
            {'title': 'Fundación', 'author': 'Isaac Asimov', 'status': 'read', 'categories': 'Ciencia ficción'},
            {'title': '2001: Una odisea del espacio', 'author': 'Arthur C. Clarke', 'status': 'read', 'categories': 'Ciencia ficción'},
            {'title': '¿Sueñan los androides con ovejas eléctricas?', 'author': 'Philip K. Dick', 'status': 'read', 'categories': 'Ciencia ficción'},
            {'title': 'Neuromante', 'author': 'William Gibson', 'status': 'reading', 'categories': 'Ciencia ficción, Cyberpunk'},
            {'title': 'El fin de la eternidad', 'author': 'Isaac Asimov', 'status': 'read', 'categories': 'Ciencia ficción'},
            {'title': 'Solaris', 'author': 'Stanisław Lem', 'status': 'want_to_read', 'categories': 'Ciencia ficción'},
        ],
    },
    {
        'username': 'lucia_fantasia',
        'first_name': 'Lucía',
        'bio': '🐉 Fantasía épica, dragones y reinos lejanos. Siempre con un mapa desplegado.',
        'favorite_authors': 'J.R.R. Tolkien, Brandon Sanderson, Patrick Rothfuss',
        'favorite_publishers': 'Minotauro, Nova',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=lucia',
        'books': [
            {'title': 'El nombre del viento', 'author': 'Patrick Rothfuss', 'status': 'read', 'categories': 'Fantasía'},
            {'title': 'El señor de los anillos', 'author': 'J.R.R. Tolkien', 'status': 'read', 'categories': 'Fantasía'},
            {'title': 'El camino de los reyes', 'author': 'Brandon Sanderson', 'status': 'reading', 'categories': 'Fantasía épica'},
            {'title': 'Nacidos de la bruma', 'author': 'Brandon Sanderson', 'status': 'read', 'categories': 'Fantasía'},
            {'title': 'El hobbit', 'author': 'J.R.R. Tolkien', 'status': 'read', 'categories': 'Fantasía'},
        ],
    },
    {
        'username': 'andres_thriller',
        'first_name': 'Andrés',
        'bio': '🔪 Thrillers y novela negra. No puedo parar de leer hasta saber quién fue.',
        'favorite_authors': 'Agatha Christie, Stephen King, Dan Brown',
        'favorite_publishers': 'Booket, DeBolsillo',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=andres',
        'books': [
            {'title': 'El código Da Vinci', 'author': 'Dan Brown', 'status': 'read', 'categories': 'Thriller'},
            {'title': 'Asesinato en el Orient Express', 'author': 'Agatha Christie', 'status': 'read', 'categories': 'Misterio'},
            {'title': 'It', 'author': 'Stephen King', 'status': 'reading', 'categories': 'Terror'},
            {'title': 'Inferno', 'author': 'Dan Brown', 'status': 'read', 'categories': 'Thriller'},
            {'title': 'El resplandor', 'author': 'Stephen King', 'status': 'read', 'categories': 'Terror'},
            {'title': 'Diez negritos', 'author': 'Agatha Christie', 'status': 'want_to_read', 'categories': 'Misterio'},
        ],
    },
    {
        'username': 'valentina_romance',
        'first_name': 'Valentina',
        'bio': '💕 Romance contemporáneo y clásicos del amor. Las historias de amor nunca pasan de moda.',
        'favorite_authors': 'Colleen Hoover, Nicholas Sparks, Jane Austen',
        'favorite_publishers': 'Planeta, Vergara',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=valentina',
        'books': [
            {'title': 'Romper el círculo', 'author': 'Colleen Hoover', 'status': 'read', 'categories': 'Romance'},
            {'title': 'Orgullo y prejuicio', 'author': 'Jane Austen', 'status': 'read', 'categories': 'Clásicos, Romance'},
            {'title': 'El diario de Noah', 'author': 'Nicholas Sparks', 'status': 'read', 'categories': 'Romance'},
            {'title': 'Verity', 'author': 'Colleen Hoover', 'status': 'reading', 'categories': 'Thriller, Romance'},
            {'title': 'Persuasión', 'author': 'Jane Austen', 'status': 'want_to_read', 'categories': 'Clásicos'},
        ],
    },
    {
        'username': 'diego_clasicos',
        'first_name': 'Diego',
        'bio': '📖 Clásicos universales y filosofía. Si tiene más de 100 años, probablemente ya lo leí.',
        'favorite_authors': 'Fiodor Dostoievski, Franz Kafka, Albert Camus',
        'favorite_publishers': 'Penguin Clásicos, Alianza',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=diego',
        'books': [
            {'title': 'Crimen y castigo', 'author': 'Fiodor Dostoievski', 'status': 'read', 'categories': 'Clásicos, Ficción'},
            {'title': 'La metamorfosis', 'author': 'Franz Kafka', 'status': 'read', 'categories': 'Clásicos'},
            {'title': 'El extranjero', 'author': 'Albert Camus', 'status': 'read', 'categories': 'Clásicos, Ficción'},
            {'title': 'Los hermanos Karamazov', 'author': 'Fiodor Dostoievski', 'status': 'reading', 'categories': 'Clásicos'},
            {'title': 'El proceso', 'author': 'Franz Kafka', 'status': 'want_to_read', 'categories': 'Clásicos'},
        ],
    },
    {
        'username': 'camila_juvenil',
        'first_name': 'Camila',
        'bio': '✨ YA, fantasía urbana y distopías. BookTok me arruinó el presupuesto.',
        'favorite_authors': 'Suzanne Collins, Sarah J. Maas, Rick Riordan',
        'favorite_publishers': 'Alfaguara, Montena',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=camila',
        'books': [
            {'title': 'Los juegos del hambre', 'author': 'Suzanne Collins', 'status': 'read', 'categories': 'Distopía, Juvenil'},
            {'title': 'Una corte de rosas y espinas', 'author': 'Sarah J. Maas', 'status': 'read', 'categories': 'Fantasía, Romance'},
            {'title': 'Percy Jackson y el ladrón del rayo', 'author': 'Rick Riordan', 'status': 'read', 'categories': 'Fantasía, Juvenil'},
            {'title': 'Trono de cristal', 'author': 'Sarah J. Maas', 'status': 'reading', 'categories': 'Fantasía'},
            {'title': 'En llamas', 'author': 'Suzanne Collins', 'status': 'read', 'categories': 'Distopía'},
        ],
    },
    {
        'username': 'santiago_tech',
        'first_name': 'Santiago',
        'bio': '💻 No-ficción, tecnología y emprendimiento. Leo para aprender y aplicar.',
        'favorite_authors': 'Yuval Noah Harari, Walter Isaacson, Malcolm Gladwell',
        'favorite_publishers': 'Debate, Empresa Activa',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=santiago',
        'books': [
            {'title': 'Sapiens', 'author': 'Yuval Noah Harari', 'status': 'read', 'categories': 'No ficción, Historia'},
            {'title': 'Steve Jobs', 'author': 'Walter Isaacson', 'status': 'read', 'categories': 'Biografía'},
            {'title': 'Outliers', 'author': 'Malcolm Gladwell', 'status': 'read', 'categories': 'No ficción'},
            {'title': 'Homo Deus', 'author': 'Yuval Noah Harari', 'status': 'reading', 'categories': 'No ficción'},
            {'title': '21 lecciones para el siglo XXI', 'author': 'Yuval Noah Harari', 'status': 'want_to_read', 'categories': 'No ficción'},
        ],
    },
    {
        'username': 'paula_poetica',
        'first_name': 'Paula',
        'bio': '🌸 Poesía, ensayo y literatura latinoamericana. Las palabras sanan.',
        'favorite_authors': 'Mario Benedetti, Pablo Neruda, Julio Cortázar',
        'favorite_publishers': 'Alfaguara, Seix Barral',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=paula',
        'books': [
            {'title': 'Rayuela', 'author': 'Julio Cortázar', 'status': 'read', 'categories': 'Ficción, Latinoamericana'},
            {'title': 'Veinte poemas de amor', 'author': 'Pablo Neruda', 'status': 'read', 'categories': 'Poesía'},
            {'title': 'La tregua', 'author': 'Mario Benedetti', 'status': 'read', 'categories': 'Ficción'},
            {'title': 'Bestiario', 'author': 'Julio Cortázar', 'status': 'reading', 'categories': 'Ficción'},
            {'title': 'Canto general', 'author': 'Pablo Neruda', 'status': 'want_to_read', 'categories': 'Poesía'},
        ],
    },
    {
        'username': 'martin_aventura',
        'first_name': 'Martín',
        'bio': '⚔️ Aventura, viajes y exploración. Si Verne o Dumas lo escribió, lo leí.',
        'favorite_authors': 'Julio Verne, Alexandre Dumas, Robert Louis Stevenson',
        'favorite_publishers': 'Penguin Clásicos, Austral',
        'avatar_url': 'https://api.dicebear.com/7.x/avataaars/png?seed=martin',
        'books': [
            {'title': 'La vuelta al mundo en 80 días', 'author': 'Julio Verne', 'status': 'read', 'categories': 'Aventura, Clásicos'},
            {'title': 'Los tres mosqueteros', 'author': 'Alexandre Dumas', 'status': 'read', 'categories': 'Aventura'},
            {'title': 'La isla del tesoro', 'author': 'Robert Louis Stevenson', 'status': 'read', 'categories': 'Aventura'},
            {'title': 'Veinte mil leguas de viaje submarino', 'author': 'Julio Verne', 'status': 'reading', 'categories': 'Ciencia ficción, Aventura'},
            {'title': 'El conde de Montecristo', 'author': 'Alexandre Dumas', 'status': 'read', 'categories': 'Aventura'},
            {'title': 'Miguel Strogoff', 'author': 'Julio Verne', 'status': 'want_to_read', 'categories': 'Aventura'},
        ],
    },
]

EDITORIAL_PROFILES = [
    {
        'name': 'Penguin Random House',
        'handle': 'penguinlibros',
        'platform': 'instagram',
        'profile_type': 'publisher',
        'bio': 'El grupo editorial más grande del mundo. Publicamos los mejores libros en español.',
        'avatar_url': 'https://api.dicebear.com/7.x/identicon/png?seed=penguin',
        'profile_url': 'https://instagram.com/penguinlibros',
        'featured': True,
    },
    {
        'name': 'Editorial Planeta',
        'handle': 'editorialplaneta',
        'platform': 'instagram',
        'profile_type': 'publisher',
        'bio': 'Desde 1949 publicando los mejores autores. Ficción, no ficción y mucho más.',
        'avatar_url': 'https://api.dicebear.com/7.x/identicon/png?seed=planeta',
        'profile_url': 'https://instagram.com/editorialplaneta',
        'featured': True,
    },
    {
        'name': 'Salamandra Editorial',
        'handle': 'salamandra_ed',
        'platform': 'instagram',
        'profile_type': 'publisher',
        'bio': 'Hogar de Harry Potter en español. Ficción juvenil y literatura de calidad.',
        'avatar_url': 'https://api.dicebear.com/7.x/identicon/png?seed=salamandra',
        'profile_url': 'https://instagram.com/salamandra_ed',
        'featured': True,
    },
    {
        'name': 'Anagrama Editorial',
        'handle': 'anagramaed',
        'platform': 'instagram',
        'profile_type': 'publisher',
        'bio': 'Literatura independiente de calidad desde 1969. Ensayo, narrativa y más.',
        'avatar_url': 'https://api.dicebear.com/7.x/identicon/png?seed=anagrama',
        'profile_url': 'https://instagram.com/anagramaed',
        'featured': True,
    },
    {
        'name': 'Alfaguara',
        'handle': 'alfaguaraes',
        'platform': 'instagram',
        'profile_type': 'publisher',
        'bio': 'Gran literatura en español. Autores como Vargas Llosa, Allende y más.',
        'avatar_url': 'https://api.dicebear.com/7.x/identicon/png?seed=alfaguara',
        'profile_url': 'https://instagram.com/alfaguaraes',
        'featured': True,
    },
]


class Command(BaseCommand):
    help = 'Create 10 fictional reader users + 5 editorial profiles for testing'

    def handle(self, *args, **options):
        # Find the main user to auto-follow
        main_user = User.objects.filter(is_superuser=False).exclude(
            username__in=[r['username'] for r in FAKE_READERS]
        ).first()
        
        if not main_user:
            main_user = User.objects.first()
        
        self.stdout.write(f'Main user: {main_user.username} (ID: {main_user.id})')
        
        created_users = 0
        created_books = 0
        
        for reader in FAKE_READERS:
            user, created = User.objects.get_or_create(
                username=reader['username'],
                defaults={
                    'first_name': reader['first_name'],
                    'bio': reader['bio'],
                    'favorite_authors': reader['favorite_authors'],
                    'favorite_publishers': reader['favorite_publishers'],
                    'avatar_url': reader['avatar_url'],
                    'is_booktoker': True,
                }
            )
            
            if created:
                user.set_password('appbook2026!')
                user.save()
                created_users += 1
                self.stdout.write(f'  Created user: {user.username}')
            else:
                self.stdout.write(f'  User exists: {user.username}')
            
            # Auto-follow main user (both directions)
            if main_user:
                user.following.add(main_user)  # fake user follows main user
                main_user.following.add(user)   # main user follows fake user
            
            # Create books for this user
            for book in reader['books']:
                _, book_created = UserBookExternal.objects.get_or_create(
                    user=user,
                    title=book['title'],
                    defaults={
                        'author': book['author'],
                        'status': book['status'],
                        'categories': book['categories'],
                        'total_chapters': random.randint(15, 40),
                        'current_chapter': random.randint(0, 15) if book['status'] == 'reading' else (
                            random.randint(15, 40) if book['status'] == 'read' else 0
                        ),
                    }
                )
                if book_created:
                    created_books += 1
        
        # Create editorial profiles
        created_editorials = 0
        for ed in EDITORIAL_PROFILES:
            _, created = SocialProfile.objects.get_or_create(
                handle=ed['handle'],
                defaults=ed,
            )
            if created:
                created_editorials += 1
        
        # Also create User entries for editorials so they appear in community
        for ed in EDITORIAL_PROFILES:
            user, created = User.objects.get_or_create(
                username=f'ed_{ed["handle"]}',
                defaults={
                    'first_name': ed['name'],
                    'bio': ed['bio'],
                    'avatar_url': ed['avatar_url'],
                    'is_editorial': True,
                }
            )
            if created:
                user.set_password('appbook2026!')
                user.save()
                if main_user:
                    user.following.add(main_user)
                    main_user.following.add(user)
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Done! Created {created_users} users, {created_books} books, {created_editorials} editorial profiles.'
        ))

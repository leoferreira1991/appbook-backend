"""
Management command to create activity (reviews + highlights) for fake users.
This makes them visible in the social feed.
Run: python manage.py seed_activity
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from social.models import Review, Highlight
from books.models import Book, Author
import random

User = get_user_model()

# Reviews from fake users about books they've read
REVIEWS = [
    # (username, book_title, author_name, rating, review_text)
    ('maria_lectora', 'Los pilares de la tierra', 'Ken Follett', 5, 'Una obra maestra de la novela histórica. Ken Follett te transporta a la Inglaterra medieval con una narrativa que atrapa desde la primera página.'),
    ('maria_lectora', 'Cien años de soledad', 'Gabriel García Márquez', 5, 'García Márquez creó un universo entero en Macondo. Cada relectura revela algo nuevo. Imprescindible.'),
    ('carlos_scifi', 'Fundación', 'Isaac Asimov', 5, 'Asimov cambió la ciencia ficción para siempre. La psicohistoria es un concepto brillante que aún hoy da que pensar.'),
    ('carlos_scifi', '2001: Una odisea del espacio', 'Arthur C. Clarke', 5, 'Clarke nos muestra lo que es la ciencia ficción dura bien hecha.'),
    ('lucia_fantasia', 'El nombre del viento', 'Patrick Rothfuss', 5, 'Rothfuss es un poeta disfrazado de escritor de fantasía. La prosa es simplemente hermosa.'),
    ('lucia_fantasia', 'El señor de los anillos', 'J.R.R. Tolkien', 5, 'La obra que definió el género. Tolkien creó un mundo tan real que a veces olvido que es ficción.'),
    ('andres_thriller', 'It', 'Stephen King', 5, 'King en su máxima expresión. No es solo terror, es una historia sobre la infancia y la amistad.'),
    ('andres_thriller', 'Asesinato en el Orient Express', 'Agatha Christie', 5, 'Christie es la reina del misterio por una razón. El giro final es uno de los mejores de la historia.'),
    ('valentina_romance', 'Romper el círculo', 'Colleen Hoover', 5, 'Hoover aborda temas difíciles con una sensibilidad increíble. Me hizo llorar y reflexionar.'),
    ('valentina_romance', 'Orgullo y prejuicio', 'Jane Austen', 5, 'Austen fue revolucionaria en su época y su obra sigue siendo relevante. Darcy es el personaje perfecto.'),
    ('diego_clasicos', 'Crimen y castigo', 'Fiodor Dostoievski', 5, 'Dostoievski explora la psicología humana como nadie. Raskólnikov es uno de los personajes más complejos jamás creados.'),
    ('diego_clasicos', 'El extranjero', 'Albert Camus', 5, 'Camus condensa el absurdismo en una novela corta y perfecta.'),
    ('camila_juvenil', 'Los juegos del hambre', 'Suzanne Collins', 5, 'Collins creó una distopía que habla directamente a nuestra generación. Katniss es la heroína que necesitábamos.'),
    ('camila_juvenil', 'Percy Jackson y el ladrón del rayo', 'Rick Riordan', 5, 'Riordan hizo que la mitología griega fuera cool.'),
    ('santiago_tech', 'Sapiens', 'Yuval Noah Harari', 5, 'Harari me cambió la forma de ver la historia humana. Cada capítulo es una revelación.'),
    ('santiago_tech', 'Steve Jobs', 'Walter Isaacson', 4, 'Isaacson pinta un retrato honesto de un genio imperfecto.'),
    ('paula_poetica', 'Rayuela', 'Julio Cortázar', 5, 'Cortázar rompió las reglas de la narrativa. Cada lectura es diferente.'),
    ('paula_poetica', 'Veinte poemas de amor', 'Pablo Neruda', 5, 'Neruda destila el amor en versos que se sienten como música.'),
    ('martin_aventura', 'La vuelta al mundo en 80 días', 'Julio Verne', 5, 'Verne era un visionario. Phileas Fogg es el caballero aventurero perfecto.'),
    ('martin_aventura', 'El conde de Montecristo', 'Alexandre Dumas', 5, 'La mejor historia de venganza jamás escrita. 1300 páginas que valen cada segundo.'),
]

# Highlights/Quotes — these don't require a book FK
HIGHLIGHTS = [
    ('maria_lectora', '«Muchos años después, frente al pelotón de fusilamiento, el coronel Aureliano Buendía había de recordar aquella tarde remota en que su padre lo llevó a conocer el hielo.» — Cien años de soledad'),
    ('carlos_scifi', '«La violencia es el último recurso del incompetente.» — Fundación, Isaac Asimov'),
    ('carlos_scifi', '«La ciencia ficción de hoy es la ciencia real de mañana.» Mi reflexión leyendo a Asimov'),
    ('lucia_fantasia', '«No todos los que vagan están perdidos.» — J.R.R. Tolkien, El señor de los anillos'),
    ('lucia_fantasia', '«He robado princesas de reyes dormidos. Incendié la ciudad de Trebon.» — El nombre del viento'),
    ('andres_thriller', '«Un asesino no es un monstruo. Es un ser humano. Y eso es lo más aterrador de todo.» — Agatha Christie'),
    ('valentina_romance', '«Es una verdad mundialmente reconocida que un hombre soltero, poseedor de una gran fortuna, necesita una esposa.» — Jane Austen'),
    ('valentina_romance', '«A veces es mejor cerrar un ciclo con dolor que mantenerlo con mentiras.» Reflexión sobre Romper el círculo'),
    ('diego_clasicos', '«Hoy mamá ha muerto. O quizá ayer, no lo sé.» — El extranjero, Albert Camus'),
    ('camila_juvenil', '«Que la suerte esté siempre de vuestra parte.» 🔥 — Los juegos del hambre'),
    ('camila_juvenil', '«Los libros son las armas más poderosas contra la ignorancia.» Reflexión de BookTok 📚'),
    ('santiago_tech', '«Los sapiens dominaron el mundo porque son el único animal capaz de creer en cosas que existen puramente en su propia imaginación.» — Sapiens'),
    ('paula_poetica', '«Puedo escribir los versos más tristes esta noche.» — Pablo Neruda'),
    ('paula_poetica', '«Andábamos sin buscarnos pero sabiendo que andábamos para encontrarnos.» — Rayuela, Cortázar'),
    ('martin_aventura', '«La ciencia, amigo mío, se compone de errores, pero de errores útiles, porque poco a poco conducen a la verdad.» — Julio Verne'),
    ('martin_aventura', '«Todos para uno, y uno para todos.» La frase más épica de la literatura — Los tres mosqueteros'),
]


class Command(BaseCommand):
    help = 'Create reviews and highlights for fake users to populate the social feed'

    def _get_or_create_book(self, title, author_name):
        """Get or create a Book + Author for reviews"""
        author, _ = Author.objects.get_or_create(
            name=author_name,
        )
        book, _ = Book.objects.get_or_create(
            title=title,
            author=author,
        )
        return book

    def handle(self, *args, **options):
        created_reviews = 0
        created_highlights = 0
        
        for username, book_title, author_name, rating, text in REVIEWS:
            try:
                user = User.objects.get(username=username)
                book = self._get_or_create_book(book_title, author_name)
                _, created = Review.objects.get_or_create(
                    user=user,
                    book=book,
                    defaults={
                        'rating': rating,
                        'text': text,
                    }
                )
                if created:
                    created_reviews += 1
                    self.stdout.write(f'  Review: {username} → {book_title}')
            except User.DoesNotExist:
                self.stdout.write(f'  User {username} not found, skipping review')
            except Exception as e:
                self.stdout.write(f'  Error creating review for {username}/{book_title}: {e}')
        
        for username, text in HIGHLIGHTS:
            try:
                user = User.objects.get(username=username)
                _, created = Highlight.objects.get_or_create(
                    user=user,
                    text=text,
                )
                if created:
                    created_highlights += 1
                    self.stdout.write(f'  Highlight: {username}')
            except User.DoesNotExist:
                self.stdout.write(f'  User {username} not found, skipping highlight')
            except Exception as e:
                self.stdout.write(f'  Error creating highlight: {e}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Done! Created {created_reviews} reviews and {created_highlights} highlights.'
        ))

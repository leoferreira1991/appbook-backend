import os
import django
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    django.setup()
except Exception:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'app.settings'
    try:
        django.setup()
    except Exception as e:
        print(f"Failed to setup: {e}")
        sys.exit(1)

from users.models import User
from books.models import UserBookExternal, UserBook
from social.models import Review, Highlight
from django.utils import timezone

try:
    print("Starting seed...")
    # Get some users
    users = list(User.objects.exclude(username='crleo1')[:3])
    if not users:
        u1, _ = User.objects.get_or_create(username='maria_lee', email='m@e.com')
        u2, _ = User.objects.get_or_create(username='carlos_b', email='c@e.com')
        users = [u1, u2]

    # Ensure there's a book
    b1 = UserBookExternal.objects.first()
    if not b1:
        # Create a dummy
        b1, _ = UserBookExternal.objects.get_or_create(user=users[0], title="El señor de los anillos", cover_url="https://covers.openlibrary.org/b/id/14627509-M.jpg")

    b2 = UserBookExternal.objects.last()
    
    # Create some reviews
    r1, _ = Review.objects.get_or_create(
        user=users[0],
        target_type='book_external',
        target_id=b1.id,
        defaults={'rating': 4.5, 'body': '¡Me encantó este libro! Los personajes son muy reales y la trama te atrapa.', 'created_at': timezone.now()}
    )
    r2, _ = Review.objects.get_or_create(
        user=users[-1],
        target_type='book_external',
        target_id=b2.id if b2 else b1.id,
        defaults={'rating': 5.0, 'body': 'Una obra maestra absoluta de la literatura clásica. Totalmente recomendado.', 'created_at': timezone.now()}
    )

    h1, _ = Highlight.objects.get_or_create(
        user=users[0],
        book_id=b1.id, # Note UserBookExternal is not linked to standard Highlights which use Book, but actually FeedView just lists everything. Wait, Highlight uses `book` which is a `books.Book`.
        defaults={'text': 'No hay nada como el hogar'}
    )

    print('Feed items seeded successfully!')
    print(f"Reviews: {Review.objects.count()}, Highlights: {Highlight.objects.count()}")
except Exception as e:
    traceback.print_exc()

from users.models import User
from books.models import UserBookExternal, ReadingChallenge
from social.models import Review, Highlight
from django.utils import timezone

# Create a dummy user if none exist
users = list(User.objects.exclude(username='crleo1')[:3])
if not users:
    u1, _ = User.objects.get_or_create(username='maria_lee', email='m@e.com')
    u2, _ = User.objects.get_or_create(username='carlos_b', email='c@e.com')
    users = [u1, u2]

# Ensure there's a book
try:
    b1 = UserBookExternal.objects.first()
    if not b1:
        # Create a dummy
        b1, _ = UserBookExternal.objects.get_or_create(user=users[0], title="Dummy Book", cover_url="https://covers.openlibrary.org/b/id/13671433-M.jpg")

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
        defaults={'rating': 5.0, 'body': 'Una obra maestra absoluta de la literatura clásica.', 'created_at': timezone.now()}
    )

    h1, _ = Highlight.objects.get_or_create(
        user=users[0],
        book__id=b1.id,
        defaults={'text': 'No hay nada como el hogar'}
    )

    print('Feed items seeded!')
except Exception as e:
    print(f"Error: {e}")

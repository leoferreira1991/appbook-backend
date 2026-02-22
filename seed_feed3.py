from users.models import User
from books.models import Book, UserBookExternal
from social.models import Review, Highlight
from django.utils import timezone

try:
    users = list(User.objects.exclude(username='crleo1')[:2])
    if not users:
        u1, _ = User.objects.get_or_create(username='maria_lee', email='m@e.com')
        users = [u1]

    # Create a real Book for Highlight
    b, _ = Book.objects.get_or_create(
        title="1984", 
        defaults={'description': 'Novela distópica', 'page_count': 328}
    )

    # Use existing UserBookExternal for Review
    bex, _ = UserBookExternal.objects.get_or_create(
        user=users[0], title="El señor de los anillos", defaults={'cover_url': "https://covers.openlibrary.org/b/id/14627509-M.jpg"}
    )
    
    Review.objects.get_or_create(
        user=users[0], target_type='book_external', target_id=bex.id, defaults={'rating': 5.0, 'body': '¡Me encantó!', 'created_at': timezone.now()}
    )
    
    Highlight.objects.get_or_create(
        user=users[0], book=b, defaults={'text': 'El Gran Hermano te vigila.'}
    )

    print('Feed items seeded successfully!')
except Exception as e:
    print(e)

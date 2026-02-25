import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from books.models import Book, Author, UserBook
from social.models import SocialInteraction, Review

User = get_user_model()

def seed_special_profiles():
    # 1. Editorials
    editorial_data = [
        {
            'username': 'planeta_libros',
            'first_name': 'Editorial',
            'last_name': 'Planeta',
            'bio': 'Líder en edición en español. Descubrí tu próxima gran lectura.',
            'avatar_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Logo_del_Grupo_Planeta.svg/1200px-Logo_del_Grupo_Planeta.svg.png'
        },
        {
            'username': 'penguin_esp',
            'first_name': 'Penguin',
            'last_name': 'Random House',
            'bio': 'Libros para todos los lectores. Construyendo el futuro de la edición.',
            'avatar_url': 'https://1000marcas.net/wp-content/uploads/2021/04/Penguin-Logo.png'
        }
    ]

    # 2. AIs
    ai_data = [
        {
            'username': 'sci_fi_bot',
            'first_name': 'Isaac',
            'last_name': 'Asimov (AI)',
            'bio': 'Analizo y leo libros de ciencia ficción a la velocidad de la luz. Me gusta la tecnología.',
            'avatar_url': 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png'
        },
        {
            'username': 'romance_ai',
            'first_name': 'Jane',
            'last_name': 'Austen (AI)',
            'bio': 'AI especializada en romance histórico y contemporáneo. Experta en corazones rotos.',
            'avatar_url': 'https://cdn-icons-png.flaticon.com/512/864/864685.png'
        }
    ]

    print("--- Creating Editorials ---")
    editorials_created = []
    for ed in editorial_data:
        user, created = User.objects.get_or_create(
            username=ed['username'],
            defaults={
                'first_name': ed['first_name'],
                'last_name': ed['last_name'],
                'bio': ed['bio'],
                'avatar_url': ed['avatar_url'],
                'is_editorial': True
            }
        )
        if created:
            user.set_password('editorial123')
            user.save()
            print(f"Created editorial: {user.username}")
        else:
            print(f"Editorial {user.username} already exists")
        editorials_created.append(user)

    print("--- Creating AIs ---")
    ais_created = []
    for ai in ai_data:
        user, created = User.objects.get_or_create(
            username=ai['username'],
            defaults={
                'first_name': ai['first_name'],
                'last_name': ai['last_name'],
                'bio': ai['bio'],
                'avatar_url': ai['avatar_url'],
                'is_ai': True
            }
        )
        if created:
            user.set_password('ai123')
            user.save()
            print(f"Created AI: {user.username}")
        else:
            print(f"AI {user.username} already exists")
        ais_created.append(user)

    # 3. Add some books to their libraries
    all_books = list(Book.objects.all()[:10])
    if not all_books:
        print("No books in DB to add to profiles.")
        return

    print("--- Giving books to test profiles ---")
    for profile in editorials_created + ais_created:
        # Give them 3 random books
        import random
        selected_books = random.sample(all_books, min(3, len(all_books)))
        for b in selected_books:
            ub, c = UserBook.objects.get_or_create(
                user=profile,
                book=b,
                defaults={
                    'status': UserBook.STATUS_READ,
                    'rating': random.randint(3, 5)
                }
            )
            if c:
                # Add a review
                Review.objects.create(
                    user=profile,
                    book=b,
                    rating=ub.rating,
                    text=f"Una lectura muy interesante por parte de {profile.first_name}."
                )
        print(f"Added {len(selected_books)} books to {profile.username}")

    print("Done generating special profiles!")

if __name__ == '__main__':
    seed_special_profiles()

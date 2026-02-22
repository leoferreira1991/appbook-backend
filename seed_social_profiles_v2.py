import os
import django

def seed():
    from social.models import SocialProfile
    profiles = [
        # TikTok - Booktokers
        {
            'name': 'Booktok Argentina',
            'handle': 'booktok_ar',
            'platform': 'tiktok',
            'profile_type': 'booktoker',
            'bio': 'Lo mejor de la literatura juvenil en Argentina.',
            'profile_url': 'https://www.tiktok.com/@booktok',
            'order': 1
        },
        {
            'name': 'Victoria Reseña',
            'handle': 'vicky_books',
            'platform': 'tiktok',
            'profile_type': 'booktoker',
            'bio': 'Amante de los thrillers y el café.',
            'profile_url': 'https://www.tiktok.com/@vicky_books',
            'order': 2
        },
        # Instagram
        {
            'name': 'Lectores Unidos',
            'handle': 'lectores_unidos',
            'platform': 'instagram',
            'profile_type': 'booktoker',
            'bio': 'Comunidad de lectura y debates mensuales.',
            'profile_url': 'https://www.instagram.com/lectores_unidos',
            'order': 1
        },
        {
            'name': 'Editorial Planeta',
            'handle': 'planetadelibros',
            'platform': 'instagram',
            'profile_type': 'publisher',
            'bio': 'Novedades editoriales y eventos literarios.',
            'profile_url': 'https://www.instagram.com/planetadelibros',
            'order': 2
        },
        # Facebook
        {
            'name': 'Club de Lectura Clásica',
            'handle': 'club_clasicos',
            'platform': 'facebook',
            'profile_type': 'booktoker',
            'bio': 'Grupo para entusiastas de la literatura clásica.',
            'profile_url': 'https://www.facebook.com/groups/lectura_clasica',
            'order': 1
        },
    ]

    for p in profiles:
        SocialProfile.objects.get_or_create(
            platform=p['platform'],
            handle=p['handle'],
            defaults={
                'name': p['name'],
                'profile_type': p['profile_type'],
                'bio': p['bio'],
                'profile_url': p['profile_url'],
                'order': p['order']
            }
        )
    print("Social profiles seeded successfully!")

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    seed()

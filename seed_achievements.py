import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import Achievement

def seed_achievements():
    achievements = [
        {
            'code': 'first_book',
            'name': 'Primer Libro',
            'description': '¡Terminaste tu primer libro en AppBook!',
            'icon_name': 'emoji_events_rounded',
            'xp_reward': 100
        },
        {
            'code': 'night_owl',
            'name': 'Lector Nocturno',
            'description': 'Registraste una lectura después de las 11 PM.',
            'icon_name': 'nights_stay_rounded',
            'xp_reward': 50
        },
        {
            'code': 'streak_7',
            'name': 'Racha de 7 días',
            'description': 'Leíste durante 7 días consecutivos.',
            'icon_name': 'bolt_rounded',
            'xp_reward': 200
        },
        {
            'code': 'social_butterfly',
            'name': 'Sociable',
            'description': 'Seguiste a 5 personas o editoriales.',
            'icon_name': 'people_rounded',
            'xp_reward': 50
        },
    ]

    for a in achievements:
        obj, created = Achievement.objects.update_or_create(
            code=a['code'],
            defaults=a
        )
        if created:
            print(f"Created achievement: {a['name']}")
        else:
            print(f"Updated achievement: {a['name']}")

if __name__ == '__main__':
    seed_achievements()

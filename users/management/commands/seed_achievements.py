from django.core.management.base import BaseCommand
from users.models import Achievement


ACHIEVEMENTS = [
    {'code': 'first_book', 'name': '📖 Primer Libro', 'description': 'Agregaste tu primer libro a la biblioteca', 'icon_name': 'menu_book', 'xp_reward': 50},
    {'code': 'five_books', 'name': '📚 Lector Activo', 'description': 'Tienes 5 libros en tu biblioteca', 'icon_name': 'library_books', 'xp_reward': 100},
    {'code': 'ten_books', 'name': '🏛️ Bibliófilo', 'description': 'Tienes 10 libros en tu biblioteca', 'icon_name': 'auto_stories', 'xp_reward': 200},
    {'code': 'twenty_books', 'name': '📖 Gran Biblioteca', 'description': 'Tienes 20 libros en tu biblioteca', 'icon_name': 'collections_bookmark', 'xp_reward': 300},
    {'code': 'first_read', 'name': '✅ Primer Libro Leído', 'description': 'Completaste tu primer libro', 'icon_name': 'check_circle', 'xp_reward': 100},
    {'code': 'five_read', 'name': '🌟 Lector Dedicado', 'description': 'Leíste 5 libros completos', 'icon_name': 'star', 'xp_reward': 250},
    {'code': 'ten_read', 'name': '🏆 Lector Experto', 'description': 'Leíste 10 libros completos', 'icon_name': 'emoji_events', 'xp_reward': 500},
    {'code': 'streak_3', 'name': '🔥 Racha de 3 días', 'description': 'Leíste 3 días seguidos', 'icon_name': 'local_fire_department', 'xp_reward': 75},
    {'code': 'streak_7', 'name': '🔥🔥 Semana lectora', 'description': 'Leíste 7 días seguidos', 'icon_name': 'whatshot', 'xp_reward': 150},
    {'code': 'streak_30', 'name': '💎 Mes completo', 'description': 'Leíste 30 días seguidos', 'icon_name': 'diamond', 'xp_reward': 500},
    {'code': 'first_highlight', 'name': '✍️ Primera Frase', 'description': 'Guardaste tu primera frase o highlight', 'icon_name': 'format_quote', 'xp_reward': 50},
    {'code': 'first_challenge', 'name': '🎯 Primer Desafío', 'description': 'Creaste tu primer desafío de lectura', 'icon_name': 'flag', 'xp_reward': 75},
    {'code': 'diverse_reader', 'name': '🌍 Lector Diverso', 'description': 'Leíste libros de 3 géneros diferentes', 'icon_name': 'public', 'xp_reward': 150},
    {'code': 'genre_master', 'name': '🎓 Maestro del Género', 'description': 'Leíste 5+ libros de un mismo género', 'icon_name': 'school', 'xp_reward': 200},
]


class Command(BaseCommand):
    help = 'Seed default achievements into the database'

    def handle(self, *args, **options):
        created_count = 0
        for data in ACHIEVEMENTS:
            _, created = Achievement.objects.update_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Seeded {created_count} new achievements (total: {len(ACHIEVEMENTS)})'))

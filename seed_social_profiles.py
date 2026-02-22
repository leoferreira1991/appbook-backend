import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from social.models import SocialProfile

def seed_profiles():
    profiles = [
        # TikTok - Publishers
        {'name': 'Victoria Resco', 'handle': 'victoriaresco', 'platform': 'tiktok', 'profile_type': 'booktoker', 'bio': 'Escritora y lectora compulsiva.', 'profile_url': 'https://www.tiktok.com/@victoriaresco', 'featured': True, 'order': 1},
        {'name': 'Penguin Libros', 'handle': 'penguinlibros', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Lo que leemos en Penguin Random House.', 'profile_url': 'https://www.tiktok.com/@penguinlibros', 'featured': True, 'order': 2},
        {'name': 'Editorial Planeta', 'handle': 'planetadelibros', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Novedades editoriales.', 'profile_url': 'https://www.tiktok.com/@planetadelibros', 'featured': True, 'order': 3},
        {'name': 'Anagrama Editor', 'handle': 'anagrama_editor', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Literatura y debate.', 'profile_url': 'https://www.tiktok.com/@anagrama_editor', 'featured': False, 'order': 10},
        {'name': 'Urano Argentina', 'handle': 'uranoargentina', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Mundo Urano.', 'profile_url': 'https://www.tiktok.com/@uranoargentina', 'featured': False, 'order': 11},
        {'name': 'VR Editoras', 'handle': 'vreditores', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Libros con alma.', 'profile_url': 'https://www.tiktok.com/@vreditores', 'featured': False, 'order': 12},
        {'name': 'VRYA', 'handle': 'vryalectoras', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Juvenil y más.', 'profile_url': 'https://www.tiktok.com/@vryalectoras', 'featured': False, 'order': 13},
        {'name': 'Sexto Piso', 'handle': 'sextopiso', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Editorial independiente.', 'profile_url': 'https://www.tiktok.com/@sextopiso', 'featured': False, 'order': 14},
        {'name': 'Almadía', 'handle': 'editorialalmadia', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Libros de Oaxaca.', 'profile_url': 'https://www.tiktok.com/@editorialalmadia', 'featured': False, 'order': 15},
        {'name': 'Minotauro', 'handle': 'edminotauro', 'platform': 'tiktok', 'profile_type': 'publisher', 'bio': 'Fantasía y CF.', 'profile_url': 'https://www.tiktok.com/@edminotauro', 'featured': False, 'order': 16},

        # Instagram - Publishers
        {'name': 'Planeta de Libros', 'handle': 'planetadelibros', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Universo Planeta.', 'profile_url': 'https://www.instagram.com/planetadelibros/', 'featured': True, 'order': 4},
        {'name': 'Penguin Argentina', 'handle': 'penguinlibrosar', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Penguin Random House Arg.', 'profile_url': 'https://www.instagram.com/penguinlibrosar/', 'featured': True, 'order': 5},
        {'name': 'Editorial Salamandra', 'handle': 'editorialsalamandra', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Harry Potter y más.', 'profile_url': 'https://www.instagram.com/editorialsalamandra/', 'featured': True, 'order': 6},
        {'name': 'RBA Libros', 'handle': 'rbalibros', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'No ficción y clásicos.', 'profile_url': 'https://www.instagram.com/rbalibros/', 'featured': False, 'order': 20},
        {'name': 'Acantilado', 'handle': 'editorial_acantilado', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Clásicos y contemporáneos.', 'profile_url': 'https://www.instagram.com/editorial_acantilado/', 'featured': False, 'order': 21},
        {'name': 'Nordica Libros', 'handle': 'nordica_libros', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Ilustrados y nórdicos.', 'profile_url': 'https://www.instagram.com/nordica_libros/', 'featured': False, 'order': 22},
        {'name': 'Eterna Cadencia', 'handle': 'eternacadencia', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Librería y editorial.', 'profile_url': 'https://www.instagram.com/eternacadencia/', 'featured': False, 'order': 23},
        {'name': 'Impedimenta', 'handle': 'editorial_impedimenta', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Libros para siempre.', 'profile_url': 'https://www.instagram.com/editorial_impedimenta/', 'featured': False, 'order': 24},
        {'name': 'Sirianda Ediciones', 'handle': 'siruelaediciones', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Mitos y cuentos.', 'profile_url': 'https://www.instagram.com/siruelaediciones/', 'featured': False, 'order': 25},
        {'name': 'Gallo Nero', 'handle': 'galloneroediciones', 'platform': 'instagram', 'profile_type': 'publisher', 'bio': 'Narrativa visual.', 'profile_url': 'https://www.instagram.com/galloneroediciones/', 'featured': False, 'order': 26},

        # Facebook - Publishers
        {'name': 'Planeta de Libros Arg', 'handle': 'PlanetadeLibrosArgentina', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Comunidad Planeta.', 'profile_url': 'https://www.facebook.com/PlanetadeLibrosArgentina', 'featured': True, 'order': 7},
        {'name': 'Penguin Libros Arg', 'handle': 'PenguinLibrosAR', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': ' Penguin Random House.', 'profile_url': 'https://www.facebook.com/PenguinLibrosAR', 'featured': True, 'order': 8},
        {'name': 'FCE Argentina', 'handle': 'fceargentina', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Fondo de Cultura Económica.', 'profile_url': 'https://www.facebook.com/fceargentina', 'featured': True, 'order': 9},
        {'name': 'Siglo XXI Editores', 'handle': 'sigloxxiargentina', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Ciencias sociales.', 'profile_url': 'https://www.facebook.com/sigloxxiargentina', 'featured': False, 'order': 30},
        {'name': 'Editorial Biblos', 'handle': 'EditorialBiblos', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Investigación académica.', 'profile_url': 'https://www.facebook.com/EditorialBiblos', 'featured': False, 'order': 31},
        {'name': 'Prometeo Editorial', 'handle': 'prometeoeditorial', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Pensamiento crítico.', 'profile_url': 'https://www.facebook.com/prometeoeditorial', 'featured': False, 'order': 32},
        {'name': 'Tusquets Editores', 'handle': 'TusquetsEditoresArgentina', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Narrativa de calidad.', 'profile_url': 'https://www.facebook.com/TusquetsEditoresArgentina', 'featured': False, 'order': 33},
        {'name': 'Seix Barral Arg', 'handle': 'SeixBarralArgentina', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Literatura contemporánea.', 'profile_url': 'https://www.facebook.com/SeixBarralArgentina', 'featured': False, 'order': 34},
        {'name': 'Ariel Libros', 'handle': 'ArielLibrosArgentina', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Divulgación.', 'profile_url': 'https://www.facebook.com/ArielLibrosArgentina', 'featured': False, 'order': 35},
        {'name': 'Paidós Arg', 'handle': 'PaidosArgentina', 'platform': 'facebook', 'profile_type': 'publisher', 'bio': 'Psicología y más.', 'profile_url': 'https://www.facebook.com/PaidosArgentina', 'featured': False, 'order': 36},

        # Extra Booktokers/Influencers
        {'name': 'Almendra Veiga', 'handle': 'almenveiga', 'platform': 'instagram', 'profile_type': 'booktoker', 'bio': 'Bibliófila.', 'profile_url': 'https://www.instagram.com/almenveiga/', 'featured': False, 'order': 40},
        {'name': 'Coos Burton', 'handle': 'coosburton', 'platform': 'tiktok', 'profile_type': 'booktoker', 'bio': 'Lector voraz.', 'profile_url': 'https://www.tiktok.com/@coosburton', 'featured': False, 'order': 41},
        {'name': 'Matías G.B.', 'handle': 'matiasgb', 'platform': 'instagram', 'profile_type': 'booktoker', 'bio': 'Reseñas y más.', 'profile_url': 'https://www.instagram.com/matiasgb/', 'featured': False, 'order': 42},
    ]

    for p in profiles:
        SocialProfile.objects.update_or_create(
            handle=p['handle'],
            platform=p['platform'],
            defaults=p
        )
    print("Social profiles seeded successfully!")

if __name__ == '__main__':
    seed_profiles()

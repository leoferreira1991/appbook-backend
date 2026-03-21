"""
Admin endpoint to trigger author seeding in background on Render.
This avoids HTTP timeout by starting the work in a thread.
"""
import threading
from django.conf import settings
from django import db as django_db
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .ai_author import _generate_author_profile, _get_author_photo_url, _cache_author_profile
from .models import CachedAuthor

# Seeding state (in-memory, resets on restart)
_seeding_state = {
    'running': False,
    'processed': 0,
    'total': 0,
    'errors': 0,
    'current': '',
    'completed': [],
}

FAMOUS_AUTHORS = [
    # ─── English-language classics & bestsellers ─────────────────
    "Agatha Christie", "Stephen King", "J.K. Rowling", "George R.R. Martin",
    "J.R.R. Tolkien", "Jane Austen", "Charles Dickens", "Mark Twain",
    "Ernest Hemingway", "F. Scott Fitzgerald", "William Shakespeare",
    "Edgar Allan Poe", "Oscar Wilde", "Arthur Conan Doyle", "H.G. Wells",
    "Ray Bradbury", "Isaac Asimov", "Philip K. Dick", "Kurt Vonnegut",
    "George Orwell", "Aldous Huxley", "Virginia Woolf", "Emily Brontë",
    "Charlotte Brontë", "Mary Shelley", "Bram Stoker", "H.P. Lovecraft",
    "Roald Dahl", "C.S. Lewis", "Lewis Carroll", "Louisa May Alcott",
    "Harper Lee", "John Steinbeck", "William Faulkner", "Toni Morrison",
    "Maya Angelou", "Truman Capote", "Jack London", "Herman Melville",
    "Nathaniel Hawthorne", "Henry James", "Joseph Conrad", "Rudyard Kipling",
    "Robert Louis Stevenson", "Daniel Defoe", "Jonathan Swift", "James Joyce",
    "Samuel Beckett", "D.H. Lawrence", "E.M. Forster", "Evelyn Waugh",
    "Graham Greene", "Ian Fleming", "John le Carré", "Ken Follett",
    "Dan Brown", "Michael Crichton", "Tom Clancy", "John Grisham",
    "James Patterson", "Nora Roberts", "Danielle Steel", "Nicholas Sparks",
    "Dean Koontz", "Neil Gaiman", "Terry Pratchett",
    "Brandon Sanderson", "Patrick Rothfuss", "Robert Jordan", "Ursula K. Le Guin",
    "Robin Hobb", "Anne McCaffrey", "Frank Herbert", "Orson Scott Card",
    "Margaret Atwood", "Kazuo Ishiguro", "Salman Rushdie", "Ian McEwan",
    "Colleen Hoover", "Sally Rooney", "Donna Tartt", "Gillian Flynn",
    "Paula Hawkins", "Stieg Larsson", "Lee Child", "Jeffrey Archer",
    "Sidney Sheldon", "Frederick Forsyth", "Wilbur Smith", "Robert Ludlum",
    "Michael Connelly", "Dennis Lehane", "Harlan Coben",
    "Mary Higgins Clark",
    "Suzanne Collins", "Veronica Roth", "Rick Riordan", "Cassandra Clare",
    "Sarah J. Maas", "Leigh Bardugo", "Holly Black", "Madeline Miller",
    "Celeste Ng", "Taylor Jenkins Reid", "Delia Owens",
    "Andy Weir", "Blake Crouch", "Amor Towles", "Anthony Doerr",
    "Khaled Hosseini", "Yann Martel", "Alice Walker", "Chimamanda Ngozi Adichie",
    "Cormac McCarthy", "Philip Roth", "Saul Bellow", "John Updike",
    "Raymond Chandler", "Dashiell Hammett", "Agatha Raisin",
    "P.D. James", "Ruth Rendell", "Dorothy L. Sayers",
    "Daphne du Maurier", "Shirley Jackson", "Flannery O'Connor",
    "Carson McCullers", "Sylvia Plath", "J.D. Salinger",
    "Chuck Palahniuk", "Bret Easton Ellis", "Don DeLillo", "Thomas Pynchon",
    "David Mitchell", "Zadie Smith", "Hilary Mantel",
    "Bernardine Evaristo", "Douglas Adams", "Clive Barker",
    "Anne Rice", "Peter Benchley", "Robin Cook",
    "Karin Slaughter", "Tess Gerritsen", "Patricia Cornwell",
    "Janet Evanovich", "Sue Grafton", "Sara Paretsky",
    "Scott Turow", "David Baldacci", "Brad Thor",
    "Vince Flynn", "Nelson DeMille", "Clive Cussler",
    "Erin Morgenstern", "Hanya Yanagihara",

    # ─── Spanish-language authors ────────────────────────────────
    "Gabriel García Márquez", "Jorge Luis Borges", "Mario Vargas Llosa",
    "Isabel Allende", "Pablo Neruda", "Julio Cortázar", "Carlos Ruiz Zafón",
    "Miguel de Cervantes", "Federico García Lorca", "Arturo Pérez-Reverte",
    "Antonio Machado", "Benito Pérez Galdós", "Camilo José Cela",
    "Miguel de Unamuno", "Gustavo Adolfo Bécquer", "Juan Rulfo",
    "Octavio Paz", "Roberto Bolaño", "Horacio Quiroga", "Ernesto Sabato",
    "Adolfo Bioy Casares", "Eduardo Galeano", "Mario Benedetti",
    "Laura Esquivel", "Elena Poniatowska", "Carlos Fuentes",
    "Alejo Carpentier", "Leopoldo Lugones",
    "Alfonsina Storni", "Rosalía de Castro", "Miguel Hernández",
    "Ana María Matute", "Carmen Laforet", "Rosa Montero",
    "Almudena Grandes", "Javier Marías", "Eduardo Mendoza",
    "Manuel Vázquez Montalbán", "Dolores Redondo", "María Dueñas",
    "Santiago Posteguillo", "Ildefonso Falcones", "Julia Navarro",
    "Eva García Sáenz de Urturi", "Blue Jeans", "Elisabet Benavent",
    "Albert Espinosa", "Jordi Sierra i Fabra",
    "Diego Fischer", "Florencia Bonelli", "Federico Axat",
    "Claudia Piñeiro", "Samanta Schweblin", "Mariana Enriquez",
    "Hernán Casciari", "Leonardo Padura",
    "Antonio Muñoz Molina", "Fernando Aramburu", "Luz Gabás",
    # More Spanish-language contemporary
    "Javier Castillo", "Juan Gómez-Jurado", "Megan Maxwell",
    "Carmen Mola", "Sonsoles Ónega", "Irene Vallejo",
    "Pérez-Reverte", "Lorenzo Silva", "Andrés Trapiello",
    "Matilde Asensi", "Reyes Monforte",
    # Latinoamerican additions
    "Gioconda Belli", "Sergio Ramírez", "Augusto Roa Bastos",
    "Rómulo Gallegos", "José Donoso", "Manuel Puig",
    "Reinaldo Arenas", "Guillermo Cabrera Infante",
    "César Vallejo", "Rubén Darío", "Gabriela Mistral",
    "José Martí", "Ricardo Güiraldes", "Leopoldo Marechal",
    "Silvina Ocampo", "Victoria Ocampo",
    # Uruguayan authors
    "Juan Carlos Onetti", "Juana de Ibarbourou", "Eduardo Acevedo Díaz",
    "Felisberto Hernández", "Idea Vilariño", "Cristina Peri Rossi",
    "Carlos Liscano", "Hugo Burel", "Mercedes Vigil",

    # ─── Portuguese-language authors ─────────────────────────────
    "José Saramago", "Fernando Pessoa", "Machado de Assis",
    "Jorge Amado", "Clarice Lispector", "Paulo Coelho",
    "Eça de Queirós", "Guimarães Rosa", "Cecília Meireles",
    "Carlos Drummond de Andrade", "Graciliano Ramos",
    "José de Alencar", "Monteiro Lobato",
    "Mia Couto", "Lygia Fagundes Telles", "Érico Veríssimo",
    "Chico Buarque",

    # ─── French-language authors ─────────────────────────────────
    "Victor Hugo", "Alexandre Dumas", "Julio Verne", "Albert Camus",
    "Jean-Paul Sartre", "Gustave Flaubert", "Émile Zola",
    "Honoré de Balzac", "Stendhal", "Marcel Proust",
    "Antoine de Saint-Exupéry", "Voltaire", "Molière",
    "Guy de Maupassant", "Simone de Beauvoir",
    "Marguerite Yourcenar", "Michel Houellebecq",
    "Amélie Nothomb", "Marc Levy", "Guillaume Musso",
    "Fred Vargas", "Pierre Lemaitre",
    "Marguerite Duras", "André Gide", "Françoise Sagan",
    "Bernard Werber", "Jean-Christophe Grangé",

    # ─── Russian-language authors ────────────────────────────────
    "Fiódor Dostoievski", "León Tolstói", "Antón Chéjov",
    "Nikolái Gógol", "Aleksandr Pushkin",
    "Mijaíl Bulgákov", "Boris Pasternak", "Aleksandr Solzhenitsyn",
    "Iván Turguénev", "Anna Ajmátova", "Marina Tsvetáyeva",

    # ─── German-language authors ─────────────────────────────────
    "Franz Kafka", "Hermann Hesse", "Thomas Mann", "Johann Wolfgang von Goethe",
    "Patrick Süskind", "Stefan Zweig", "Erich Maria Remarque",
    "Bernhard Schlink", "Michael Ende",

    # ─── Italian-language authors ────────────────────────────────
    "Dante Alighieri", "Umberto Eco", "Italo Calvino", "Luigi Pirandello",
    "Elena Ferrante", "Andrea Camilleri", "Alessandro Baricco",
    "Primo Levi",

    # ─── Japanese-language authors ───────────────────────────────
    "Haruki Murakami", "Yukio Mishima", "Banana Yoshimoto",
    "Keigo Higashino",

    # ─── Scandinavian authors ────────────────────────────────────
    "Jo Nesbø", "Henning Mankell", "Astrid Lindgren",
    "Hans Christian Andersen", "Fredrik Backman",

    # ─── Other world literature ──────────────────────────────────
    "Naguib Mahfouz", "Orhan Pamuk", "Elif Shafak",
    "Milan Kundera", "Amos Oz",

    # ─── Contemporary bestsellers & trending ─────────────────────
    "Emily Henry", "Ali Hazelwood",
    "Freida McFadden", "Rebecca Yarros", "Ana Huang",
    "Lisa Jewell", "Ruth Ware", "Lucy Foley",
    "Alex Michaelides", "R.F. Kuang",
    "Naomi Novik", "V.E. Schwab",


    # ─── Self-help & non-fiction popular ─────────────────────────
    "Dale Carnegie", "Napoleon Hill", "Robert Kiyosaki",
    "Yuval Noah Harari", "James Clear", "Mark Manson",
    "Ryan Holiday", "Viktor Frankl",

    # ─── Science Fiction & Fantasy greats ────────────────────────
    "Arthur C. Clarke", "Robert A. Heinlein", "Stanislaw Lem",
    "Octavia E. Butler", "N.K. Jemisin",
    "Joe Abercrombie", "Raymond E. Feist",
    "Terry Brooks", "R.A. Salvatore",

    # ─── More classics ───────────────────────────────────────────
    "Homero", "Sófocles", "Platón", "Sun Tzu",

    # ─── Horror / Thriller ───────────────────────────────────────
    "Thomas Harris", "Richard Matheson",
    "Joe Hill",

    # ─── Romance & contemporary fiction ──────────────────────────
    "Jojo Moyes", "Sophie Kinsella", "Liane Moriarty",
    "Kristin Hannah", "Julia Quinn",
]


def _seed_worker():
    """Background worker that generates and caches author profiles."""
    import time

    # Close stale DB connections from previous requests
    django_db.close_old_connections()

    # Deduplicate
    unique = list(dict.fromkeys(FAMOUS_AUTHORS))

    # Filter out already-cached authors (only skip if they have enough works)
    to_process = []
    for name in unique:
        try:
            cached = CachedAuthor.objects.get(name__iexact=name)
            # Only skip if the author has a substantial bibliography (15+ works)
            # Authors with fewer works may have been cached before the improved GPT prompt
            if cached.works.count() >= 15:
                continue
        except CachedAuthor.DoesNotExist:
            pass
        to_process.append(name)

    _seeding_state['total'] = len(to_process)
    _seeding_state['processed'] = 0
    _seeding_state['errors'] = 0
    _seeding_state['completed'] = []

    for i, author_name in enumerate(to_process):
        if not _seeding_state['running']:
            break  # Allow stopping

        _seeding_state['current'] = author_name
        try:
            # Refresh DB connections periodically to prevent stale connections
            if i % 5 == 0:
                django_db.close_old_connections()

            profile_data = _generate_author_profile(author_name)
            if profile_data and 'name' in profile_data:
                # CRITICAL: Force the name to match our list to prevent duplicates
                profile_data['name'] = author_name
                photo_url = _get_author_photo_url(profile_data.get('name', author_name))
                profile_data['photo_url'] = photo_url
                author = _cache_author_profile(profile_data)
                works_count = author.works.count()
                _seeding_state['completed'].append(f"✅ {author.name} ({works_count} obras)")
            else:
                _seeding_state['errors'] += 1
                _seeding_state['completed'].append(f"❌ {author_name} (GPT empty)")
        except Exception as e:
            import traceback
            _seeding_state['errors'] += 1
            _seeding_state['completed'].append(f"❌ {author_name} ({str(e)[:50]})")
            traceback.print_exc()

        _seeding_state['processed'] = i + 1

        # Rate limiting: small pause between requests
        if (i + 1) % 5 == 0:
            time.sleep(1)

    _seeding_state['running'] = False
    _seeding_state['current'] = 'DONE'
    django_db.close_old_connections()


ADMIN_KEY = 'appbook-admin-2026'


def _check_admin_key(request):
    key = request.query_params.get('key', '') or request.data.get('key', '')
    return key == ADMIN_KEY


class SeedAuthorsView(APIView):
    permission_classes = []  # Allow key-based auth

    def post(self, request):
        """Start the seeding process in background."""
        # Accept either JWT auth or admin key
        if not _check_admin_key(request) and not (request.user and request.user.is_authenticated):
            return Response({'error': 'Authentication required (JWT or admin key)'}, status=403)

        if _seeding_state['running']:
            return Response({
                'status': 'already_running',
                'processed': _seeding_state['processed'],
                'total': _seeding_state['total'],
                'current': _seeding_state['current'],
            })

        _seeding_state['running'] = True
        thread = threading.Thread(target=_seed_worker, daemon=True)
        thread.start()

        return Response({
            'status': 'started',
            'message': 'Seeding started in background',
        })

    def get(self, request):
        """Check seeding progress."""
        # Accept either JWT auth or admin key
        if not _check_admin_key(request) and not (request.user and request.user.is_authenticated):
            return Response({'error': 'Authentication required (JWT or admin key)'}, status=403)

        # Count total cached
        total_cached = CachedAuthor.objects.count()
        last_completed = _seeding_state['completed'][-10:] if _seeding_state['completed'] else []

        return Response({
            'running': _seeding_state['running'],
            'processed': _seeding_state['processed'],
            'total': _seeding_state['total'],
            'errors': _seeding_state['errors'],
            'current': _seeding_state['current'],
            'total_cached_in_db': total_cached,
            'last_completed': last_completed,
        })


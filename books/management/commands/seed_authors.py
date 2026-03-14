"""
Management command to pre-populate the CachedAuthor table with
the world's most popular/searched authors.
Run: python manage.py seed_authors [--batch N]
"""
from django.core.management.base import BaseCommand
from books.ai_author import _generate_author_profile, _get_author_photo_url, _cache_author_profile
from books.models import CachedAuthor
import time


# Top ~500 authors worldwide across languages
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
    "Dean Koontz", "Clive Barker", "Neil Gaiman", "Terry Pratchett",
    "Brandon Sanderson", "Patrick Rothfuss", "Robert Jordan", "Ursula K. Le Guin",
    "Robin Hobb", "Anne McCaffrey", "Frank Herbert", "Orson Scott Card",
    "Margaret Atwood", "Kazuo Ishiguro", "Salman Rushdie", "Ian McEwan",
    "Colleen Hoover", "Sally Rooney", "Donna Tartt", "Gillian Flynn",
    "Paula Hawkins", "Stieg Larsson", "Lee Child", "Jeffrey Archer",
    "Sidney Sheldon", "Frederick Forsyth", "Wilbur Smith", "Robert Ludlum",
    "Peter Benchley", "Michael Connelly", "Dennis Lehane", "Harlan Coben",
    "Mary Higgins Clark", "V.C. Andrews", "Jackie Collins",
    "Suzanne Collins", "Veronica Roth", "Rick Riordan", "Cassandra Clare",
    "Sarah J. Maas", "Leigh Bardugo", "Holly Black", "Madeline Miller",
    "Celeste Ng", "Brit Bennett", "Taylor Jenkins Reid", "Delia Owens",
    "Andy Weir", "Blake Crouch", "Amor Towles", "Anthony Doerr",
    "Khaled Hosseini", "Yann Martel", "Alice Walker", "Chimamanda Ngozi Adichie",

    # ─── Spanish-language authors ────────────────────────────────
    "Gabriel García Márquez", "Jorge Luis Borges", "Mario Vargas Llosa",
    "Isabel Allende", "Pablo Neruda", "Julio Cortázar", "Carlos Ruiz Zafón",
    "Miguel de Cervantes", "Federico García Lorca", "Arturo Pérez-Reverte",
    "Antonio Machado", "Benito Pérez Galdós", "Camilo José Cela",
    "Miguel de Unamuno", "Gustavo Adolfo Bécquer", "Juan Rulfo",
    "Octavio Paz", "Roberto Bolaño", "Horacio Quiroga", "Ernesto Sabato",
    "Adolfo Bioy Casares", "Eduardo Galeano", "Mario Benedetti",
    "Laura Esquivel", "Elena Poniatowska", "Carlos Fuentes",
    "Alejo Carpentier", "José Saramago", "Leopoldo Lugones",
    "Alfonsina Storni", "Rosalía de Castro", "Miguel Hernández",
    "Ana María Matute", "Carmen Laforet", "Rosa Montero",
    "Almudena Grandes", "Javier Marías", "Eduardo Mendoza",
    "Manuel Vázquez Montalbán", "Dolores Redondo", "María Dueñas",
    "Santiago Posteguillo", "Ildefonso Falcones", "Julia Navarro",
    "Eva García Sáenz de Urturi", "Blue Jeans", "Elisabet Benavent",
    "Elísabet Benavent", "Albert Espinosa", "Jordi Sierra i Fabra",

    # ─── Portuguese-language authors ─────────────────────────────
    "José Saramago", "Fernando Pessoa", "Machado de Assis",
    "Jorge Amado", "Clarice Lispector", "Paulo Coelho",
    "Eça de Queirós", "Guimarães Rosa", "Cecília Meireles",
    "Carlos Drummond de Andrade", "Manuel Bandeira", "Graciliano Ramos",
    "José de Alencar", "Monteiro Lobato", "Vinícius de Moraes",
    "Mia Couto", "Pepetela", "Luís de Camões",
    "Lygia Fagundes Telles", "Rachel de Queiroz", "Érico Veríssimo",
    "Rubem Fonseca", "Chico Buarque", "João Ubaldo Ribeiro",

    # ─── French-language authors ─────────────────────────────────
    "Victor Hugo", "Alexandre Dumas", "Julio Verne", "Albert Camus",
    "Jean-Paul Sartre", "Gustave Flaubert", "Émile Zola",
    "Honoré de Balzac", "Stendhal", "Marcel Proust",
    "Antoine de Saint-Exupéry", "Voltaire", "Molière",
    "Jean de La Fontaine", "Guy de Maupassant", "Colette",
    "Simone de Beauvoir", "André Gide", "Marguerite Duras",
    "Marguerite Yourcenar", "Michel Houellebecq", "Patrick Modiano",
    "Amélie Nothomb", "Marc Levy", "Guillaume Musso",
    "Fred Vargas", "Pierre Lemaitre", "Françoise Sagan",

    # ─── Russian-language authors ────────────────────────────────
    "Fiódor Dostoievski", "León Tolstói", "Antón Chéjov",
    "Nikolái Gógol", "Aleksandr Pushkin", "Iván Turguénev",
    "Mijaíl Bulgákov", "Boris Pasternak", "Aleksandr Solzhenitsyn",
    "Anna Ajmátova", "Marina Tsvetáyeva", "Máximo Gorki",

    # ─── German-language authors ─────────────────────────────────
    "Franz Kafka", "Hermann Hesse", "Thomas Mann", "Johann Wolfgang von Goethe",
    "Friedrich Schiller", "Günter Grass", "Patrick Süskind",
    "Stefan Zweig", "Erich Maria Remarque", "Bernhard Schlink",
    "Michael Ende", "Heinrich Böll", "Rainer Maria Rilke",

    # ─── Italian-language authors ────────────────────────────────
    "Dante Alighieri", "Umberto Eco", "Italo Calvino", "Luigi Pirandello",
    "Giovanni Boccaccio", "Cesare Pavese", "Alberto Moravia",
    "Elena Ferrante", "Andrea Camilleri", "Alessandro Baricco",
    "Niccolò Ammaniti", "Primo Levi",

    # ─── Japanese-language authors ───────────────────────────────
    "Haruki Murakami", "Yukio Mishima", "Banana Yoshimoto",
    "Kenzaburō Ōe", "Natsume Sōseki", "Ryūnosuke Akutagawa",
    "Keigo Higashino", "Yōko Ogawa",

    # ─── Scandinavian authors ────────────────────────────────────
    "Jo Nesbø", "Henning Mankell", "Astrid Lindgren",
    "Hans Christian Andersen", "Henrik Ibsen", "Karin Fossum",
    "Lars Kepler", "Camilla Läckberg", "Fredrik Backman",

    # ─── Other world literature ──────────────────────────────────
    "Fyodor Dostoevsky", "Leo Tolstoy", "Anton Chekhov",
    "Naguib Mahfouz", "Orhan Pamuk", "Elif Shafak",
    "Yaşar Kemal", "Banana Yoshimoto", "Mo Yan",
    "Herta Müller", "Olga Tokarczuk", "Wisława Szymborska",
    "Milan Kundera", "Bohumil Hrabal", "Amos Oz",
    "José María Eça de Queiroz",

    # ─── Classic children's/YA ───────────────────────────────────
    "Enid Blyton", "R.L. Stine", "Judy Blume",
    "Lois Lowry", "Madeleine L'Engle", "Beverly Cleary",
    "Roald Dahl", "Dr. Seuss", "Maurice Sendak",

    # ─── Contemporary bestsellers & trending ─────────────────────
    "Colleen Hoover", "Emily Henry", "Ali Hazelwood",
    "Freida McFadden", "Rebecca Yarros", "Ana Huang",
    "Penelope Douglas", "Tessa Bailey", "Christina Lauren",
    "Lisa Jewell", "Ruth Ware", "Lucy Foley",
    "Alex Michaelides", "A.J. Finn", "Grady Hendrix",
    "T.J. Klune", "Travis Baldree", "R.F. Kuang",
    "Fourth Wing", "Naomi Novik", "V.E. Schwab",
    "Leigh Bardugo", "Holly Black", "Tamora Pierce",

    # ─── More Spanish-language contemporary ──────────────────────
    "Diego Fischer", "Florencia Bonelli", "Federico Axat",
    "Claudia Piñeiro", "Samanta Schweblin", "Mariana Enriquez",
    "Hernán Casciari", "Sergio Olguín", "Leonardo Padura",
    "Antonio Muñoz Molina", "Fernando Aramburu", "Luz Gabás",
    "Joël Dicker", "César Aira", "Ricardo Piglia",
    "Manuel Puig", "Silvina Ocampo", "Alejandro Zambra",

    # ─── Self-help & non-fiction popular ─────────────────────────
    "Dale Carnegie", "Napoleon Hill", "Robert Kiyosaki",
    "Brené Brown", "Malcolm Gladwell", "Yuval Noah Harari",
    "Daniel Kahneman", "James Clear", "Mark Manson",
    "Ryan Holiday", "Cal Newport", "Nassim Nicholas Taleb",
    "Viktor Frankl", "Eckhart Tolle", "Deepak Chopra",

    # ─── More classics ───────────────────────────────────────────
    "Homero", "Virgilio", "Ovidio", "Sófocles", "Eurípides",
    "Esquilo", "Aristófanes", "Platón", "Aristóteles",
    "Sun Tzu", "Lao Tse", "Confucio",

    # ─── Horror & Thriller ───────────────────────────────────────
    "Thomas Harris", "Peter Straub", "Shirley Jackson",
    "Richard Matheson", "Robert Bloch", "Ira Levin",
    "Joe Hill", "Paul Tremblay", "Grady Hendrix",

    # ─── Science Fiction & Fantasy greats ────────────────────────
    "Arthur C. Clarke", "Robert A. Heinlein", "Stanislaw Lem",
    "Octavia E. Butler", "N.K. Jemisin", "Becky Chambers",
    "Ann Leckie", "Martha Wells", "China Miéville",
    "Joe Abercrombie", "Mark Lawrence", "Brent Weeks",
    "Peter V. Brett", "Brian Sanderson", "Raymond E. Feist",
    "David Eddings", "Terry Brooks", "Tad Williams",
    "R.A. Salvatore", "Margaret Weis", "Tracy Hickman",

    # ─── Romance & contemporary fiction ──────────────────────────
    "Jane Austen", "Nicholas Sparks", "Jojo Moyes",
    "Sophie Kinsella", "Marian Keyes", "Liane Moriarty",
    "Big Little Lies", "Diane Chamberlain", "Kristin Hannah",
    "Lisa Kleypas", "Julia Quinn", "Courtney Milan",
]


class Command(BaseCommand):
    help = 'Pre-populate CachedAuthor with profiles of famous authors'

    def add_arguments(self, parser):
        parser.add_argument('--batch', type=int, default=10,
                            help='Number of authors to process per batch (default: 10)')
        parser.add_argument('--start', type=int, default=0,
                            help='Start index in the list (for resuming)')
        parser.add_argument('--limit', type=int, default=0,
                            help='Max authors to process (0 = all)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Just show which authors would be processed')

    def handle(self, *args, **options):
        batch_size = options['batch']
        start = options['start']
        limit = options['limit']
        dry_run = options['dry_run']

        # Deduplicate list
        unique_authors = list(dict.fromkeys(FAMOUS_AUTHORS))
        self.stdout.write(f"Total unique authors in list: {len(unique_authors)}")

        # Check which ones are already cached with enough works
        already_cached = set(
            CachedAuthor.objects.filter(
                name__in=unique_authors
            ).values_list('name', flat=True)
        )
        # Also check case-insensitive
        for author in unique_authors[:]:
            if CachedAuthor.objects.filter(name__iexact=author).exists():
                cached_obj = CachedAuthor.objects.filter(name__iexact=author).first()
                if cached_obj and cached_obj.works.count() >= 15:
                    already_cached.add(author)

        to_process = [a for a in unique_authors if a not in already_cached]
        self.stdout.write(f"Already cached (with ≥15 works): {len(already_cached)}")
        self.stdout.write(f"To process: {len(to_process)}")

        if start > 0:
            to_process = to_process[start:]
            self.stdout.write(f"After start offset ({start}): {len(to_process)} remaining")

        if limit > 0:
            to_process = to_process[:limit]
            self.stdout.write(f"Limited to: {len(to_process)}")

        if dry_run:
            for i, author in enumerate(to_process):
                self.stdout.write(f"  [{i+1}] {author}")
            return

        success = 0
        errors = 0
        for i, author_name in enumerate(to_process):
            self.stdout.write(f"[{i+1}/{len(to_process)}] Generating: {author_name}...")
            try:
                profile_data = _generate_author_profile(author_name)
                if profile_data and 'name' in profile_data:
                    photo_url = _get_author_photo_url(profile_data.get('name', author_name))
                    profile_data['photo_url'] = photo_url
                    author = _cache_author_profile(profile_data)
                    works_count = author.works.count()
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✅ {author.name} — {works_count} obras cached"
                    ))
                    success += 1
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ {author_name} — GPT returned empty"
                    ))
                    errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ {author_name} — {e}"))
                errors += 1

            # Rate limiting: wait between batches
            if (i + 1) % batch_size == 0:
                self.stdout.write(f"  ⏳ Batch of {batch_size} done, waiting 2s...")
                time.sleep(2)

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Done! Success: {success}, Errors: {errors}"
        ))

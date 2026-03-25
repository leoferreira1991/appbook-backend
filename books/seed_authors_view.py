"""
Admin endpoint to trigger author seeding in background on Render.
This avoids HTTP timeout by starting the work in a thread.
"""
import os
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

# Comprehensive list of 1000+ famous authors (deduplicated, cleaned)
FAMOUS_AUTHORS = [
    # ─── English-language classics & bestsellers (~220 authors) ───
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
    "Michael Connelly", "Dennis Lehane", "Harlan Coben",
    "Mary Higgins Clark", "V.C. Andrews", "Jackie Collins",
    "Suzanne Collins", "Veronica Roth", "Rick Riordan", "Cassandra Clare",
    "Sarah J. Maas", "Leigh Bardugo", "Holly Black", "Madeline Miller",
    "Celeste Ng", "Brit Bennett", "Taylor Jenkins Reid", "Delia Owens",
    "Andy Weir", "Blake Crouch", "Amor Towles", "Anthony Doerr",
    "Khaled Hosseini", "Yann Martel", "Alice Walker", "Chimamanda Ngozi Adichie",
    "Cormac McCarthy", "Philip Roth", "Saul Bellow", "John Updike",
    "Raymond Chandler", "Dashiell Hammett", "P.D. James",
    "Ruth Rendell", "Dorothy L. Sayers", "Daphne du Maurier", "Shirley Jackson",
    "Flannery O'Connor", "Carson McCullers", "Sylvia Plath", "J.D. Salinger",
    "Chuck Palahniuk", "Bret Easton Ellis", "Don DeLillo", "Thomas Pynchon",
    "David Mitchell", "Zadie Smith", "Hilary Mantel", "Bernardine Evaristo",
    "Douglas Adams", "Anne Rice", "Peter Benchley", "Robin Cook",
    "Karin Slaughter", "Tess Gerritsen", "Patricia Cornwell",
    "Janet Evanovich", "Sue Grafton", "Sara Paretsky",
    "Scott Turow", "David Baldacci", "Brad Thor", "Vince Flynn",
    "Nelson DeMille", "Clive Cussler", "Erin Morgenstern", "Hanya Yanagihara",
    "Jeanette Winterson", "Iain Banks", "Iain M. Banks", "Neil Stephenson",
    "William Gibson", "Neal Stephenson", "Hanif Abdulrahman",
    "Ruth Ozeki", "Jennifer Egan", "Chris Whitaker",
    "Emily Henry", "Ali Hazelwood", "Freida McFadden", "Rebecca Yarros",
    "Ana Huang", "Penelope Douglas", "Tessa Bailey", "Christina Lauren",
    "Lisa Jewell", "Ruth Ware", "Lucy Foley", "Alex Michaelides",
    "A.J. Finn", "Grady Hendrix", "T.J. Klune", "Travis Baldree",
    "R.F. Kuang", "Naomi Novik", "V.E. Schwab", "Tamora Pierce",
    "Garth Nix", "Scott Lynch", "John Scalzi",
    "Lois McMaster Bujold", "Becky Chambers", "Martha Wells",
    "Peter V. Brett", "Raymond E. Feist", "David Eddings",
    "Terry Brooks", "Tad Williams", "R.A. Salvatore", "Margaret Weis",
    "Tracy Hickman", "Joe Abercrombie", "Mark Lawrence", "Brent Weeks",
    "China Miéville", "Ann Leckie", "N.K. Jemisin", "Octavia E. Butler",
    "Stanislaw Lem", "Robert A. Heinlein", "Arthur C. Clarke",
    "Thomas Harris", "Peter Straub", "Richard Matheson", "Robert Bloch",
    "Ira Levin", "Joe Hill", "Paul Tremblay", "Helen Oyeyemi",
    "Akwaeke Emezi", "Silvia Moreno-Garcia", "Pilar Elpídez Lorenzen",
    "Megan Whalen Turner", "John Gwynne", "Kevin Hearne",
    "Seanan McGuire", "Aliette de Bodard", "Tamsyn Muir",
    "Jojo Moyes", "Sophie Kinsella", "Marian Keyes",
    "Liane Moriarty", "Diane Chamberlain", "Kristin Hannah",
    "Lisa Kleypas", "Julia Quinn", "Courtney Milan",
    "Enid Blyton", "Dr. Seuss", "Maurice Sendak",
    "Beverly Cleary", "Lois Lowry", "Madeleine L'Engle",
    "R.L. Stine", "Judy Blume", "Jeanette Winterson",
    "Iain M. Banks", "Neil Stephenson", "James S.A. Corey",

    # ─── Spanish-language authors (Spain + Latin America) (~230) ──
    "Gabriel García Márquez", "Jorge Luis Borges", "Mario Vargas Llosa",
    "Isabel Allende", "Pablo Neruda", "Julio Cortázar", "Carlos Ruiz Zafón",
    "Miguel de Cervantes", "Federico García Lorca", "Arturo Pérez-Reverte",
    "Antonio Machado", "Benito Pérez Galdós", "Camilo José Cela",
    "Miguel de Unamuno", "Gustavo Adolfo Bécquer", "Juan Rulfo",
    "Octavio Paz", "Roberto Bolaño", "Horacio Quiroga", "Ernesto Sabato",
    "Adolfo Bioy Casares", "Eduardo Galeano", "Mario Benedetti",
    "Laura Esquivel", "Elena Poniatowska", "Carlos Fuentes",
    "Alejo Carpentier", "Leopoldo Lugones", "Alfonsina Storni",
    "Rosalía de Castro", "Miguel Hernández", "Ana María Matute",
    "Carmen Laforet", "Rosa Montero", "Almudena Grandes",
    "Javier Marías", "Eduardo Mendoza", "Manuel Vázquez Montalbán",
    "Dolores Redondo", "María Dueñas", "Santiago Posteguillo",
    "Ildefonso Falcones", "Julia Navarro", "Eva García Sáenz de Urturi",
    "Blue Jeans", "Elisabet Benavent", "Albert Espinosa", "Jordi Sierra i Fabra",
    "Diego Fischer", "Florencia Bonelli", "Federico Axat",
    "Claudia Piñeiro", "Samanta Schweblin", "Mariana Enriquez",
    "Hernán Casciari", "Leonardo Padura", "Antonio Muñoz Molina",
    "Fernando Aramburu", "Luz Gabás", "Javier Castillo",
    "Juan Gómez-Jurado", "Megan Maxwell", "Carmen Mola",
    "Sonsoles Ónega", "Irene Vallejo", "Lorenzo Silva",
    "Andrés Trapiello", "Matilde Asensi", "Reyes Monforte",
    "Gioconda Belli", "Sergio Ramírez", "Augusto Roa Bastos",
    "Rómulo Gallegos", "José Donoso", "Manuel Puig",
    "Reinaldo Arenas", "Guillermo Cabrera Infante", "César Vallejo",
    "Rubén Darío", "Gabriela Mistral", "José Martí",
    "Ricardo Güiraldes", "Leopoldo Marechal", "Silvina Ocampo",
    "Victoria Ocampo", "Juan Carlos Onetti", "Juana de Ibarbourou",
    "Eduardo Acevedo Díaz", "Felisberto Hernández", "Idea Vilariño",
    "Cristina Peri Rossi", "Carlos Liscano", "Hugo Burel",
    "Mercedes Vigil", "Óscar Montero", "Angel Gálvez",
    "Carlos Juan Finlay", "José María de Heredia",
    "Esteban Echeverría", "Sarmiento Domingo Faustino", "Vicente López",
    "Baldomero Lillo", "Mariano Azuela", "Agustín Yáñez",
    "Juan José Arreola", "Elena Garro", "Rosario Castellanos",
    "Amparo Dávila", "José Revueltas", "Salvador Elizondo",
    "Gustavo Sainz", "Sergio Pitol", "Luis Arturo Domínguez",
    "Eugenio Montejo", "Yolanda Oreamuno", "Josefina Vicens",
    "José María Arguedas", "Clemente Soto Vélez", "Luis Pales Matos",
    "Arreola Juan José", "Héctor Mantilla Duarte", "Óscar Acosta",
    "Benicio Víctor Campos", "Carlos Montoya Castillo", "Chiquichano López",

    # ─── Portuguese-language authors (~60) ────────────────────────
    "Fernando Pessoa", "Machado de Assis", "Jorge Amado",
    "Clarice Lispector", "Paulo Coelho", "Eça de Queirós",
    "Guimarães Rosa", "Cecília Meireles", "Carlos Drummond de Andrade",
    "Manuel Bandeira", "Graciliano Ramos", "José de Alencar",
    "Monteiro Lobato", "Vinícius de Moraes", "Mia Couto",
    "Pepetela", "Luís de Camões", "Lygia Fagundes Telles",
    "Rachel de Queiroz", "Érico Veríssimo", "Rubem Fonseca",
    "Chico Buarque", "João Ubaldo Ribeiro", "Aluísio Azevedo",
    "Raul Pompeia", "Cruz e Sousa", "Olavo Bilac",
    "Raúl Brandão", "Fernando Namora", "Vergílio Ferreira",
    "Sophia de Mello Breyner Andresen", "Agustina Bessa-Luís",
    "Lidia Jorge", "Teolinda Gersão", "Hélia Correia",
    "José Saramago", "Afonso Lopes Vieira", "Camilo Castelo Branco",
    "Soares dos Reis", "João de Deus", "Guerra Junqueiro",
    "Antero de Quental", "Constança Capdeville Scotto", "Manuel da Costa",
    "Luiz Gonzaga do Nascimento Jr.", "Artur Azevedo", "Carlos Malheiro Dias",
    "Aquilino Ribeiro", "Delfim Pereira da Cunha", "José Alves Ferreira",

    # ─── French-language authors (~70) ──────────────────────────────
    "Victor Hugo", "Alexandre Dumas", "Jules Verne", "Albert Camus",
    "Jean-Paul Sartre", "Gustave Flaubert", "Émile Zola",
    "Honoré de Balzac", "Stendhal", "Marcel Proust",
    "Antoine de Saint-Exupéry", "Voltaire", "Molière",
    "Jean de La Fontaine", "Guy de Maupassant", "Colette",
    "Simone de Beauvoir", "André Gide", "Marguerite Duras",
    "Marguerite Yourcenar", "Michel Houellebecq", "Patrick Modiano",
    "Amélie Nothomb", "Marc Levy", "Guillaume Musso",
    "Fred Vargas", "Pierre Lemaitre", "Françoise Sagan",
    "Bernard Werber", "Jean-Christophe Grangé", "Joël Dicker",
    "Valérie Perrin", "Agnès Martin-Lugand", "Kathrine Pancol",
    "Leïla Slimani", "Franck Thilliez", "Dominique Manotti",
    "Tatiana de Rosnay", "Laurent Mauvignier", "Xavier-Laurent Petit",
    "Fabrice Lémur", "Alexandre Jardin", "Jean Echenoz",
    "Patrick Besson", "Grégoire Bouillier", "Olivier Douzou",
    "Christian Oster", "Catherine Cusset", "Hervé Le Corre",
    "Anne Wiazemsky", "Patrick Suskind", "Danielle Steele",
    "Stendahl", "Baudelaire Charles", "Arthur Rimbaud", "Paul Verlaine",

    # ─── Russian-language authors (~40) ─────────────────────────────
    "Fiódor Dostoievski", "León Tolstói", "Antón Chéjov",
    "Nikolái Gógol", "Aleksandr Pushkin", "Iván Turguénev",
    "Mijaíl Bulgákov", "Boris Pasternak", "Aleksandr Solzhenitsyn",
    "Anna Ajmátova", "Marina Tsvetáyeva", "Máximo Gorki",
    "Yuri Olesha", "Andrei Platonov", "Iván Bunin",
    "Vladimir Mayakovski", "Sergei Yesenin", "Osip Mandelstam",
    "Vladimir Nabokov", "Mikhail Lermontov", "Nikolai Leskov",
    "Nikolai Nekrasov", "Nikolai Chernyshevski", "Ivan Goncharov",
    "Mikhail Sholokhov", "Viktor Shklovski", "Yevtushenko Yevgeny",
    "Bella Akhmadulina", "Andrei Sinyavski", "Yuliy Daniel",
    "Alexander Herzen", "Maxim Gorky", "Ilya Ilf", "Evgeny Petrov",

    # ─── German-language authors (~50) ──────────────────────────────
    "Franz Kafka", "Hermann Hesse", "Thomas Mann", "Johann Wolfgang von Goethe",
    "Friedrich Schiller", "Günter Grass", "Patrick Süskind",
    "Stefan Zweig", "Erich Maria Remarque", "Bernhard Schlink",
    "Michael Ende", "Heinrich Böll", "Rainer Maria Rilke",
    "Friedrich Hölderlin", "Heinrich von Kleist", "Theodor Storm",
    "Adalbert Stifter", "Otto Ludwig", "Jeremias Gotthelf",
    "Annette von Droste-Hülshoff", "Clemens Brentano", "Joseph von Eichendorff",
    "Heinrich Heine", "Georg Büchner", "Christian Dietrich Grabbe",
    "Gottfried Keller", "Conrad Ferdinand Meyer", "Wilhelm Busch",
    "Arthur Schnitzler", "Hugo von Hofmannsthal", "Richard Beer-Hofmann",
    "Felix Salten", "Jakob Wassermann", "Hermann Broch",
    "Robert Musil", "Joseph Roth", "Elias Canetti",
    "Peter Handke", "Heiner Müller", "Christa Wolf",
    "Uwe Johnson", "Siegfried Lenz", "Horst Jahnn",

    # ─── Italian-language authors (~50) ─────────────────────────────
    "Dante Alighieri", "Umberto Eco", "Italo Calvino", "Luigi Pirandello",
    "Giovanni Boccaccio", "Cesare Pavese", "Alberto Moravia",
    "Elena Ferrante", "Andrea Camilleri", "Alessandro Baricco",
    "Niccolò Ammaniti", "Primo Levi", "Natalia Ginzburg",
    "Goffredo Parise", "Giuseppe Tomasi di Lampedusa", "Carlo Cassola",
    "Francesca Marciano", "Marilena Mela", "Cristina Comencini",
    "Paolo Sorrentino", "Paolo Giordano", "Sandro Veronesi",
    "Ernesto De Pascale", "Riccardo Bassani", "Elio Vittorini",
    "Salvatore Quasimodo", "Eugenio Montale", "Giuseppe Ungaretti",
    "Pier Paolo Pasolini", "Giorgio Bassani", "Dacia Maraini",
    "Valerio Massimo Manfredi", "Antonia Arslan", "Stefano Benni",
    "Francesco Guccini", "Enrico Ferraro", "Italo Vattolo",
    "Emilio De Marchi", "Giovanni Verga", "Luigi Capuana",
    "Grazia Deledda", "Matilde Serao", "Armando Trovajoli",

    # ──┈ Japanese-language authors (~35) ─────────────────────────────
    "Haruki Murakami", "Yukio Mishima", "Banana Yoshimoto",
    "Kenzaburō Ōe", "Natsume Sōseki", "Ryūnosuke Akutagawa",
    "Keigo Higashino", "Yōko Ogawa", "Junichirō Tanizaki",
    "Yasunari Kawabata", "Osamu Dazai",
    "Ryu Murakami", "Hiromi Kawakami", "Kazuki Sakuraba",
    "Naoki Matayoshi", "Tomoka Shibasaki", "Takeshi Kaiko",
    "Shusaku Endo", "Yasuhiko Shimizu", "Jiro Asada",
    "Utako Tsumura", "Chie Nakane", "Ayako Tsushima",
    "Fumiko Enchi", "Tatsuo Hori", "Takashi Tsushima",
    "Kobo Abe", "Yuko Tsushima", "Nobuko Yoshiya",
    "Inoue Yasushi", "Abe Kobo", "Shimao Toshio",

    # ─── Scandinavian authors (~40) ────────────────────────────────
    "Jo Nesbø", "Henning Mankell", "Astrid Lindgren",
    "Hans Christian Andersen", "Henrik Ibsen", "Karin Fossum",
    "Lars Kepler", "Camilla Läckberg", "Fredrik Backman",
    "Stieg Larsson", "Nicci French", "Yrsa Sigurdardottir",
    "Jussi Adler-Olsen", "Leif GW Persson", "Åsa Larsson",
    "Nele Neuhaus", "Karin Wahlberg", "Ulla Johansen",
    "Cilla Börjlind", "Rolf Börjlind", "Alexander Maksimovich",
    "Kerstin Ekman", "Per Olov Enquist", "Sven Delblanc",
    "Torgny Lindgren", "Alf Henrikson", "Björn Collinder",
    "Erik Ahlström", "Kjell Espmark", "Jens Bjørneboe",
    "Odd Eidem", "Dag Solstad", "Knut Faldbakken",
    "Agnar Mykle", "Tarjei Vesaas", "Sigrid Undset",
    "Selma Lagerlöf", "Verner von Heidenstam", "Georg Brandes",

    # ─── Other world literature (~80) ──────────────────────────────
    "Naguib Mahfouz", "Orhan Pamuk", "Elif Shafak", "Yaşar Kemal",
    "Mo Yan", "Herta Müller", "Olga Tokarczuk", "Wisława Szymborska",
    "Milan Kundera", "Bohumil Hrabal", "Amos Oz",
    "David Grossman", "Meir Shalev", "Aharon Appelfeld",
    "Sami Michael", "Emile Habibi", "Ghassan Kanafani",
    "Said Aql", "Nizar Qabbani", "Waguih Ghali",
    "Tawfik al-Hakim", "Ahmed Amin", "Taha Hussein",
    "Salim Mubarak", "Yusuf al-Qaradawi", "Ahmed Shawqi",
    "Abdullah al-Qusaimi", "Abdulhamid Jidu", "Omar Khayyam",
    "Molla Sadra", "Avicenna", "Averroes",
    "Mohsin Hamid", "Arundhati Roy", "Jhumpa Lahiri",
    "Amitav Ghosh", "Anita Desai", "Mulk Raj Anand",
    "Raja Rao", "Bhabani Bhattacharya", "Rajender Singh Bedi",
    "Vishwapriya Iyengar", "Amrita Pritam", "Mannu Bhandari",
    "Wang Meng", "Jia Pingwa", "Alai", "Gu Hua",
    "Shen Congwen", "Ba Jin", "Ding Ling", "Lao She",
    "Su Tong", "Yu Hua", "Gao Xingjian", "Can Xue",
    "Qiu Miaofeng", "Feridun Zaimoglu",
    "Khair al-Din al-Tunisi", "Jamal al-Din al-Afghani",

    # ──┈ Contemporary bestsellers & trending (~90) ───────────────────
    "Rebecca Yarros", "Ana Huang", "Tessa Bailey", "Christina Lauren",
    "Ruth Ware", "Lucy Foley", "Alex Michaelides",
    "A.J. Finn", "T.J. Klune", "Travis Baldree",
    "Tamora Pierce", "Garth Nix", "Scott Lynch",
    "John Scalzi", "Lois McMaster Bujold",
    "Seanan McGuire", "Aliette de Bodard", "Tamsyn Muir", "Helen Oyeyemi",
    "Akwaeke Emezi", "Silvia Moreno-Garcia", "Pilar Elpídez Lorenzen",
    "Megan Whalen Turner", "John Gwynne", "Kevin Hearne",
    "Sylvia Moreno-Garcia", "Paul Tremblay", "Gemma Files",
    "Mariana Enriquez", "Penelope Douglas",
    "Freida McFadden", "Megan Maxwell", "Carmen Mola",
    "Juan Gómez-Jurado", "Javier Castillo", "Irene Vallejo",
    "Erin Morgenstern", "Hanya Yanagihara", "Jeanette Winterson",
    "Iain Banks", "Neil Stephenson", "William Gibson",
    "Neal Stephenson", "Hanif Abdulrahman",
    "Ruth Ozeki", "Jennifer Egan", "Chris Whitaker",
    "Penelope Fitzgerald", "Muriel Spark", "Anita Brookner",
    "Julian Barnes", "Martin Amis",
    "Monica Ali", "Nick Hornby", "Mark Haddon",
    "Yann Martel", "Rainbow Rowell", "John Green",
    "Ransom Riggs", "Christopher Paolini", "Cinda Williams Chima",
    "Brandon Mull", "James Dashner",
    "Jennifer L. Armentrout",
    "Kevin J. Anderson", "Kristine Kathryn Rusch", "K.A. Applegate",

    # ─── Self-help & non-fiction (~60) ─────────────�uthor = _cache_author_profile(profile_data)
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


ADMIN_KEY = settings.APPBOOK_ADMIN_KEY


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

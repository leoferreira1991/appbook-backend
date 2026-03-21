"""
Admin endpoint to bulk-populate a user's library from a pre-defined book list.
Triggered via POST with admin key. Skips books already in the library.
"""
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserBookExternal

ADMIN_KEY = 'appbook-admin-2026'

# ═══════════════════════════════════════════════════════════════════════════
# COMPLETE BOOK LIST — parsed from user's reading list
# Format: (title, author, year_or_date, status, category)
#   status: 'read' | 'want_to_read' | 'searching'
#   want_to_read = user owns the book (📚)
#   searching = user wants to buy (🛒)
# ═══════════════════════════════════════════════════════════════════════════

BOOKS = [
    # ═══ 1. Aventura y Ciencia Ficción Clásica ═══════════════════════════

    # ─── Julio Verne ─────────────────────────────────────────────────────
    ("Veinte mil leguas de viaje submarino", "Julio Verne", "1870", "read", "Aventura, Ciencia Ficción"),
    ("Los hijos del Capitán Grant", "Julio Verne", "1868", "read", "Aventura, Ciencia Ficción"),
    ("La Isla Misteriosa", "Julio Verne", "1875", "read", "Aventura, Ciencia Ficción"),
    ("De la Tierra a la Luna", "Julio Verne", "1865", "read", "Aventura, Ciencia Ficción"),
    ("Alrededor de la Luna", "Julio Verne", "1870", "read", "Aventura, Ciencia Ficción"),
    ("La esfinge de los hielos", "Julio Verne", "1897", "read", "Aventura, Ciencia Ficción"),
    ("Cinco semanas en globo", "Julio Verne", "1863", "read", "Aventura, Ciencia Ficción"),
    ("Viaje al centro de la Tierra", "Julio Verne", "1864", "read", "Aventura, Ciencia Ficción"),
    ("La vuelta al mundo en ochenta días", "Julio Verne", "1873", "read", "Aventura, Ciencia Ficción"),
    # Julio Verne — 📚 owned, unread
    ("Robur el Conquistador", "Julio Verne", "1886", "want_to_read", "Aventura, Ciencia Ficción"),
    ("Dueño del Mundo", "Julio Verne", "1904", "want_to_read", "Aventura, Ciencia Ficción"),
    ("Una ciudad flotante", "Julio Verne", "1871", "want_to_read", "Aventura, Ciencia Ficción"),
    ("La jangada: Ochocientas leguas por el Amazonas", "Julio Verne", "1881", "want_to_read", "Aventura, Ciencia Ficción"),
    ("Un capitán de quince años", "Julio Verne", "1878", "want_to_read", "Aventura, Ciencia Ficción"),
    ("Escuela de Robinsones", "Julio Verne", "1882", "want_to_read", "Aventura, Ciencia Ficción"),
    ("Dos años de vacaciones", "Julio Verne", "1888", "want_to_read", "Aventura, Ciencia Ficción"),
    # Julio Verne — 🛒 searching
    ("Las aventuras del Capitán Hatteras", "Julio Verne", "1866", "searching", "Aventura, Ciencia Ficción"),
    ("El Chancellor", "Julio Verne", "1875", "searching", "Aventura, Ciencia Ficción"),
    ("Héctor Servadac", "Julio Verne", "1877", "searching", "Aventura, Ciencia Ficción"),
    ("La casa de vapor", "Julio Verne", "1880", "searching", "Aventura, Ciencia Ficción"),
    ("Miguel Strogoff", "Julio Verne", "1876", "searching", "Aventura, Ciencia Ficción"),
    ("La fortuna de la mujer del rajá", "Julio Verne", "1879", "searching", "Aventura, Ciencia Ficción"),
    ("El castillo de los Cárpatos", "Julio Verne", "1892", "searching", "Aventura, Ciencia Ficción"),
    ("El testamento de un excéntrico", "Julio Verne", "1899", "searching", "Aventura, Ciencia Ficción"),
    ("Matías Sandorf", "Julio Verne", "1885", "searching", "Aventura, Ciencia Ficción"),
    ("Aventuras de tres rusos y tres ingleses en el África Austral", "Julio Verne", "1872", "searching", "Aventura, Ciencia Ficción"),
    ("El país de las pieles", "Julio Verne", "1873", "searching", "Aventura, Ciencia Ficción"),
    ("El rayo verde", "Julio Verne", "1882", "searching", "Aventura, Ciencia Ficción"),
    ("Kerabán el testarudo", "Julio Verne", "1883", "searching", "Aventura, Ciencia Ficción"),
    ("El archipiélago en llamas", "Julio Verne", "1884", "searching", "Aventura, Ciencia Ficción"),
    ("Norte contra Sur", "Julio Verne", "1887", "searching", "Aventura, Ciencia Ficción"),
    ("La compra del Polo Norte", "Julio Verne", "1889", "searching", "Aventura, Ciencia Ficción"),
    ("César Cascabel", "Julio Verne", "1890", "searching", "Aventura, Ciencia Ficción"),
    ("Mistress Branican", "Julio Verne", "1891", "searching", "Aventura, Ciencia Ficción"),
    ("La isla de hélice", "Julio Verne", "1895", "searching", "Aventura, Ciencia Ficción"),
    ("Clovis Dardentor", "Julio Verne", "1896", "searching", "Aventura, Ciencia Ficción"),
    ("El pueblo aéreo", "Julio Verne", "1901", "searching", "Aventura, Ciencia Ficción"),
    ("Los hermanos Kip", "Julio Verne", "1902", "searching", "Aventura, Ciencia Ficción"),
    ("Becas de viaje", "Julio Verne", "1903", "searching", "Aventura, Ciencia Ficción"),
    ("La invasión del mar", "Julio Verne", "1905", "searching", "Aventura, Ciencia Ficción"),

    # ─── H.G. Wells ──────────────────────────────────────────────────────
    ("El hombre invisible", "H.G. Wells", "1897", "read", "Ciencia Ficción"),
    ("La guerra de los mundos", "H.G. Wells", "1898", "read", "Ciencia Ficción"),
    ("La máquina del tiempo", "H.G. Wells", "1895", "read", "Ciencia Ficción"),
    ("La isla del Dr. Moreau", "H.G. Wells", "1896", "want_to_read", "Ciencia Ficción"),
    ("El Alimento de los Dioses", "H.G. Wells", "1904", "want_to_read", "Ciencia Ficción"),
    ("Los primeros hombres en la Luna", "H.G. Wells", "1901", "want_to_read", "Ciencia Ficción"),
    ("Una historia de los tiempos venideros", "H.G. Wells", "1899", "want_to_read", "Ciencia Ficción"),
    ("Doce historias y un sueño", "H.G. Wells", "1903", "want_to_read", "Ciencia Ficción"),

    # ─── Ray Bradbury ────────────────────────────────────────────────────
    ("Fahrenheit 451", "Ray Bradbury", "1953", "read", "Ciencia Ficción"),
    ("Crónicas marcianas", "Ray Bradbury", "1950", "want_to_read", "Ciencia Ficción"),

    # ─── George Orwell ───────────────────────────────────────────────────
    ("1984", "George Orwell", "1949", "read", "Ciencia Ficción, Distopía"),
    ("Rebelión en la granja", "George Orwell", "1945", "read", "Ciencia Ficción, Sátira"),

    # ═══ 2. Misterio y Policial ═══════════════════════════════════════════

    # ─── Agatha Christie — Poirot ────────────────────────────────────────
    ("El misterioso caso de Styles", "Agatha Christie", "1920", "read", "Misterio, Policial"),
    ("El asesinato de Roger Ackroyd", "Agatha Christie", "1926", "read", "Misterio, Policial"),
    ("Peligro inminente", "Agatha Christie", "1932", "read", "Misterio, Policial"),
    ("Asesinato en el Oriente Express", "Agatha Christie", "1934", "read", "Misterio, Policial"),
    ("Muerte en el Nilo", "Agatha Christie", "1937", "read", "Misterio, Policial"),
    ("Maldad bajo el sol", "Agatha Christie", "1941", "read", "Misterio, Policial"),
    ("Los elefantes pueden recordar", "Agatha Christie", "1972", "read", "Misterio, Policial"),
    # Poirot — 📚 owned
    ("Muerte en las nubes", "Agatha Christie", "1935", "want_to_read", "Misterio, Policial"),
    ("El misterio de la guía de ferrocarriles", "Agatha Christie", "1936", "want_to_read", "Misterio, Policial"),
    ("Asesinato en Mesopotamia", "Agatha Christie", "1936", "want_to_read", "Misterio, Policial"),
    ("Cartas sobre la mesa", "Agatha Christie", "1936", "want_to_read", "Misterio, Policial"),
    ("El testigo mudo", "Agatha Christie", "1937", "want_to_read", "Misterio, Policial"),
    ("Cita con la muerte", "Agatha Christie", "1938", "want_to_read", "Misterio, Policial"),
    ("Cinco cerditos", "Agatha Christie", "1942", "want_to_read", "Misterio, Policial"),
    ("La tercera muchacha", "Agatha Christie", "1966", "want_to_read", "Misterio, Policial"),
    ("Telón", "Agatha Christie", "1975", "want_to_read", "Misterio, Policial"),
    # Poirot — 🛒 searching
    ("Asesinato en el campo de Golf", "Agatha Christie", "1923", "searching", "Misterio, Policial"),
    ("Poirot investiga", "Agatha Christie", "1924", "searching", "Misterio, Policial"),
    ("Los cuatro grandes", "Agatha Christie", "1927", "searching", "Misterio, Policial"),
    ("El misterio del tren azul", "Agatha Christie", "1928", "searching", "Misterio, Policial"),
    ("La muerte de Lord Edgware", "Agatha Christie", "1933", "searching", "Misterio, Policial"),
    ("Tragedia en tres actos", "Agatha Christie", "1935", "searching", "Misterio, Policial"),
    ("Navidades trágicas", "Agatha Christie", "1939", "searching", "Misterio, Policial"),
    ("Un triste ciprés", "Agatha Christie", "1940", "searching", "Misterio, Policial"),
    ("La muerte visita al dentista", "Agatha Christie", "1940", "searching", "Misterio, Policial"),
    ("Sangre en la piscina", "Agatha Christie", "1946", "searching", "Misterio, Policial"),
    ("Los trabajos de Hércules", "Agatha Christie", "1947", "searching", "Misterio, Policial"),
    ("Plegarias de la vida", "Agatha Christie", "1948", "searching", "Misterio, Policial"),
    ("Ocho casos de Poirot", "Agatha Christie", "1949", "searching", "Misterio, Policial"),
    ("La señora McGinty ha muerto", "Agatha Christie", "1952", "searching", "Misterio, Policial"),
    ("Después del funeral", "Agatha Christie", "1953", "searching", "Misterio, Policial"),
    ("Asesinato en la calle Hickory", "Agatha Christie", "1955", "searching", "Misterio, Policial"),
    ("El templo de Nasse House", "Agatha Christie", "1956", "searching", "Misterio, Policial"),
    ("Un gato en el palomar", "Agatha Christie", "1959", "searching", "Misterio, Policial"),
    ("Los relojes", "Agatha Christie", "1963", "searching", "Misterio, Policial"),
    ("Los manzanos", "Agatha Christie", "1969", "searching", "Misterio, Policial"),
    ("Los primeros casos de Poirot", "Agatha Christie", "1974", "searching", "Misterio, Policial"),

    # ─── Agatha Christie — Miss Marple ───────────────────────────────────
    ("Muerte en la vicaría", "Agatha Christie", "1930", "read", "Misterio, Policial"),
    ("El tren de las 4:50", "Agatha Christie", "1957", "read", "Misterio, Policial"),
    ("El espejo se rajó de lado a lado", "Agatha Christie", "1962", "read", "Misterio, Policial"),
    ("Un cadáver en la biblioteca", "Agatha Christie", "1942", "want_to_read", "Misterio, Policial"),
    ("El caso de los anónimos", "Agatha Christie", "1943", "want_to_read", "Misterio, Policial"),
    ("Se anuncia un asesinato", "Agatha Christie", "1950", "want_to_read", "Misterio, Policial"),
    ("Némesis", "Agatha Christie", "1971", "want_to_read", "Misterio, Policial"),
    ("Miss Marple y trece problemas", "Agatha Christie", "1932", "searching", "Misterio, Policial"),
    ("El truco de los espejos", "Agatha Christie", "1952", "searching", "Misterio, Policial"),
    ("Un puñado de centeno", "Agatha Christie", "1953", "searching", "Misterio, Policial"),
    ("Misterio en el Caribe", "Agatha Christie", "1964", "searching", "Misterio, Policial"),
    ("En el hotel Bertram", "Agatha Christie", "1965", "searching", "Misterio, Policial"),
    ("Un crimen dormido", "Agatha Christie", "1976", "searching", "Misterio, Policial"),

    # ─── Agatha Christie — Coronel Race ──────────────────────────────────
    ("Cianuro espumoso", "Agatha Christie", "1945", "read", "Misterio, Policial"),
    ("El hombre de traje marrón", "Agatha Christie", "1924", "searching", "Misterio, Policial"),

    # ─── Agatha Christie — Autoconclusivas ───────────────────────────────
    ("Diez negritos", "Agatha Christie", "1939", "read", "Misterio, Policial"),
    ("La casa torcida", "Agatha Christie", "1948", "want_to_read", "Misterio, Policial"),
    ("Hacia cero", "Agatha Christie", "1944", "want_to_read", "Misterio, Policial"),
    ("El misterio de las siete esferas", "Agatha Christie", "1929", "want_to_read", "Misterio, Policial"),
    ("El misterio de Sittaford", "Agatha Christie", "1931", "searching", "Misterio, Policial"),
    ("La trayectoria del bumerán", "Agatha Christie", "1934", "searching", "Misterio, Policial"),
    ("La venganza de Nofret", "Agatha Christie", "1945", "searching", "Misterio, Policial"),
    ("Intriga en Bagdad", "Agatha Christie", "1951", "searching", "Misterio, Policial"),
    ("Destino desconocido", "Agatha Christie", "1955", "searching", "Misterio, Policial"),
    ("Inocencia trágica", "Agatha Christie", "1958", "searching", "Misterio, Policial"),
    ("El misterio de Pale Horse", "Agatha Christie", "1961", "searching", "Misterio, Policial"),
    ("Noche eterna", "Agatha Christie", "1967", "searching", "Misterio, Policial"),
    ("Pasajero a Frankfurt", "Agatha Christie", "1970", "searching", "Misterio, Policial"),

    # ─── Arthur Conan Doyle ──────────────────────────────────────────────
    ("Estudio en Escarlata", "Arthur Conan Doyle", "1887", "read", "Misterio, Policial"),
    ("El Signo de los Cuatro", "Arthur Conan Doyle", "1890", "read", "Misterio, Policial"),
    ("Las Aventuras de Sherlock Holmes", "Arthur Conan Doyle", "1892", "read", "Misterio, Policial"),
    ("Las Memorias de Sherlock Holmes", "Arthur Conan Doyle", "1893", "want_to_read", "Misterio, Policial"),
    ("El Perro de los Baskerville", "Arthur Conan Doyle", "1902", "want_to_read", "Misterio, Policial"),
    ("El Regreso de Sherlock Holmes", "Arthur Conan Doyle", "1905", "want_to_read", "Misterio, Policial"),
    ("Su Último Saludo", "Arthur Conan Doyle", "1917", "want_to_read", "Misterio, Policial"),
    ("El Valle del Miedo", "Arthur Conan Doyle", "1915", "want_to_read", "Misterio, Policial"),

    # ═══ 3. Fantasía Épica ════════════════════════════════════════════════

    # ─── J.R.R. Tolkien ──────────────────────────────────────────────────
    ("El Hobbit", "J.R.R. Tolkien", "1937", "read", "Fantasía"),
    ("La comunidad del anillo", "J.R.R. Tolkien", "1954", "read", "Fantasía"),
    ("Las dos torres", "J.R.R. Tolkien", "1954", "read", "Fantasía"),
    ("El retorno del Rey", "J.R.R. Tolkien", "1955", "read", "Fantasía"),
    ("El Silmarillion", "J.R.R. Tolkien", "1977", "read", "Fantasía"),
    ("Los Hijos de Húrin", "J.R.R. Tolkien", "2007", "want_to_read", "Fantasía"),
    ("Beren y Lúthien", "J.R.R. Tolkien", "2017", "want_to_read", "Fantasía"),
    ("La Caída de Gondolin", "J.R.R. Tolkien", "2018", "want_to_read", "Fantasía"),
    ("La caída de Númenor", "J.R.R. Tolkien", "2022", "want_to_read", "Fantasía"),
    ("Cuentos inconclusos de Númenor y la Tierra Media", "J.R.R. Tolkien", "1980", "want_to_read", "Fantasía"),
    ("La historia de Kullervo", "J.R.R. Tolkien", "2015", "want_to_read", "Fantasía"),
    ("La caída de Arturo", "J.R.R. Tolkien", "2013", "want_to_read", "Fantasía"),
    ("La balada de Aotrou e Itroun", "J.R.R. Tolkien", "2016", "want_to_read", "Fantasía"),
    # David Day — Tolkien analysis
    ("El mundo ilustrado de Tolkien: La Segunda Edad", "David Day", "2020", "want_to_read", "Fantasía, Ensayo"),
    ("Las batallas de Tolkien", "David Day", "2016", "want_to_read", "Fantasía, Ensayo"),
    ("Los héroes de Tolkien", "David Day", "2017", "want_to_read", "Fantasía, Ensayo"),

    # ─── George R.R. Martin ──────────────────────────────────────────────
    ("Fuego y Sangre", "George R.R. Martin", "2018", "read", "Fantasía"),
    ("El caballero de los siete reinos", "George R.R. Martin", "2015", "read", "Fantasía"),
    ("El mundo de hielo y fuego", "George R.R. Martin", "2014", "read", "Fantasía"),
    ("Juego de tronos", "George R.R. Martin", "1996", "want_to_read", "Fantasía"),
    ("Choque de reyes", "George R.R. Martin", "1998", "want_to_read", "Fantasía"),
    ("Tormenta de espadas", "George R.R. Martin", "2000", "want_to_read", "Fantasía"),
    ("Festín de cuervos", "George R.R. Martin", "2005", "want_to_read", "Fantasía"),
    ("Danza de dragones", "George R.R. Martin", "2011", "want_to_read", "Fantasía"),

    # ─── Frank Herbert — Dune ────────────────────────────────────────────
    ("Dune", "Frank Herbert", "1965", "want_to_read", "Ciencia Ficción"),
    ("El mesías de Dune", "Frank Herbert", "1969", "want_to_read", "Ciencia Ficción"),
    ("Hijos de Dune", "Frank Herbert", "1976", "want_to_read", "Ciencia Ficción"),
    ("Dios emperador de Dune", "Frank Herbert", "1981", "searching", "Ciencia Ficción"),
    ("Herejes de Dune", "Frank Herbert", "1984", "searching", "Ciencia Ficción"),
    ("Casa capitular: Dune", "Frank Herbert", "1985", "searching", "Ciencia Ficción"),
    ("Dune: Casa Atreides", "Brian Herbert", "1999", "searching", "Ciencia Ficción"),
    ("Dune: Casa Harkonnen", "Brian Herbert", "2000", "searching", "Ciencia Ficción"),
    ("Dune: Casa Corrino", "Brian Herbert", "2001", "searching", "Ciencia Ficción"),
    ("Dune: La Yihad Butleriana", "Brian Herbert", "2002", "searching", "Ciencia Ficción"),
    ("Dune: La cruzada de las máquinas", "Brian Herbert", "2003", "searching", "Ciencia Ficción"),
    ("Dune: La batalla de Corrin", "Brian Herbert", "2004", "searching", "Ciencia Ficción"),
    ("Cazadores de Dune", "Brian Herbert", "2006", "searching", "Ciencia Ficción"),
    ("Gusanos de arena de Dune", "Brian Herbert", "2007", "searching", "Ciencia Ficción"),
    ("Paul de Dune", "Brian Herbert", "2008", "searching", "Ciencia Ficción"),
    ("Los vientos de Dune", "Brian Herbert", "2009", "searching", "Ciencia Ficción"),
    ("La hermandad de Dune", "Brian Herbert", "2012", "searching", "Ciencia Ficción"),
    ("Mentats de Dune", "Brian Herbert", "2014", "searching", "Ciencia Ficción"),
    ("Navegantes de Dune", "Brian Herbert", "2016", "searching", "Ciencia Ficción"),

    # ─── J.K. Rowling — Harry Potter ─────────────────────────────────────
    ("Harry Potter y la piedra filosofal", "J.K. Rowling", "1997", "want_to_read", "Fantasía, YA"),
    ("Harry Potter y la cámara secreta", "J.K. Rowling", "1998", "want_to_read", "Fantasía, YA"),
    ("Harry Potter y el prisionero de Azkaban", "J.K. Rowling", "1999", "want_to_read", "Fantasía, YA"),
    ("Harry Potter y el cáliz de fuego", "J.K. Rowling", "2000", "want_to_read", "Fantasía, YA"),
    ("Harry Potter y la Orden del Fénix", "J.K. Rowling", "2003", "want_to_read", "Fantasía, YA"),
    ("Harry Potter y el misterio del príncipe", "J.K. Rowling", "2005", "want_to_read", "Fantasía, YA"),
    ("Harry Potter y las reliquias de la muerte", "J.K. Rowling", "2007", "want_to_read", "Fantasía, YA"),

    # ═══ 4. Clásicos Literarios Universales ══════════════════════════════
    ("Ilíada", "Homero", "800 a.C.", "read", "Clásico"),
    ("Odisea", "Homero", "800 a.C.", "read", "Clásico"),
    ("Cien años de soledad", "Gabriel García Márquez", "1967", "read", "Clásico, Realismo Mágico"),
    ("Los Tres Mosqueteros", "Alexandre Dumas", "1844", "read", "Clásico, Aventura"),
    ("Martín Fierro", "José Hernández", "1872", "read", "Clásico, Poesía"),
    ("El Aleph", "Jorge Luis Borges", "1949", "read", "Clásico, Cuentos"),
    ("El viejo y el mar", "Ernest Hemingway", "1952", "read", "Clásico"),
    ("Verdes colinas de África", "Ernest Hemingway", "1935", "read", "Clásico, No Ficción"),
    # Clásicos — 📚 owned
    ("Don Quijote de la Mancha", "Miguel de Cervantes", "1605", "want_to_read", "Clásico"),
    ("La Divina Comedia", "Dante Alighieri", "1321", "want_to_read", "Clásico, Poesía"),
    ("Frankenstein", "Mary Shelley", "1818", "want_to_read", "Clásico, Terror"),
    ("Hamlet", "William Shakespeare", "1603", "want_to_read", "Clásico, Teatro"),
    ("Romeo y Julieta", "William Shakespeare", "1597", "want_to_read", "Clásico, Teatro"),
    ("El Gran Gatsby", "F. Scott Fitzgerald", "1925", "want_to_read", "Clásico"),
    ("Ulises", "James Joyce", "1922", "want_to_read", "Clásico"),
    ("Crónica de una muerte anunciada", "Gabriel García Márquez", "1981", "want_to_read", "Clásico, Realismo Mágico"),
    ("El amor en los tiempos del cólera", "Gabriel García Márquez", "1985", "want_to_read", "Clásico, Realismo Mágico"),
    ("El coronel no tiene quien le escriba", "Gabriel García Márquez", "1958", "want_to_read", "Clásico"),
    ("Las mil y una noches", "Anónimo", "Siglo VIII-XIV", "want_to_read", "Clásico"),
    ("El Conde de Montecristo", "Alexandre Dumas", "1845", "want_to_read", "Clásico, Aventura"),
    ("La dama de las camelias", "Alexandre Dumas (hijo)", "1848", "want_to_read", "Clásico"),
    ("El hombre de la máscara de hierro", "Alexandre Dumas", "1850", "want_to_read", "Clásico, Aventura"),
    ("Robin Hood", "Howard Pyle", "1883", "want_to_read", "Clásico, Aventura"),
    ("El jorobado de Notre Dame", "Victor Hugo", "1831", "want_to_read", "Clásico"),
    ("Crimen y castigo", "Fiódor Dostoyevski", "1866", "want_to_read", "Clásico"),
    ("Cumbres borrascosas", "Emily Brontë", "1847", "want_to_read", "Clásico"),
    ("Cuentos de los Hermanos Grimm", "Jacob y Wilhelm Grimm", "1812", "want_to_read", "Clásico, Cuentos"),
    ("El mago de Oz", "L. Frank Baum", "1900", "want_to_read", "Clásico, Fantasía"),
    ("La insoportable levedad del ser", "Milan Kundera", "1984", "want_to_read", "Clásico"),
    ("El verano peligroso", "Ernest Hemingway", "1960", "want_to_read", "Clásico, No Ficción"),
    ("Muerte en la tarde", "Ernest Hemingway", "1932", "want_to_read", "Clásico, No Ficción"),
    ("Fiesta", "Ernest Hemingway", "1926", "want_to_read", "Clásico"),
    ("Cuentos completos", "Ernest Hemingway", "", "want_to_read", "Clásico, Cuentos"),
    ("Moby Dick", "Herman Melville", "1851", "want_to_read", "Clásico"),
    ("Mujercitas", "Louisa May Alcott", "1868", "want_to_read", "Clásico"),
    ("El retrato de Dorian Gray", "Oscar Wilde", "1890", "want_to_read", "Clásico"),
    ("Oscar Wilde - Narrativa completa", "Oscar Wilde", "", "want_to_read", "Clásico"),
    ("La metamorfosis", "Franz Kafka", "1915", "want_to_read", "Clásico"),
    ("Orgullo y prejuicio", "Jane Austen", "1813", "want_to_read", "Clásico"),
    ("Emma", "Jane Austen", "1815", "want_to_read", "Clásico"),
    ("Persuasión", "Jane Austen", "1817", "want_to_read", "Clásico"),
    ("Alicia en el país de las maravillas", "Lewis Carroll", "1865", "want_to_read", "Clásico, Fantasía"),
    # Clásicos — 🛒 searching
    ("Sentido y sensibilidad", "Jane Austen", "1811", "searching", "Clásico"),
    ("Mansfield Park", "Jane Austen", "1814", "searching", "Clásico"),
    ("Agnes Grey", "Anne Brontë", "1847", "searching", "Clásico"),
    ("Jane Eyre", "Charlotte Brontë", "1847", "searching", "Clásico"),
    ("Una casa en alquiler", "Charles Dickens", "1858", "want_to_read", "Clásico"),
    ("Padre Rico, Padre Pobre", "Robert Kiyosaki", "1997", "read", "No Ficción, Finanzas"),

    # ═══ 5. Ensayos, Filosofía y Reflexión ════════════════════════════════
    ("El arte de la guerra", "Sun Tzu", "", "read", "Filosofía, Estrategia"),
    ("Camino de servidumbre", "Friedrich Hayek", "1944", "read", "Ensayo, Economía"),
    ("Comienza con el porqué", "Simon Sinek", "2009", "read", "No Ficción, Negocios"),
    ("Sálvese quien pueda", "Andrés Oppenheimer", "2017", "read", "No Ficción"),
    ("Multiplicadores", "Liz Wiseman", "2010", "want_to_read", "No Ficción, Negocios"),
    ("De cero a gigante", "Alex Ponce", "2018", "want_to_read", "No Ficción, Negocios"),
    ("El fin de la inflación", "Javier Milei", "2022", "want_to_read", "No Ficción, Economía"),
    ("Cómo salir del pozo", "Andrés Oppenheimer", "2021", "want_to_read", "No Ficción"),

    # ─── Diego Fischer ───────────────────────────────────────────────────
    ("Qué tupé", "Diego Fischer", "2001", "read", "No Ficción"),
    ("Al encuentro de las tres Marías", "Diego Fischer", "2003", "read", "No Ficción"),
    ("Directo al corazón", "Diego Fischer", "2005", "want_to_read", "No Ficción"),
    ("El sentir de las violetas", "Diego Fischer", "2006", "read", "No Ficción"),
    ("Mejor callar", "Diego Fischer", "2008", "read", "No Ficción"),
    ("Qué poco vale la vida", "Diego Fischer", "2010", "read", "No Ficción"),
    ("El precio de una traición", "Diego Fischer", "2011", "read", "No Ficción"),
    ("El robo del siglo", "Diego Fischer", "2013", "read", "No Ficción"),
    ("La gran estafa", "Diego Fischer", "2018", "want_to_read", "No Ficción"),
    ("La bendición de Jonás", "Diego Fischer", "", "want_to_read", "No Ficción"),

    # ═══ 6. Latinoamericana y Cultura Popular ════════════════════════════
    ("Cuentos de la selva", "Horacio Quiroga", "1918", "want_to_read", "Clásico, Cuentos"),
    ("Yo Darwin", "Darwin Desbocatti", "2005", "want_to_read", "Humor, Uruguay"),
    ("No es digno pero es legal", "Darwin Desbocatti", "2012", "want_to_read", "Humor, Uruguay"),
    ("Memorias del olvido", "No Te Va Gustar", "2017", "want_to_read", "Música, Uruguay"),
    ("No + Pálidas", "Varios", "", "want_to_read", "Crónica, Uruguay"),
    ("Yo vi jugar al Chino", "Luzardo y Solana", "2022", "want_to_read", "Deportes, Uruguay"),
    ("El alquimista de la Rambla Wilson", "Mercedes Vigil", "2011", "want_to_read", "Ficción, Uruguay"),
    ("Las venas abiertas de América Latina", "Eduardo Galeano", "1971", "want_to_read", "No Ficción"),
    ("Como agua para chocolate", "Laura Esquivel", "1989", "want_to_read", "Realismo Mágico"),
    ("El presidente ha desaparecido", "Bill Clinton y James Patterson", "2018", "want_to_read", "Thriller"),

    # ═══ Edgar Allan Poe ══════════════════════════════════════════════════
    # Libro 1 — all read ✅
    ("Los asesinatos de la calle Morgue", "Edgar Allan Poe", "1841", "read", "Misterio, Terror"),
    ("El misterio de Marie Rogêt", "Edgar Allan Poe", "1842", "read", "Misterio"),
    ("La carta robada", "Edgar Allan Poe", "1844", "read", "Misterio"),
    ("El escarabajo de oro", "Edgar Allan Poe", "1843", "read", "Misterio"),
    ("¡Tú eres el hombre!", "Edgar Allan Poe", "1845", "read", "Misterio"),
    ("El gato negro", "Edgar Allan Poe", "1843", "read", "Terror"),
    ("El corazón delator", "Edgar Allan Poe", "1843", "read", "Terror"),
    ("El diablillo de la maldad", "Edgar Allan Poe", "1844", "read", "Terror"),
    ("El hombre de la multitud", "Edgar Allan Poe", "1840", "read", "Misterio"),
    ("El barril de amontillado", "Edgar Allan Poe", "1846", "read", "Terror"),
    ("Ligeia", "Edgar Allan Poe", "1838", "read", "Terror"),
    ("Elenora", "Edgar Allan Poe", "1841", "read", "Terror"),
    ("Morella", "Edgar Allan Poe", "1835", "read", "Terror"),
    ("Berenice", "Edgar Allan Poe", "1835", "read", "Terror"),
    ("La conversación de Eiros y Charmion", "Edgar Allan Poe", "1839", "read", "Ciencia Ficción"),
    ("El poder de las palabras", "Edgar Allan Poe", "1845", "read", "Filosofía"),
    ("El coloquio de Monos y Una", "Edgar Allan Poe", "1845", "read", "Filosofía"),
    ("Hop-Frog", "Edgar Allan Poe", "1849", "read", "Terror"),
    ("Metzengerstein", "Edgar Allan Poe", "1832", "read", "Terror"),
    ("Manuscrito encontrado en una botella", "Edgar Allan Poe", "1833", "read", "Aventura, Terror"),
    ("Un descenso al Maelström", "Edgar Allan Poe", "1841", "read", "Aventura, Terror"),
    ("La caja oblonga", "Edgar Allan Poe", "1844", "read", "Misterio"),
    ("Rey Peste", "Edgar Allan Poe", "1842", "read", "Terror"),
    ("La máscara de la Muerte Roja", "Edgar Allan Poe", "1842", "read", "Terror"),
    ("Sombra", "Edgar Allan Poe", "1835", "read", "Terror"),
    ("El entierro prematuro", "Edgar Allan Poe", "1844", "read", "Terror"),
    ("Sin aliento", "Edgar Allan Poe", "1844", "read", "Humor"),
    ("El pozo y el péndulo", "Edgar Allan Poe", "1842", "read", "Terror"),
    ("La caída de la Casa Usher", "Edgar Allan Poe", "1839", "read", "Terror"),
    ("La narración de Arthur Gordon Pym", "Edgar Allan Poe", "1838", "read", "Aventura, Terror"),
    # Poe Libro 2 — all want_to_read 📚
    ("Una mañana en el Wissahickon", "Edgar Allan Poe", "1844", "want_to_read", "Relato"),
    ("Una historia de Jerusalén", "Edgar Allan Poe", "1836", "want_to_read", "Relato"),
    ("Tres domingos en una semana", "Edgar Allan Poe", "1841", "want_to_read", "Relato"),
    ("El sistema del doctor Alquitrán y el profesor Pluma", "Edgar Allan Poe", "1845", "want_to_read", "Relato"),
    ("El duque de l'Omelette", "Edgar Allan Poe", "1832", "want_to_read", "Relato"),
    ("Las memorias de Thingum Bob", "Edgar Allan Poe", "1844", "want_to_read", "Relato"),
    ("Cómo escribir un artículo para la revista Blackwood", "Edgar Allan Poe", "1838", "want_to_read", "Relato"),
    ("El milésimo segundo cuento de Scherezada", "Edgar Allan Poe", "1845", "want_to_read", "Relato"),
    ("Los hechos en el caso del señor Valdemar", "Edgar Allan Poe", "1845", "want_to_read", "Terror"),
    ("Revelación mesmérica", "Edgar Allan Poe", "1844", "want_to_read", "Ciencia Ficción"),
    ("Von Kempelen y su descubrimiento", "Edgar Allan Poe", "1849", "want_to_read", "Relato"),
    ("Algunas palabras con una momia", "Edgar Allan Poe", "1845", "want_to_read", "Humor"),
    ("La aventura incomparable de un tal Hans Pfaall", "Edgar Allan Poe", "1835", "want_to_read", "Ciencia Ficción"),
    # Poe Libro 3 — Poesía — all want_to_read 📚
    ("El cuervo", "Edgar Allan Poe", "1845", "want_to_read", "Poesía"),
    ("Annabel Lee", "Edgar Allan Poe", "1849", "want_to_read", "Poesía"),
    ("Lenore", "Edgar Allan Poe", "1843", "want_to_read", "Poesía"),
    ("Ulalume", "Edgar Allan Poe", "1847", "want_to_read", "Poesía"),
    ("A Helena", "Edgar Allan Poe", "1831", "want_to_read", "Poesía"),

    # ═══ Clásicos Universales adicionales ═════════════════════════════════
    # (included above with the clásicos section)

    # ═══ 7. Literatura Médica y Suspenso ══════════════════════════════════
    ("Turno de noche", "Robin Cook", "2022", "want_to_read", "Thriller, Medicina"),
    ("Pandemia", "Robin Cook", "2018", "want_to_read", "Thriller, Medicina"),
    ("Virus mortal", "Robin Cook", "1987", "want_to_read", "Thriller, Medicina"),
    ("Anestesia letal", "Robin Cook", "1990", "want_to_read", "Thriller, Medicina"),
    ("Impostores", "Robin Cook", "2017", "want_to_read", "Thriller, Medicina"),
    ("La cura", "Robin Cook", "2010", "want_to_read", "Thriller, Medicina"),
    ("Invasión", "Robin Cook", "1997", "want_to_read", "Thriller, Medicina"),
    ("Crisis", "Robin Cook", "2006", "want_to_read", "Thriller, Medicina"),
]


class BulkLibraryImportView(APIView):
    """Admin endpoint to bulk-populate a user's library."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            key = request.query_params.get('key', '')
            if key != ADMIN_KEY:
                return Response({'error': 'Forbidden'}, status=403)

            username = request.data.get('username', 'cr.leonardo.ferreira')
            dry_run = request.data.get('dry_run', False)

            try:
                User = get_user_model()
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'error': f'User "{username}" not found'}, status=404)

            # Get existing books (by title, case-insensitive)
            existing = set()
            for book in UserBookExternal.objects.filter(user=user):
                existing.add(book.title.lower().strip())

            added = []
            skipped = []
            errors = []

            for title, author, pub_date, book_status, categories in BOOKS:
                title_clean = title.strip()
                if title_clean.lower() in existing:
                    skipped.append(title_clean)
                    continue

                if dry_run:
                    added.append(f"[DRY] {title_clean} ({author}) [{book_status}]")
                    continue

                try:
                    obj = UserBookExternal.objects.create(
                        user=user,
                        title=title_clean,
                        author=author,
                        publish_date=pub_date,
                        status=book_status,
                        categories=categories,
                    )
                    added.append(f"{title_clean} ({author}) [{book_status}] id={obj.id}")
                    existing.add(title_clean.lower())
                except Exception as e:
                    errors.append(f"{title_clean}: {str(e)}")

            return Response({
                'user': username,
                'total_in_list': len(BOOKS),
                'added': len(added),
                'skipped': len(skipped),
                'errors': len(errors),
                'added_detail': added[:50],
                'skipped_detail': skipped[:20],
                'error_detail': errors,
            })
        except Exception as e:
            import traceback
            return Response({'error': str(e), 'trace': traceback.format_exc()}, status=500)

    def get(self, request):
        """Preview: show what would be imported."""
        try:
            key = request.query_params.get('key', '')
            if key != ADMIN_KEY:
                return Response({'error': 'Forbidden'}, status=403)

            username = request.query_params.get('username', 'cr.leonardo.ferreira')
            try:
                User = get_user_model()
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'error': f'User "{username}" not found'}, status=404)

            existing = set()
            for book in UserBookExternal.objects.filter(user=user):
                existing.add(book.title.lower().strip())

            to_add = []
            already = []
            for title, author, pub_date, book_status, categories in BOOKS:
                entry = {'title': title, 'author': author, 'status': book_status, 'year': pub_date}
                if title.lower().strip() in existing:
                    already.append(entry)
                else:
                    to_add.append(entry)

            counts = {'read': 0, 'want_to_read': 0, 'searching': 0}
            for b in BOOKS:
                counts[b[3]] = counts.get(b[3], 0) + 1

            return Response({
                'total_in_list': len(BOOKS),
                'already_in_library': len(already),
                'to_add': len(to_add),
                'breakdown': counts,
                'preview_to_add': to_add[:30],
            })
        except Exception as e:
            import traceback
            return Response({'error': str(e), 'trace': traceback.format_exc()}, status=500)


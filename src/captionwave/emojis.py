"""
Asignación palabra -> emoji.

Importante: solo se usan emojis cuya **versión de Unicode** es lo bastante
antigua como para estar presente en iOS. Esto evita "tofus" (cuadritos) en
iPhone. El umbral se controla con `max_version` (por defecto 15.0, que cubre
ampliamente las versiones recientes de iOS).

Nota sobre la APARIENCIA "estilo Apple": este módulo entrega el CARÁCTER de
emoji correcto (un punto de código Unicode), no la imagen de Apple. La imagen
con la que se ve un emoji la pone el sistema/fuente donde se renderice:
  - En un iPhone/Mac se verá con el diseño de Apple automáticamente.
  - En Linux (p. ej. un servidor) se verá con Noto/Twemoji.
La librería NO incluye ni descarga el arte propietario de Apple. Si necesitas
el diseño exacto de Apple en el video, superpón tus propias imágenes usando los
tiempos del emoji que entrega `generate(...)` (campo `emojis`).
"""

from __future__ import annotations
import unicodedata
import functools

import emoji as _emoji_lib


# Palabras que NO deben disparar la búsqueda de emoji.
_STOP = {
    "de", "del", "la", "el", "los", "las", "con", "y", "o", "un", "una", "para",
    "por", "en", "a", "al", "que", "se", "su", "sus", "sin", "sobre", "tipo",
    "como", "este", "esta", "ese", "esa", "es", "son", "tiene", "tienen", "fue",
    "ser", "han", "hay", "muy", "mas", "menos", "todo", "toda", "todos", "mismo",
    "cada", "entre", "hasta", "cuando", "donde", "porque", "mucho", "mucha",
    "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
    "diez", "cien", "mil", "veces", "vez", "casi", "tan", "tanto", "cerca",
}

# Diccionario curado palabra -> emoji. Solo emojis muy difundidos (un único
# punto de código, salvo el selector de variación FE0F) para que se rendericen
# bien y exista su PNG en Twemoji al superponerlos en el video (sin cuadritos).
CURADOS = {
    # --- Espacio y astronomía ---
    "estrella": "⭐", "estrellas": "⭐", "estelar": "⭐",
    "galaxia": "🌌", "universo": "🌌", "cosmos": "🌌", "nebulosa": "🌌",
    "tierra": "🌍", "mundo": "🌍", "planeta": "🪐", "planetas": "🪐", "orbita": "🪐",
    "sol": "☀️", "solar": "☀️", "luna": "🌙", "lunar": "🌙", "eclipse": "🌑",
    "cohete": "🚀", "nave": "🚀", "astronauta": "🚀", "espacio": "🚀", "satelite": "🛰️",
    "telescopio": "🔭", "astronomia": "🔭",
    "cometa": "☄️", "meteorito": "☄️", "asteroide": "☄️", "meteoro": "☄️",

    # --- Ciencia, física y química ---
    "ciencia": "🔬", "cientifico": "🔬", "experimento": "🔬", "microscopio": "🔬",
    "laboratorio": "🔬", "quimica": "🧪", "reaccion": "🧪", "formula": "🧪", "elemento": "🧪",
    "molecula": "⚛️", "atomo": "⚛️", "particula": "⚛️", "neutron": "⚛️", "proton": "⚛️",
    "electron": "⚛️", "nuclear": "☢️", "radiacion": "☢️", "radiactivo": "☢️",
    "energia": "⚡", "electricidad": "⚡", "rayo": "⚡", "rayos": "⚡", "voltaje": "⚡",
    "iman": "🧲", "magnetico": "🧲", "magnetismo": "🧲", "gravedad": "🌐",
    "luz": "💡", "brillo": "💡", "idea": "💡", "ilumina": "💡", "bombilla": "💡",
    "explosion": "💥", "estalla": "💥", "impacto": "💥", "choque": "💥", "bomba": "💣",
    "matematica": "🔢", "numero": "🔢", "numeros": "🔢", "cifra": "🔢", "calculo": "🧮",

    # --- Cuerpo humano y salud ---
    "cerebro": "🧠", "mente": "🧠", "neurona": "🧠", "memoria": "🧠", "pensamiento": "🧠",
    "corazon": "❤️", "latido": "❤️", "pulso": "❤️", "amor": "❤️",
    "sangre": "🩸", "hueso": "🦴", "huesos": "🦴", "esqueleto": "💀", "craneo": "💀",
    "ojo": "👀", "ojos": "👀", "vista": "👀", "mirada": "👀",
    "oido": "👂", "oreja": "👂", "nariz": "👃", "olfato": "👃",
    "boca": "👄", "diente": "🦷", "dientes": "🦷", "lengua": "👅",
    "mano": "✋", "manos": "✋", "dedo": "👆", "pie": "🦶", "pierna": "🦵", "brazo": "💪",
    "musculo": "💪", "fuerza": "💪", "pulmon": "🫁", "pulmones": "🫁", "oxigeno": "🫁",
    "salud": "🩺", "medico": "🩺", "doctor": "🩺", "medicina": "💊", "pastilla": "💊",
    "vacuna": "💉", "inyeccion": "💉", "aguja": "💉",
    "adn": "🧬", "gen": "🧬", "genetica": "🧬", "celula": "🦠", "celulas": "🦠",
    "virus": "🦠", "bacteria": "🦠", "microbio": "🦠", "germen": "🦠",

    # --- Naturaleza, clima y geografía ---
    "agua": "💧", "gota": "💧", "liquido": "💧", "lluvia": "🌧️", "tormenta": "⛈️",
    "oceano": "🌊", "mar": "🌊", "ola": "🌊", "olas": "🌊", "marea": "🌊",
    "rio": "🏞️", "lago": "🏞️", "cascada": "🏞️", "montaña": "⛰️", "montañas": "⛰️",
    "volcan": "🌋", "lava": "🌋", "erupcion": "🌋", "terremoto": "🌋", "sismo": "🌋",
    "fuego": "🔥", "llama": "🔥", "calor": "🔥", "caliente": "🔥", "incendio": "🔥",
    "frio": "❄️", "nieve": "❄️", "congelado": "❄️", "hielo": "🧊", "glaciar": "🧊",
    "viento": "💨", "aire": "💨", "gas": "💨", "huracan": "🌀", "tornado": "🌀",
    "nube": "☁️", "nubes": "☁️", "niebla": "🌫️", "arcoiris": "🌈", "temperatura": "🌡️",
    "arbol": "🌳", "arboles": "🌳", "bosque": "🌳", "selva": "🌳", "madera": "🪵",
    "planta": "🌱", "semilla": "🌱", "hoja": "🍃", "flor": "🌸", "flores": "🌸",
    "desierto": "🏜️", "arena": "🏜️", "isla": "🏝️", "playa": "🏖️",

    # --- Animales ---
    "animal": "🐾", "animales": "🐾", "perro": "🐶", "gato": "🐱", "leon": "🦁",
    "tigre": "🐯", "oso": "🐻", "lobo": "🐺", "zorro": "🦊", "conejo": "🐰",
    "raton": "🐭", "caballo": "🐴", "vaca": "🐮", "cerdo": "🐷", "mono": "🐵",
    "elefante": "🐘", "jirafa": "🦒", "cebra": "🦓", "rinoceronte": "🦏",
    "pajaro": "🐦", "aguila": "🦅", "buho": "🦉", "pinguino": "🐧", "loro": "🦜",
    "pez": "🐟", "peces": "🐟", "tiburon": "🦈", "ballena": "🐳", "delfin": "🐬",
    "pulpo": "🐙", "cangrejo": "🦀", "tortuga": "🐢", "serpiente": "🐍", "cocodrilo": "🐊",
    "rana": "🐸", "araña": "🕷️", "abeja": "🐝", "mariposa": "🦋", "hormiga": "🐜",
    "insecto": "🐛", "gusano": "🐛", "dinosaurio": "🦕", "dinosaurios": "🦕", "fosil": "🦴",

    # --- Comida y bebida ---
    "comida": "🍔", "comer": "🍴", "hambre": "🍴", "fruta": "🍎", "manzana": "🍎",
    "platano": "🍌", "naranja": "🍊", "uva": "🍇", "fresa": "🍓", "limon": "🍋",
    "pan": "🍞", "queso": "🧀", "huevo": "🥚", "carne": "🍖", "pollo": "🍗",
    "pizza": "🍕", "cafe": "☕", "leche": "🥛", "azucar": "🍬", "miel": "🍯",
    "chocolate": "🍫", "pastel": "🍰", "bebida": "🥤",

    # --- Tecnología e internet ---
    "computadora": "💻", "ordenador": "💻", "laptop": "💻", "pantalla": "🖥️", "monitor": "🖥️",
    "telefono": "📱", "celular": "📱", "movil": "📱", "smartphone": "📱",
    "internet": "🌐", "web": "🌐", "red": "🌐", "online": "🌐", "wifi": "📶", "señal": "📶",
    "robot": "🤖", "inteligencia": "🤖", "algoritmo": "🤖", "codigo": "💻", "programa": "💻",
    "dato": "💾", "datos": "💾", "archivo": "📁", "disco": "💿",
    "camara": "📷", "foto": "📷", "video": "🎥", "pelicula": "🎬", "television": "📺",
    "bateria": "🔋", "carga": "🔋", "enchufe": "🔌", "cable": "🔌",

    # --- Dinero, trabajo y economía ---
    "dinero": "💰", "moneda": "🪙", "monedas": "🪙", "oro": "🪙", "plata": "🪙",
    "billete": "💵", "dolar": "💵", "euro": "💶", "banco": "🏦", "pago": "💳",
    "tarjeta": "💳", "precio": "🏷️", "compra": "🛒", "tienda": "🏪", "negocio": "💼",
    "trabajo": "💼", "empresa": "🏢", "fabrica": "🏭", "grafico": "📈", "crecimiento": "📈",
    "diamante": "💎", "cristal": "💎", "joya": "💎", "tesoro": "💰", "riqueza": "💰",

    # --- Tiempo, lugares y transporte ---
    "tiempo": "⏳", "reloj": "⏰", "hora": "⏰", "minuto": "⏱️", "segundo": "⏱️",
    "año": "📅", "años": "📅", "mes": "📅", "dia": "🌞", "noche": "🌙", "siglo": "📅",
    "casa": "🏠", "hogar": "🏠", "edificio": "🏢", "ciudad": "🏙️", "puente": "🌉",
    "castillo": "🏰", "templo": "🏛️", "iglesia": "⛪", "mapa": "🗺️", "ubicacion": "📍",
    "viaje": "✈️", "avion": "✈️", "vuelo": "✈️", "coche": "🚗", "carro": "🚗", "auto": "🚗",
    "tren": "🚆", "barco": "🚢", "bicicleta": "🚲", "moto": "🏍️", "camion": "🚚",

    # --- Personas, emociones e ideas ---
    "persona": "🧑", "gente": "👥", "humano": "🧑", "familia": "👪", "bebe": "👶",
    "rey": "👑", "reina": "👑", "corona": "👑", "feliz": "😀", "alegria": "😀",
    "risa": "😂", "triste": "😢", "llanto": "😢", "miedo": "😱", "sorpresa": "😮",
    "enojo": "😡", "beso": "💋", "sueño": "💤", "dormir": "💤",
    "pensar": "🤔", "duda": "🤔", "secreto": "🤫", "silencio": "🤫", "genio": "🧞",

    # --- Acciones y conceptos varios ---
    "musica": "🎵", "cancion": "🎵", "sonido": "🔊", "ruido": "🔊", "voz": "🗣️", "hablar": "🗣️",
    "libro": "📚", "leer": "📖", "lectura": "📖", "estudio": "📚", "escuela": "🏫",
    "arte": "🎨", "pintura": "🎨", "color": "🎨", "deporte": "⚽", "futbol": "⚽",
    "juego": "🎮", "ganar": "🏆", "premio": "🏆", "campeon": "🏆",
    "guerra": "⚔️", "batalla": "⚔️", "arma": "⚔️", "escudo": "🛡️", "proteccion": "🛡️",
    "llave": "🔑", "candado": "🔒", "seguridad": "🔒", "peligro": "⚠️", "alerta": "⚠️",
    "prohibido": "🚫", "correcto": "✅", "error": "❌", "muerte": "💀", "fantasma": "👻",
    "magia": "✨", "magico": "✨", "regalo": "🎁", "fiesta": "🎉", "celebracion": "🎉",
    "globo": "🎈", "bandera": "🚩", "objetivo": "🎯", "meta": "🎯", "diana": "🎯",
    "velocidad": "⚡", "veloz": "⚡", "rapido": "⚡",
}

# Emojis de respaldo cuando no se encuentra nada relevante.
DEFAULTS = ["✨", "🤯", "💫", "👀", "🔥"]


def _norm(w: str) -> str:
    """minúsculas, sin acentos (conservando ñ), solo letras."""
    w = w.lower().replace("ñ", "\x00")
    w = "".join(c for c in unicodedata.normalize("NFKD", w) if not unicodedata.combining(c))
    w = w.replace("\x00", "ñ")
    return "".join(c for c in w if c.isalpha())


def _es_bandera(ch: str) -> bool:
    return any(0x1F1E6 <= ord(c) <= 0x1F1FF or c == "\U0001F3F4" for c in ch)


@functools.lru_cache(maxsize=8)
def _build_index(max_version: float):
    """Construye {palabra_norm: emoji} desde la librería emoji.

    Filtra por versión (compatibilidad iOS), descarta banderas y se queda con
    el nombre más específico para cada palabra.
    """
    idx: dict[str, tuple[str, int]] = {}
    try:
        _emoji_lib.config.load_language("es")
    except Exception:
        pass
    for ch, d in _emoji_lib.EMOJI_DATA.items():
        if d.get("status") != _emoji_lib.STATUS["fully_qualified"]:
            continue
        ver = d.get("E")
        if not isinstance(ver, (int, float)) or ver > max_version:
            continue
        if _es_bandera(ch):
            continue
        nombre = d.get("es") or d.get("en")
        if not nombre:
            continue
        tokens = nombre.strip(":").split("_")
        ntok = len(tokens)
        for t in tokens:
            k = _norm(t)
            if len(k) < 3 or k in _STOP:
                continue
            if k not in idx or ntok < idx[k][1]:
                idx[k] = (ch, ntok)
    return idx


class EmojiPicker:
    """Selecciona emojis para palabras y frases, limitado a iOS."""

    def __init__(self, max_version: float = 15.0):
        self.max_version = max_version
        self._idx = _build_index(max_version)

    def for_word(self, palabra: str):
        """Devuelve un emoji para una sola palabra, o None si no aplica."""
        k = _norm(palabra)
        if not k or k in _STOP:
            return None
        if k in CURADOS:
            return CURADOS[k]
        # plurales sencillos
        for suf in ("es", "s"):
            base = k[:-len(suf)]
            if k.endswith(suf) and len(base) >= 3 and base in CURADOS:
                return CURADOS[base]
        if k in self._idx:
            return self._idx[k][0]
        for suf in ("es", "s"):
            base = k[:-len(suf)]
            if k.endswith(suf) and len(base) >= 3 and base in self._idx:
                return self._idx[base][0]
        return None

    def for_phrase(self, frase: str, fallback_idx: int = 0):
        """Mejor emoji para una frase (busca en sus palabras, de larga a corta)."""
        for w in sorted(frase.split(), key=len, reverse=True):
            e = self.for_word(w)
            if e:
                return e
        return DEFAULTS[fallback_idx % len(DEFAULTS)]

    def is_ios_safe(self, ch: str) -> bool:
        """True si el emoji está dentro de la versión permitida (iOS)."""
        d = _emoji_lib.EMOJI_DATA.get(ch)
        if not d:
            return False
        ver = d.get("E")
        return isinstance(ver, (int, float)) and ver <= self.max_version


@functools.lru_cache(maxsize=4)
def _default_picker(max_version: float = 15.0) -> EmojiPicker:
    return EmojiPicker(max_version)


def emoji_for_word(word: str, max_version: float = 15.0):
    """Devuelve el emoji asignado a una palabra, o ``None`` si no hay uno claro.

    Combina el diccionario curado :data:`CURADOS` (cientos de palabras en
    español) con el índice de la librería ``emoji`` filtrado por versión de
    Unicode, para evitar "cuadritos". Pensado para usarse directamente::

        from captionwave import emoji_for_word
        emoji_for_word("estrella")   # -> "⭐"
        emoji_for_word("planeta")    # -> "🪐"
    """
    return _default_picker(max_version).for_word(word)

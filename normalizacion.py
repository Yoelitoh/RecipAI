import csv
import re
import unicodedata
from pathlib import Path

CARPETA = Path(__file__).resolve().parent

FRACCIONES = "½⅓⅔¼¾⅛⅜⅝⅞"
RE_NUMERO = re.compile(r"^[\d%s][\d%s.,/\-–]*$" % (FRACCIONES, FRACCIONES))

UNIDADES = {
    "taza", "tazas", "cucharada", "cucharadas", "cucharadita", "cucharaditas",
    "cda", "cdas", "cdta", "cdtas", "tbsp", "tsp", "c",
    "sopera", "soperas", "cafetera", "cafeteras", "tetera", "teteras",
    "rasa", "colmada", "g", "gr", "grs", "gramo", "gramos", "kg", "kilo",
    "kilos", "kilogramo", "kilogramos", "ml", "mililitro", "mililitros", "l",
    "litro", "litros", "lb", "libra", "libras", "oz", "onza", "onzas",
    "lata", "latas", "paquete", "paquetes", "pkg", "caja", "cajas", "bolsa",
    "bolsas", "frasco", "frascos", "botella", "botellas", "vaso", "vasos",
    "copa", "copas", "pizca", "pizcas", "diente", "dientes", "hoja", "hojas",
    "rama", "ramas", "ramita", "ramitas", "ramo", "manojo", "manojos",
    "tallo", "tallos", "vara", "varas", "varita", "varitas", "rebanada",
    "rebanadas", "rodaja", "rodajas", "loncha", "lonchas", "lonja", "lonjas",
    "trozo", "trozos", "pedazo", "pedazos", "pieza", "piezas", "cubo",
    "cubos", "cubito", "cubitos", "cabeza", "cabezas", "puñado", "puñados",
    "chorro", "chorrito", "gota", "gotas", "sobre", "sobres", "barra",
    "barras", "tableta", "tabletas", "tablilla", "tablillas", "pulgada",
    "palito", "palitos", "raja", "rajas", "filete", "filetes", "vaina",
    "vainas", "grano", "granos", "tira", "tiras", "porcion", "porciones",
    "cono", "conos", "bola", "bolas", "gajo", "gajos", "cuarto", "atado",
    "tapa", "tapas",
}

RELLENO = {
    "aprox", "aproximadamente", "alrededor", "cerca", "unos", "unas", "un",
    "una", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
    "nueve", "diez", "once", "doce", "docena", "media", "medio", "mitad",
    "de", "del", "la", "el", "los", "las", "y", "o", "al", "poco", "poca",
    "pocas", "pocos", "algunas", "algunos", "varias", "varios", "como",
    "casi", "grande", "grandes", "mediano", "mediana", "medianos",
    "medianas", "pequeno", "pequena", "pequenos", "pequenas", "chico",
    "chica", "chicos", "chicas", "extra", "bien", "buen", "buena",
}

CORTE = {
    "cortado", "cortada", "cortados", "cortadas", "picado", "picada",
    "picados", "picadas", "pelado", "pelada", "pelados", "peladas",
    "rallado", "rallada", "rallados", "ralladas", "cocido", "cocida",
    "cocidos", "cocidas", "asado", "asada", "asados", "asadas", "molido",
    "molida", "molidos", "molidas", "finamente", "partido", "partida",
    "partidos", "partidas", "troceado", "troceada", "troceados",
    "troceadas", "rebanado", "rebanada", "rebanados", "rebanadas",
    "desmenuzado", "desmenuzada", "desmenuzados", "desmenuzadas",
    "lavado", "lavada", "lavados", "lavadas", "escurrido", "escurrida",
    "escurridos", "escurridas", "drenado", "drenada", "limpio", "limpia",
    "limpios", "limpias", "tostado", "tostada", "tostados", "tostadas",
    "en", "para", "sin", "con", "que", "si", "u", "o", "gusto", "opcional",
    "opcionales", "aprox", "aproximadamente", "ver", "nota", "segun",
    "cada", "mas", "menos", "por", "picadito", "picadita", "picaditos",
    "picaditas", "finito", "finita", "finitos", "finitas", "separando",
    "suficiente", "bien", "entero", "entera", "enteros", "enteras",
    "fresco", "fresca", "frescos", "frescas", "maduro", "madura", "maduros",
    "maduras", "seco", "seca", "secos", "secas",
}

PREFIJOS_DE = {
    "jugo", "zumo", "ralladura", "cascara", "pulpa", "yema", "yemas", "clara",
    "claras",
}

IGNORAR_PALABRA = {"pero", "aunque", "nota", "notas", "opcional", "opcionales", "ver", "si"}

SINGULARES_FIJOS = {"res", "anis", "cuscus", "mas", "gas", "tres", "pan"}

UTENSILIOS = {
    "cuchillo", "palillo", "palillos", "papel", "plastico", "olla", "sarten",
    "charola", "molde", "licuadora", "procesador", "aluminio", "servilleta",
    "toalla", "brocheta", "brochetas", "vidrio", "bandeja", "cacerola",
    "tazon", "recipiente", "comal", "batidora", "colador", "rosticero",
    "cuchara", "tenedor", "horno", "tapa", "pinza", "pinzas", "espatula",
}

BASICOS = {"sal", "pimienta", "agua", "aceite"}

REPARACIONES = [
    (re.compile(r"\bto (?=(?:rtilla|mate|matillo|stada|stado))", re.I), "to"),
]


def sin_acentos(texto):
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def clave(texto):
    return sin_acentos(texto).lower().strip()


def _leer_csv_sinonimos():
    ruta = CARPETA / "sinonimos.csv"
    sinonimos = {}
    if ruta.exists():
        with ruta.open(encoding="utf-8", newline="") as f:
            for fila in csv.reader(f):
                if len(fila) >= 2 and not fila[0].startswith("#"):
                    sinonimos[clave(fila[0])] = fila[1].strip().lower()
    return sinonimos


def _leer_compuestos():
    ruta = CARPETA / "compuestos.txt"
    compuestos = []
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip().lower()
            if linea and not linea.startswith("#"):
                compuestos.append(linea)
    return sorted(compuestos, key=len, reverse=True)


SINONIMOS = _leer_csv_sinonimos()
COMPUESTOS = _leer_compuestos()
COMPUESTOS_CLAVE = [(clave(c), c) for c in COMPUESTOS]

def limpiar_texto(texto):
    texto = texto.replace("\u200b", "").replace("\xa0", " ")
    for patron, reemplazo in REPARACIONES:
        texto = patron.sub(reemplazo, texto)
    texto = re.sub(r"\([^)]*\)", " ", texto)
    texto = re.sub(r"(?<=\d),(?=\d)", ".", texto)
    texto = texto.replace("*", " ").replace("/", " ")
    return re.sub(r"\s+", " ", texto).strip()


def dividir_ingredientes(texto):
    texto = re.sub(r"(?<=\d),(?=\d)", ".", texto)
    partes, nivel, actual = [], 0, []
    for car in texto:
        if car == "(":
            nivel += 1
        elif car == ")":
            nivel = max(0, nivel - 1)
        if car == "," and nivel == 0:
            partes.append("".join(actual))
            actual = []
        else:
            actual.append(car)
    partes.append("".join(actual))
    return [p.strip() for p in partes if p.strip()]


def _token_limpio(token):
    return clave(token).strip(".,;:()\"'")


def quitar_cantidad(tokens):
    tokens = list(tokens)
    while tokens:
        t = _token_limpio(tokens[0])
        if not t or RE_NUMERO.match(t) or t in UNIDADES or t in RELLENO:
            tokens.pop(0)
        else:
            break
    return tokens


def cortar_preparacion(tokens):
    resultado = []
    for token in tokens:
        if _token_limpio(token) in CORTE:
            break
        resultado.append(token)
    return resultado


def quitar_prefijos(tokens):
    tokens = list(tokens)
    while len(tokens) >= 3 and _token_limpio(tokens[0]) in PREFIJOS_DE and _token_limpio(tokens[1]) in ("de", "del"):
        tokens = tokens[2:]
    return tokens


def _compuesto(tokens):
    frase = clave(" ".join(tokens))
    for compuesto_clave, compuesto in COMPUESTOS_CLAVE:
        if frase == compuesto_clave or frase.startswith(compuesto_clave + " "):
            return compuesto
    return None


def _palabra_principal(tokens):
    for token in tokens:
        palabra = re.sub(r"[^\wñáéíóúü]", "", token.lower())
        if palabra and not palabra.isdigit():
            return palabra
    return None


def analizar_linea(linea):
    texto = limpiar_texto(linea)
    if not texto or texto.endswith(":") or clave(texto).startswith("para "):
        return "ignorar", []
    tokens = quitar_prefijos(quitar_cantidad(texto.split()))
    if not tokens:
        return "fallo", []
    comp = _compuesto(tokens)
    if comp:
        return "ok", [comp]
    tokens = cortar_preparacion(tokens)
    if not tokens or len(tokens) > 8:
        return "fallo", []
    grupos = [tokens]
    limpios = [_token_limpio(t) for t in tokens]
    if "y" in limpios:
        pos = limpios.index("y")
        izq, der = tokens[:pos], tokens[pos + 1:]
        if 0 < len(izq) <= 2 and 0 < len(der) <= 2:
            grupos = [izq, der]
    palabras = []
    for grupo in grupos:
        grupo = quitar_prefijos(quitar_cantidad(grupo))
        if not grupo:
            continue
        comp = _compuesto(grupo)
        palabra = comp or _palabra_principal(grupo)
        if palabra is None or len(palabra) < 3:
            return "fallo", []
        if clave(palabra) in UTENSILIOS or clave(palabra) in IGNORAR_PALABRA:
            return "ignorar", []
        palabras.append(palabra)
    if not palabras:
        return "fallo", []
    return "ok", palabras


def singular(palabra, vocabulario=None):
    vocabulario = vocabulario or {}
    if " " in palabra or len(palabra) < 4 or clave(palabra) in SINGULARES_FIJOS:
        return palabra
    if palabra.endswith("ones"):
        return palabra[:-4] + "ón"
    if palabra.endswith("ces"):
        return palabra[:-3] + "z"
    if palabra.endswith("es"):
        a, b = palabra[:-1], palabra[:-2]
        if vocabulario.get(a, 0) >= vocabulario.get(b, 0) and vocabulario.get(a, 0) > 0:
            return a
        if vocabulario.get(b, 0) > 0:
            return b
        if palabra.endswith(("ores", "ales")):
            return b
        return a
    if palabra.endswith("s") and not palabra.endswith("ss"):
        return palabra[:-1]
    return palabra


def canonico(palabra, vocabulario=None):
    if " " in palabra:
        nombre = palabra
    else:
        nombre = singular(palabra, vocabulario)
    return SINONIMOS.get(clave(nombre), nombre)


def extraer_ingredientes(texto, vocabulario=None):
    resultado = []
    for linea in dividir_ingredientes(texto):
        estado, palabras = analizar_linea(linea)
        if estado == "ok":
            resultado.extend(canonico(p, vocabulario) for p in palabras)
    return resultado

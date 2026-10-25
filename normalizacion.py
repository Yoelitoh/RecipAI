import ast
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
    "tapa", "tapas", "unidad", "unidades", "ud", "uds", "centimetro", "centimetros", "cm",
    "pellizco", "pellizcos", "tarro", "tarros", "vasito", "vasitos", "trocito", "trocitos",
    "cch", "cdita", "cditas", "cuch", "cuchs", "unid", "unids", "pza", "pzas", "chispa", "chispas",
    "hebra", "hebras", "lamina", "laminas", "palo", "palos", "pastilla", "pastillas", "barrita",
    "barritas", "ramillete", "ramilletes", "sobrecito", "sobrecitos", "terron", "terrones",
    "medida", "medidas", "chorreon", "cta", "ctas", "copita", "copitas", "ramito", "ramitos", "und", "unds",
    "tacita", "tacitas", "grm", "grms", "grs", "lbs", "lb", "gms", "cuña", "cuñas", "cuenco", "cuencos", "dado", "dados",
    "placa", "placas", "pocillo", "pocillos", "bolsita", "bolsitas", "latita", "latitas", "pedacito", "pedacitos",
    "pote", "potes", "tarrina", "tarrinas", "rulo", "rulos", "racimo", "racimos", "manojito", "manojitos",
    "atado", "atados", "caballito", "caballitos", "toque", "ras",
    "plancha", "planchas", "perla", "perlas", "aro", "aros", "botellin", "botellines", "cubilete", "cubiletes",
    "tza", "tzas", "lts", "lt", "lto", "ltrs", "bolita", "bolitas", "cc", "cl", "dl", "ccs", "kgr", "kgrs", "cucharon", "cucharones", "brick", "bricks", "brik", "cubico", "cubicos", "bote", "botes", "docenas", "anillo", "anillos", "planta", "plantas", "ram", "bar",
}

UNIDADES_DEBILES = {"filete", "filetes"}

CUCHARAS = {"cucharilla", "cucharillas", "cuchara", "cucharas", "cchta", "cchtas", "cucharada", "cucharadas", "cucharadita", "cucharaditas", "cda", "cdas", "cdta", "cdtas"}
CALIFICADORES_CUCHARA = {
    "postre", "cafe", "sopera", "soperas", "rasa", "rasas", "colmada", "colmadas", "grande", "grandes", "pequena", "pequenas",
}

RELLENO = {
    "aprox", "aproximadamente", "alrededor", "cerca", "unos", "unas", "un",
    "una", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
    "nueve", "diez", "once", "doce", "docena", "media", "medio", "mitad",
    "de", "del", "la", "el", "los", "las", "y", "o", "al", "poco", "poca",
    "pocas", "pocos", "algunas", "algunos", "varias", "varios", "como",
    "casi", "gusto", "necesaria", "necesario", "cantidad", "suficiente", "suficientes",
    "abundante", "cualquier", "cualquiera", "otro", "otra", "otros", "otras", "alguno", "alguna",
    "fino", "fina", "finos", "finas", "grande", "grandes", "mediano", "mediana", "medianos",
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
    "en", "para", "sin", "con", "que", "si", "u", "o", "es", "gusto", "opcional",
    "opcionales", "aprox", "aproximadamente", "ver", "nota", "segun",
    "cada", "mas", "menos", "por", "picadito", "picadita", "picaditos",
    "picaditas", "finito", "finita", "finitos", "finitas", "separando",
    "suficiente", "fundido", "fundida", "derretido", "derretida", "triturado", "triturada",
    "bajo", "baja", "light", "bien", "entero", "entera", "enteros", "enteras",
    "fresco", "fresca", "frescos", "frescas", "maduro", "madura", "maduros",
    "maduras", "seco", "seca", "secos", "secas",
}

PREFIJOS_DE = {
    "jugo", "zumo", "ralladura", "cascara", "pulpa", "yema", "yemas", "clara",
    "claras", "corteza", "cortezas", "semilla", "semillas", "raiz", "raices", "cogollo", "cogollos", "bulbo",
    "bulbos", "penca", "pencas", "corazon", "corazones", "piel",
}

IGNORAR_PALABRA = {
    "pero", "aunque", "nota", "notas", "opcional", "opcionales", "ver", "si", "gusto",
    "necesario", "necesaria", "cantidad", "persona", "personas", "racion", "raciones", "etc", "receta", "ponle",
    "tipo", "ingrediente", "acompanamiento", "puede", "separado", "separados", "separada", "separadas", "desgranado",
    "remojado", "despepitado", "deshuesada", "deshuesado", "preparado", "instantaneo", "soluble", "color", "amargo",
    "picante", "blanco", "blanca", "rojo", "roja", "negro", "negra", "grande", "grandes", "pequeno", "pequena", "ligeramente",
}

SINGULARES_FIJOS = {"res", "anis", "cuscus", "mas", "gas", "tres", "pan", "hummus", "humus", "callos"}

GENERICOS_OBLIGATORIOS = {
    "caldo", "salsa", "crema", "fecula", "polvo", "mezcla", "condimento", "humo", "sirop", "jarabe",
    "sazonador", "esencia", "extracto", "aroma", "dulce", "hueso", "alita", "ala", "higado", "higadito",
    "grasa", "miga", "copo", "orejon", "relleno", "fondo", "sofrito", "masa", "aromatizante", "concentrado", "base", "pipa", "chip",
}
CORTES = {
    "lomo", "solomillo", "costilla", "muslo", "contramuslo", "pechuga", "chuleta", "falda", "nalga",
    "cadera", "carrillera", "cuerito", "presa", "paleta", "aleta", "carre", "pecho", "secreto", "pluma",
    "entrecot", "rabo", "pata", "zancarron", "punta", "bistec", "bife", "matambre", "arrachera", "pierna",
    "redondo", "bondiola", "espinazo", "costillar", "medallon",
}
GENERICOS_OPCIONALES = {"tortilla", "queso", "pasta", "seta"}

ANIMALES = {
    "pollo", "gallina", "pavo", "pato", "oca", "codorniz", "perdiz", "ave", "ternera", "vaca", "buey", "res",
    "cerdo", "puerco", "cochinillo", "lechon", "cordero", "cabrito", "cabra", "conejo", "liebre", "jabali",
    "ciervo", "venado", "caballo", "atun", "salmon", "bacalao", "merluza", "rape", "bonito", "lubina",
    "dorada", "trucha", "pulpo", "calamar", "sepia", "cangrejo", "langosta", "bogavante", "gamba",
}
CORTE_EXCLUIDOS = {"huevo", "huevos", "leche", "queso", "mantequilla", "manteca", "yogur", "nata", "crema"}

UTENSILIOS = {
    "cuchillo", "palillo", "palillos", "papel", "plastico", "olla", "sarten",
    "charola", "molde", "licuadora", "procesador", "aluminio", "servilleta",
    "toalla", "brocheta", "brochetas", "vidrio", "bandeja", "cacerola",
    "tazon", "recipiente", "comal", "batidora", "colador", "rosticero",
    "cuchara", "tenedor", "horno", "tapa", "pinza", "pinzas", "espatula", "huevera",
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


def _claves(conjunto):
    return {clave(x) for x in conjunto}


UNIDADES = _claves(UNIDADES)
UNIDADES_FUERTES = UNIDADES - _claves(UNIDADES_DEBILES)
CUCHARAS = _claves(CUCHARAS)
CALIFICADORES_CUCHARA = _claves(CALIFICADORES_CUCHARA)
RELLENO = _claves(RELLENO)
CORTE = _claves(CORTE)
UTENSILIOS = _claves(UTENSILIOS)
PREFIJOS_DE = _claves(PREFIJOS_DE)
IGNORAR_PALABRA = _claves(IGNORAR_PALABRA)
GENERICOS_OBLIGATORIOS = _claves(GENERICOS_OBLIGATORIOS) | _claves(CORTES)
CORTES = _claves(CORTES)
GENERICOS_OPCIONALES = _claves(GENERICOS_OPCIONALES)
ANIMALES = _claves(ANIMALES)
CORTE_EXCLUIDOS = _claves(CORTE_EXCLUIDOS)
ACENTOS = {"orejon": "orejón", "higado": "hígado", "carre": "carré", "fecula": "fécula"}
ARTICULOS = {"la", "el", "los", "las", "un", "una"}
STOP_COMPLEMENTO = {
    "variado", "variada", "variados", "variadas", "surtido", "surtida", "surtidos", "surtidas",
    "mixto", "mixta", "mixtos", "mixtas", "tipo", "estilo", "donde", "que", "se", "su", "al", "a", "si", "como", "cuando", "por", "lo", "le", "es", "ya"}

MOJIBAKE = {
    "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú", "Ã±": "ñ", "Ã¼": "ü",
    "Â¿": "¿", "Â¡": "¡", "Âº": "º", "Âª": "ª", "Â½": "½", "Â¼": "¼", "Â¾": "¾", "Â": "",
}


def reparar_codificacion(texto):
    if not isinstance(texto, str) or ("Ã" not in texto and "Â" not in texto):
        return texto
    for codec in ("cp1252", "latin-1"):
        try:
            return texto.encode(codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    for malo, bueno in MOJIBAKE.items():
        texto = texto.replace(malo, bueno)
    return texto

def _patron_flexible(frase):
    vocales = {"a": "[aáàä]", "e": "[eéèë]", "i": "[iíìï]", "o": "[oóòö]", "u": "[uúùü]"}
    partes = [vocales.get(c, re.escape(c)) for c in clave(frase)]
    return re.compile(r"(?<!\w)" + "".join(partes) + r"(?!\w)", re.I)


def _leer_frases():
    ruta = CARPETA / "frases.csv"
    frases = []
    if ruta.exists():
        with ruta.open(encoding="utf-8", newline="") as f:
            for fila in csv.reader(f):
                if len(fila) >= 2 and not fila[0].startswith("#"):
                    frases.append((_patron_flexible(fila[0].strip()), fila[1].strip()))
    return frases


FRASES = _leer_frases()


def aplicar_frases(texto):
    for patron, reemplazo in FRASES:
        texto = patron.sub(reemplazo, texto)
    return texto


def limpiar_texto(texto):
    texto = reparar_codificacion(texto)
    texto = texto.replace("\u200b", "").replace("\xa0", " ")
    texto = re.sub(r"[ðŸÿ]+[^\w\s]{0,2}", "", texto)
    texto = re.sub(r"(?<=\d)(?=[A-Za-zñáéíóúÑÁÉÍÓÚ])", " ", texto)
    for patron, reemplazo in REPARACIONES:
        texto = patron.sub(reemplazo, texto)
    texto = re.sub(r"\([^)]*\)", " ", texto)
    texto = re.sub(r"\bc\s*/\s*[nsNS]\b|\b[qQ]\.?\s?[bB]\.?(?=\s|$)", " ", texto)
    texto = re.sub(r"(?<=\d),(?=\d)", ".", texto)
    texto = texto.replace("*", " ").replace("/", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = aplicar_frases(texto)
    return texto.strip("'\" ")


def _dividir_comas(texto):
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


def dividir_ingredientes(texto):
    texto = str(texto or "").strip()
    elementos = [texto]
    if texto.startswith("["):
        try:
            valor = ast.literal_eval(texto)
            if isinstance(valor, (list, tuple)):
                elementos = [str(v) for v in valor]
        except (ValueError, SyntaxError):
            interior = texto.strip("[]")
            elementos = [e.strip("'\" ") for e in re.split(r"['\"]\s*,\s*['\"]", interior)]
    partes = []
    for elemento in elementos:
        partes.extend(_dividir_comas(elemento))
    return partes


def _token_limpio(token):
    return clave(token).strip(".,;:()\"'")


def quitar_cantidad(tokens):
    tokens = list(tokens)
    tras_cuchara = False
    while len(tokens) > 1:
        t = _token_limpio(tokens[0])
        if t in CUCHARAS:
            tras_cuchara = True
            tokens.pop(0)
        elif not t or RE_NUMERO.match(t) or t in UNIDADES or t in RELLENO:
            tokens.pop(0)
        elif tras_cuchara and t in CALIFICADORES_CUCHARA:
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
        siguiente = [t for t in tokens[2:] if _token_limpio(t) not in ARTICULOS and not RE_NUMERO.match(_token_limpio(t))]
        if siguiente and _token_limpio(siguiente[0]) in ANIMALES:
            break
        tokens = tokens[2:]
    return tokens


def _sin_plural(texto):
    return " ".join(
        w[:-1] if w.endswith("s") and len(w) > 3 and not w.endswith("ss") else w for w in texto.split()
    )


def _compuesto(tokens):
    frase = _sin_plural(clave(" ".join(tokens)))
    for compuesto_clave, compuesto in COMPUESTOS_CLAVE:
        ck = _sin_plural(compuesto_clave)
        if frase == ck or frase.startswith(ck + " "):
            return compuesto
    return None


def _palabra_principal(tokens):
    for token in tokens:
        palabra = re.sub(r"[^\wñáéíóúü]", "", token.lower())
        if palabra and not palabra.isdigit():
            return palabra
    return None


def _singular_simple(palabra):
    if palabra.endswith("s") and len(palabra) > 4 and not palabra.endswith(("ss", "is", "us")):
        return palabra[:-1]
    return palabra


def _complemento_de(tokens):
    if len(tokens) >= 3 and _token_limpio(tokens[1]) in ("de", "del"):
        siguiente = [t for t in tokens[2:] if _token_limpio(t) not in ARTICULOS]
        if siguiente:
            return _palabra_principal(siguiente[:1])
    return None


def _generico(tokens):
    cabeza = _token_limpio(tokens[0])
    complemento = _complemento_de(tokens)
    if (
        complemento and clave(complemento) in ANIMALES and cabeza.isalpha() and len(cabeza) >= 3
        and cabeza not in CORTE_EXCLUIDOS and cabeza not in RELLENO and cabeza not in UNIDADES
    ):
        return "%s de %s" % (_singular_simple(tokens[0].lower().strip(".,;:")), complemento)
    todos = GENERICOS_OBLIGATORIOS | GENERICOS_OPCIONALES
    base = cabeza
    candidatos = [cabeza]
    if cabeza.endswith("s"):
        candidatos.append(cabeza[:-1])
    if cabeza.endswith("es"):
        candidatos.append(cabeza[:-2])
    for candidato in candidatos:
        if candidato in todos:
            base = candidato
            break
    obligatorio = base in GENERICOS_OBLIGATORIOS
    if not obligatorio and base not in GENERICOS_OPCIONALES:
        return None
    nombre = tokens[0].lower().strip(".,;:") if base == cabeza else ACENTOS.get(base, base)
    resto = tokens[1:]
    if complemento and clave(complemento) in ("coccion", "cocer", "cocinar", "cocido", "cocida"):
        return "__fallo__"
    if complemento:
        return "%s de %s" % (nombre, complemento)
    if ((obligatorio and base not in CORTES) or base in ("queso", "seta")) and resto and _token_limpio(resto[0]) not in ("de", "del"):
        palabra = _palabra_principal(resto[:1])
        if palabra and _token_limpio(resto[0]) not in CORTE | RELLENO | STOP_COMPLEMENTO:
            return "%s %s" % (nombre, palabra)
    return "__fallo__" if obligatorio else None


def _hay_alternativa(tokens):
    for k, token in enumerate(tokens):
        if k == 0 or _token_limpio(token) not in ("o", "u"):
            continue
        despues = tokens[k + 1:]
        if not despues or _token_limpio(despues[0]) in ("de", "del") or RE_NUMERO.match(_token_limpio(despues[0])):
            return False
        despues = quitar_prefijos(quitar_cantidad(despues))
        palabra_despues = _palabra_principal(despues[:1])
        palabra_antes = _palabra_principal(quitar_prefijos(tokens[:k]))
        if not palabra_despues or not palabra_antes:
            return False
        if clave(palabra_antes) not in ANIMALES or clave(palabra_despues) not in ANIMALES:
            return False
        return canonico(palabra_antes) != canonico(palabra_despues)
    return False


def analizar_linea(linea):
    texto = limpiar_texto(linea)
    if not texto or texto.endswith(":") or clave(texto).startswith("para "):
        return "ignorar", []
    tokens = quitar_prefijos(quitar_cantidad(texto.split()))
    if not tokens:
        return "fallo", []
    if len(tokens) > 1 and _token_limpio(tokens[0]) == "de":
        return "ignorar", []
    if _hay_alternativa(tokens):
        return "fallo", []
    comp = _compuesto(tokens)
    if comp:
        return "ok", [comp]
    gen = _generico(tokens)
    if gen == "__fallo__":
        return "fallo", []
    if gen:
        return "ok", [gen]
    primero = _token_limpio(tokens[0])
    tokens = cortar_preparacion(tokens)
    if not tokens and primero in CORTE:
        return "ignorar", []
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
        gen = _generico(grupo)
        if gen == "__fallo__":
            return "fallo", []
        comp = _compuesto(grupo) or gen
        palabra = comp or _palabra_principal(grupo)
        if palabra is None or len(palabra) < 3:
            return "fallo", []
        if clave(palabra) in UTENSILIOS or clave(palabra) in IGNORAR_PALABRA or clave(palabra) in UNIDADES_FUERTES or clave(palabra).endswith("mente"):
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
        if palabra.endswith(("ores", "ales", "ines")):
            return b
        return a
    if palabra.endswith("s") and not palabra.endswith("ss"):
        return palabra[:-1]
    return palabra


def canonico(palabra, vocabulario=None):
    if " " in palabra:
        nombre = palabra
        if clave(nombre) not in SINONIMOS and " de " in nombre:
            cabeza, _, resto = nombre.partition(" de ")
            if clave(resto) in SINONIMOS:
                nombre = cabeza + " de " + SINONIMOS[clave(resto)]
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
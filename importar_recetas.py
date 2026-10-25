import argparse
import difflib
import getpass
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from normalizacion import (
    BASICOS, IGNORAR_PALABRA, SINONIMOS, UNIDADES_FUERTES, UTENSILIOS, analizar_linea, canonico, clave,
    dividir_ingredientes, reparar_codificacion,
)

CARPETA = Path(__file__).resolve().parent

TIPOS = [
    ("postre",
     r"postre|dulce|flan|galleta|helado|gelatina|mousse|natilla|brownie|bizcocho|budin|pudin|merengue|cheesecake|bunuelo|capirotada|tres leches|arroz con leche|mermelada|compota|churro|rosca|torrija|gofre|panqueque|magdalena|cupcake|muffin|alfajor|trufa|caramelo|turron|cajeta|en tacha|crema catalana|crema pastelera|sorbete|ganache|marquise|pancake|tortitas|\\bteja|majarete|sirope|tiramisu|profiterol|polvoron|mantecado|coulant|fudge|bombon",
     None),
    ("bebida",
     r"ponche|licuado|batido|coctel|cocktail|bebida|limonada|smoothie|atole|chocolate caliente|rompope|sangria|horchata|refresco|\bcafe\b|licor|caipirinha|frape|mojito|cerveza|zumo|\bte\b|infusion|colada|margarita|daiquiri",
     None),
    ("salsa",
     r"salsa|aderezo|vinagreta|guacamole|mojo|chimichurri|mayonesa|alioli|pesto|sofrito|encurtid|curtid|escabeche",
     r"^(?:salsa|aderezo|vinagreta|guacamole|pico de gallo|mojo|chimichurri|mayonesa|alioli|pesto|sofrito|hummus|humus|pate|chutney|mermelada de (?:cebolla|tomate|pimiento))"),
    ("sopa", r"sopa|crema de|caldo|consome|pozole|gazpacho|salmorejo|ajoblanco|vichyssoise|cocido|menestra|puchero|sancocho|locro|potaje", None),
    ("ensalada", r"ensalada", None),
    ("pasta", r"pasta|espagueti|spaghetti|macarron|fideo|lasana|tallarin|canelon|raviol|noqui|fusilli|penne|coditos", None),
    ("arroz", r"arroz|paella|risotto|risoto", None),
    ("pescado y marisco",
     r"pescado|marisco|camaron|atun|salmon|bacalao|pulpo|calamar|merluza|tilapia|ceviche|gamba|mejillon|almeja|jaiba|langostino|trucha|sardina|dorada|lubina|robalo|corvina|huachinango|mojarra|pargo|cangrejo|bonito|bogavante|besugo|\\brape\\b|boqueron|anchoa|sushi|maki|nigiri|nigeri|\\bpacu|vieira|necora|sepia|chipiron|lenguado|rodaballo|gambas|percebe|zamburina|anguila",
     None),
    ("tacos y antojitos",
     r"taco|quesadilla|tamal|empanada|tostada|enchilada|burrito|nacho|taquito|gordita|sope|tlayuda|arepa|pupusa|fajita|chilaquil|totopo|flauta|huarache|falafel|pakora|croqueta|samosa|rollito",
     None),
    ("carne",
     r"carne|cerdo|puerco|pollo|pavo|\bres\b|ternera|cordero|chorizo|jamon|costilla|albondiga|bistec|bife|pierna|lomo|chuleta|cochinita|barbacoa|milanesa|hamburguesa|salchicha|tocino|pernil|filete|medallon|solomillo|entrecot|higado|butifarra|cochinillo|conejo|cabrito|morcilla|callos|gulash|goulash|rabo de|lengua|codorniz|pato|oso buco|asado|rosbif|kebab",
     None),
    ("huevos", r"huevo|omelette|revuelto|quiche|tortilla", None),
    ("verdura",
     r"ratatouille|alcachofa|menestra|pisto|esparrago|judias verdes|setas|verdura|vegetal|hortaliza|legumbre|frijol|lenteja|garbanzo|champinon|hongo|nopal|calabaza|calabacita|berenjena|espinaca|brocoli|coliflor|chayote|papa\b|papas|patata|camote|yuca",
     None),
    ("pan y masa", r"\bpan\b|masa|pizza|focaccia|brioche|bollo|sandwich|bocadillo|bocata|canape|tosta|bagel|\btorta\b", None),
]
TIPOS_COMPILADOS = [
    (tipo, re.compile(pat_cat), re.compile(pat_nom if pat_nom else pat_cat))
    for tipo, pat_cat, pat_nom in TIPOS
]


PESCADOS = {
    "atun", "salmon", "bacalao", "merluza", "gamba", "langostino", "bonito", "besugo", "lubina", "dorada",
    "pulpo", "calamar", "mejillon", "vieira", "bogavante", "sardina", "anchoa", "trucha", "rape", "nécora",
    "necora", "almeja", "cangrejo", "sepia", "lenguado", "rodaballo", "surimi", "boqueron", "pescado", "marisco",
    "camaron", "jaiba", "tilapia", "caballa", "pacu",
}
CARNES = {
    "pollo", "ternera", "cerdo", "cordero", "butifarra", "higado", "conejo", "pavo", "lomo", "costilla",
    "carne", "solomillo", "chuleta", "cochinillo", "morcilla", "pato", "salchicha", "hamburguesa", "bistec",
    "bife", "pechuga", "muslo", "cabrito", "codorniz", "entrecot", "rabo", "tocino", "panceta",
}
DULCES = {"azucar", "chocolate", "nata", "vainilla", "miel", "cacao", "cocoa", "mermelada", "sirope", "caramelo", "esencia"}
SALADOS = {
    "ajo", "cebolla", "tomate", "pimiento", "puerro", "pimienta", "vino", "caldo", "perejil", "laurel",
    "oregano", "pimenton", "comino", "zanahoria", "patata",
}
VERDURAS = {
    "zanahoria", "calabacin", "berenjena", "pimiento", "espinaca", "acelga", "coliflor", "brocoli", "alcachofa",
    "judia", "esparrago", "puerro", "calabaza", "champinon", "seta", "col", "repollo", "lechuga", "pepino",
    "nabo", "remolacha", "guisante", "haba", "lenteja", "garbanzo", "alubia", "tomate", "patata", "maiz",
}
PASTAS = {"pasta", "espagueti", "macarron", "fideo", "lasana", "tallarin", "canelon", "penne"}


def tipo_por_ingredientes(nombres):
    claves = {clave(n) for n in nombres}
    if claves & PESCADOS:
        return "pescado y marisco"
    if claves & CARNES:
        return "carne"
    if claves & DULCES and not claves & SALADOS:
        return "postre"
    if "arroz" in claves:
        return "arroz"
    if claves & PASTAS:
        return "pasta"
    if len(claves & VERDURAS) >= 3:
        return "verdura"
    return None


POSTRE_DEBIL = re.compile(r"pastel|tarta|tartaleta|crepa")
SALADO = re.compile(
    r"carne|pollo|pescado|atun|salmon|bacalao|merluza|marisco|gamba|verdura|patata|jamon|puerro|calabacin|"
    r"espinaca|cerdo|champinon|berenjena|lomo|ternera|pavo|brocoli|cordero|chorizo|salchicha|bechamel|seta|hongo|"
    r"salad[oa]|gratinad|arroz|cebolla|ajo"
)


def asignar_tipo(categoria, nombre, ingredientes=None):
    cat = clave(categoria or "")
    nom = clave(nombre or "")
    for tipo, re_cat, _ in TIPOS_COMPILADOS:
        if not cat:
            break
        if re_cat.search(cat) or (tipo == "postre" and POSTRE_DEBIL.search(cat)):
            return tipo
    for tipo, _, re_nom in TIPOS_COMPILADOS:
        if not nom:
            break
        if re_nom.search(nom):
            return tipo
        if tipo == "postre" and POSTRE_DEBIL.search(nom) and not SALADO.search(nom):
            return tipo
    if ingredientes:
        return tipo_por_ingredientes(ingredientes) or "otros"
    return "otros"


def buscar_columna(df, *candidatos):
    por_clave = {clave(c): c for c in df.columns}
    for candidato in candidatos:
        if clave(candidato) in por_clave:
            return por_clave[clave(candidato)]
    return None


def a_minutos(texto):
    coincidencia = re.match(r"^\s*(\d+):(\d{2})\s*$", str(texto or ""))
    if not coincidencia:
        return None
    return int(coincidencia.group(1)) * 60 + int(coincidencia.group(2))


def a_entero(texto):
    coincidencia = re.search(r"\d+", str(texto or ""))
    return int(coincidencia.group()) if coincidencia else None


def texto_o_none(valor):
    valor = str(valor or "").strip()
    return None if valor.lower() in ("", "null", "nan", "none") else valor


def cargar_datos(args):
    if args.csv:
        return pd.read_csv(args.csv, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    try:
        from datasets import load_dataset
        conjunto = load_dataset("somosnlp/RecetasDeLaAbuela", args.subconjunto, split="train")
        return conjunto.to_pandas().astype(str)
    except Exception as error:
        sys.exit(
            "No se ha podido descargar el dataset automaticamente (%s).\n"
            "Descargalo a mano desde Hugging Face y usa --csv ruta/al/fichero.csv" % error
        )


def analizar_receta(ingredientes_texto):
    lineas = dividir_ingredientes(ingredientes_texto)
    resultados = []
    for linea in lineas:
        estado, palabras = analizar_linea(linea)
        resultados.append((linea, estado, palabras))
    return resultados


def cargar_aprobados(ruta):
    if not ruta:
        return None
    tabla = pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return {clave(f["ingrediente"]) for _, f in tabla.iterrows() if clave(f.get("aprobado", "")) in ("si", "s", "1", "x")}


def procesar(df, args):
    c_id = buscar_columna(df, "Id")
    c_nombre = buscar_columna(df, "Nombre")
    c_url = buscar_columna(df, "URL")
    c_ingr = buscar_columna(df, "Ingredientes")
    c_pasos = buscar_columna(df, "Pasos")
    c_pais = buscar_columna(df, "Pais")
    c_dur = buscar_columna(df, "Duracion")
    c_cat = buscar_columna(df, "Categoria")
    c_com = buscar_columna(df, "Comensales")
    c_tiempo = buscar_columna(df, "Tiempo")
    c_dif = buscar_columna(df, "Dificultad")
    if not all([c_nombre, c_ingr, c_pasos]):
        sys.exit("Faltan columnas obligatorias (Nombre, Ingredientes, Pasos). Columnas encontradas: %s" % list(df.columns))

    parseadas = []
    vocabulario = Counter()
    for _, fila in df.iterrows():
        analisis = analizar_receta(fila[c_ingr])
        parseadas.append(analisis)
        for _, estado, palabras in analisis:
            if estado == "ok":
                vocabulario.update(palabras)

    frecuencia_recetas = Counter()
    canonicos_por_receta = []
    for analisis in parseadas:
        nombres = set()
        for _, estado, palabras in analisis:
            if estado == "ok":
                nombres.update(canonico(p, vocabulario) for p in palabras)
        canonicos_por_receta.append(nombres)
        frecuencia_recetas.update(nombres)

    aceptadas, descartadas = [], []
    aprobados = cargar_aprobados(args.aprobados)
    bloqueos = Counter()
    lineas_total = lineas_ok = lineas_fallo = lineas_ignoradas = 0
    for i, (_, fila) in enumerate(df.iterrows()):
        analisis = parseadas[i]
        validas = [a for a in analisis if a[1] != "ignorar"]
        lineas_total += len(analisis)
        lineas_ignoradas += len(analisis) - len(validas)
        buenas = 0
        dudosas = []
        for linea, estado, palabras in validas:
            if estado != "ok":
                dudosas.append(linea)
                lineas_fallo += 1
                continue
            lineas_ok += 1
            nombres = [canonico(p, vocabulario) for p in palabras]
            if any(frecuencia_recetas[n] < args.min_frec for n in nombres):
                dudosas.append(linea)
            else:
                buenas += 1
        nombre = reparar_codificacion(fila[c_nombre])
        identificador = fila[c_id] if c_id else str(i + 1)
        if len(canonicos_por_receta[i]) < 2:
            descartadas.append((identificador, nombre, "menos de 2 ingredientes reconocidos", " | ".join(dudosas)))
            continue
        if validas and buenas / len(validas) < args.min_ratio:
            descartadas.append((identificador, nombre, "demasiadas lineas dudosas", " | ".join(dudosas)))
            continue
        if aprobados is not None:
            pendientes = sorted(n for n in canonicos_por_receta[i] if clave(n) not in aprobados and not es_basico(n))
            if pendientes:
                bloqueos.update(pendientes)
                descartadas.append((identificador, nombre, "ingrediente no aprobado", " | ".join(pendientes)))
                continue
        if len(str(fila[c_pasos]).strip()) < 40:
            descartadas.append((identificador, nombre, "pasos demasiado cortos", ""))
            continue
        aceptadas.append(i)

    recetas = []
    for i in aceptadas:
        fila = df.iloc[i]
        por_ingrediente = {}
        for linea, estado, palabras in parseadas[i]:
            if estado != "ok":
                continue
            for palabra in palabras:
                nombre_canonico = canonico(palabra, vocabulario)
                clave_ing = clave(nombre_canonico)
                if clave_ing in por_ingrediente:
                    por_ingrediente[clave_ing][1].append(linea)
                else:
                    por_ingrediente[clave_ing] = [nombre_canonico, [linea]]
        categoria = texto_o_none(fila[c_cat]) if c_cat else None
        recetas.append({
            "id": int(fila[c_id]) if c_id and str(fila[c_id]).isdigit() else i + 1,
            "nombre": reparar_codificacion(fila[c_nombre]).strip(),
            "categoria_original": categoria,
            "tipo_plato": asignar_tipo(categoria, fila[c_nombre], [n for n, _ in por_ingrediente.values()]),
            "momento": texto_o_none(fila[c_tiempo]) if c_tiempo else None,
            "pais": texto_o_none(fila[c_pais]) if c_pais else None,
            "duracion_min": a_minutos(fila[c_dur]) if c_dur else None,
            "comensales": a_entero(fila[c_com]) if c_com else None,
            "dificultad": texto_o_none(fila[c_dif]) if c_dif else None,
            "instrucciones": reparar_codificacion(str(fila[c_pasos])).replace("\r", "").strip(),
            "url": texto_o_none(fila[c_url]) if c_url else None,
            "ingredientes_originales": reparar_codificacion(fila[c_ingr]),
            "ingredientes": {k: (v[0], " | ".join(v[1])) for k, v in por_ingrediente.items()},
        })

    estadisticas = {
        "recetas_totales": len(df),
        "recetas_aceptadas": len(aceptadas),
        "recetas_descartadas": len(descartadas),
        "lineas_total": lineas_total,
        "lineas_ok": lineas_ok,
        "lineas_fallo": lineas_fallo,
        "lineas_ignoradas": lineas_ignoradas,
        "bloqueos": bloqueos,
    }
    return recetas, descartadas, estadisticas, frecuencia_recetas


def avisos_ingredientes(frecuencia):
    ruido = UNIDADES_FUERTES | UTENSILIOS | IGNORAR_PALABRA
    frecuentes = [clave(n) for n, c in frecuencia.items() if c >= 30]
    avisos = {}
    for nombre, usos in frecuencia.items():
        k = clave(nombre)
        notas = []
        if len(k) < 3:
            notas.append("muy corto")
        if re.search(r"\d", k) or not re.fullmatch(r"[a-z ]+", k):
            notas.append("caracteres raros")
        if k in ruido:
            notas.append("posible medida o nota")
        if k in SINONIMOS and clave(SINONIMOS[k]) != k:
            notas.append("americanismo o variante: usar " + SINONIMOS[k])
        if re.search(r"(ado|ada|ados|adas|ido|ida|idos|idas)$", k) and " " not in k and k not in ("pescado", "helado", "rebozado"):
            notas.append("posible participio")
        if usos >= 3 and usos < 30:
            cercano = difflib.get_close_matches(k, frecuentes, n=1, cutoff=0.86)
            if cercano and cercano[0] != k:
                notas.append("parecido a " + cercano[0])
        avisos[nombre] = "; ".join(notas)
    return avisos


def es_basico(nombre):
    return clave(nombre) in BASICOS or clave(nombre).startswith("aceite")


def escribir_salidas(recetas, descartadas, estadisticas, frecuencia, args):
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    utiles = Counter()
    for r in recetas:
        for nombre, _ in r["ingredientes"].values():
            utiles[nombre] += 1

    aprobados = cargar_aprobados(args.aprobados)
    filas_ing = []
    avisos = avisos_ingredientes(frecuencia)
    for n, c in frecuencia.most_common():
        if aprobados is not None:
            aprobado = "si" if clave(n) in aprobados else ""
        else:
            aprobado = "si" if c >= args.auto_aprobar else ""
        filas_ing.append((n, c, es_basico(n), aprobado, avisos.get(n, "")))
    pd.DataFrame(filas_ing, columns=["ingrediente", "recetas", "es_basico", "aprobado", "aviso"]).to_csv(
        salida / "ingredientes_frecuencia.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(estadisticas["bloqueos"].most_common(), columns=["ingrediente", "recetas_bloqueadas"]).to_csv(
        salida / "ingredientes_pendientes.csv", index=False, encoding="utf-8-sig"
    )

    pd.DataFrame(descartadas, columns=["id", "nombre", "motivo", "lineas_dudosas"]).to_csv(
        salida / "recetas_descartadas.csv", index=False, encoding="utf-8-sig"
    )

    sin_mapear = Counter(r["categoria_original"] for r in recetas if r["tipo_plato"] == "otros")
    pd.DataFrame(sin_mapear.most_common(), columns=["categoria_original", "recetas"]).to_csv(
        salida / "categorias_sin_tipo.csv", index=False, encoding="utf-8-sig"
    )

    azar = random.Random(args.semilla)
    muestra = azar.sample(recetas, min(100, len(recetas)))
    pd.DataFrame(
        [
            (r["id"], r["nombre"], r["ingredientes_originales"],
             ", ".join(n for n, _ in r["ingredientes"].values()), "")
            for r in muestra
        ],
        columns=["id", "nombre", "ingredientes_originales", "ingredientes_detectados", "correcto_si_no"],
    ).to_csv(salida / "muestra_revision.csv", index=False, encoding="utf-8-sig")

    tipos = Counter(r["tipo_plato"] for r in recetas)
    aceptacion = 100 * estadisticas["recetas_aceptadas"] / max(1, estadisticas["recetas_totales"])
    lineas = [
        "INFORME DE IMPORTACION",
        "Recetas en el dataset: %d" % estadisticas["recetas_totales"],
        "Recetas aceptadas: %d (%.1f %%)" % (estadisticas["recetas_aceptadas"], aceptacion),
        "Recetas descartadas: %d" % estadisticas["recetas_descartadas"],
        *["  motivo: %-40s %d" % (m, n) for m, n in Counter(d[2] for d in descartadas).most_common()],
        "Lineas de ingredientes: %d (reconocidas %d, no reconocidas %d, ignoradas %d)" % (
            estadisticas["lineas_total"], estadisticas["lineas_ok"],
            estadisticas["lineas_fallo"], estadisticas["lineas_ignoradas"]),
        "Ingredientes distintos en recetas aceptadas: %d" % len(utiles),
        "Parametros: min_frec=%d, min_ratio=%.2f, ingredientes aprobados: %s" % (args.min_frec, args.min_ratio, args.aprobados or "no se usa"),
        "",
        "Recetas por tipo de plato:",
    ]
    lineas += ["  %-20s %d" % (t, n) for t, n in tipos.most_common()]
    lineas += ["", "Ingredientes mas frecuentes:"]
    lineas += ["  %-20s %d" % (n, c) for n, c in utiles.most_common(30)]
    informe = "\n".join(lineas)
    (salida / "informe.txt").write_text(informe, encoding="utf-8")
    print(informe)
    print("\nFicheros escritos en: %s" % salida.resolve())


def cargar_mysql(recetas, args):
    import mysql.connector

    contrasena = os.environ.get("MYSQL_PASSWORD") or getpass.getpass("Contrasena de MySQL: ")
    conexion = mysql.connector.connect(host=args.host, port=args.puerto, user=args.usuario, password=contrasena)
    cursor = conexion.cursor()
    cursor.execute(
        "CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci" % args.bd
    )
    cursor.execute("USE `%s`" % args.bd)
    if args.reiniciar:
        cursor.execute("DROP TABLE IF EXISTS receta_ingrediente")
        cursor.execute("DROP TABLE IF EXISTS receta")
        cursor.execute("DROP TABLE IF EXISTS ingrediente")
    esquema = (CARPETA / "schema.sql").read_text(encoding="utf-8")
    for sentencia in [s.strip() for s in esquema.split(";") if s.strip()]:
        cursor.execute(sentencia)

    ingredientes = {}
    for r in recetas:
        for clave_ing, (nombre, _) in r["ingredientes"].items():
            actual = ingredientes.get(clave_ing)
            if actual is None or (actual == clave(actual) and nombre != clave(nombre)):
                ingredientes[clave_ing] = nombre
    ids_ingrediente = {}
    for clave_ing, nombre in sorted(ingredientes.items()):
        cursor.execute(
            "INSERT INTO ingrediente (nombre, es_basico) VALUES (%s, %s)",
            (nombre, es_basico(nombre)),
        )
        ids_ingrediente[clave_ing] = cursor.lastrowid

    filas_receta = [
        (r["id"], r["nombre"][:200], (r["categoria_original"] or "")[:100] or None, r["tipo_plato"],
         r["momento"], r["pais"], r["duracion_min"], r["comensales"], r["dificultad"],
         r["instrucciones"], r["url"])
        for r in recetas
    ]
    cursor.executemany(
        "INSERT INTO receta (id, nombre, categoria_original, tipo_plato, momento, pais, duracion_min, "
        "comensales, dificultad, instrucciones, url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        filas_receta,
    )
    filas_relacion = [
        (r["id"], ids_ingrediente[clave_ing], texto[:500])
        for r in recetas
        for clave_ing, (_, texto) in r["ingredientes"].items()
    ]
    cursor.executemany(
        "INSERT INTO receta_ingrediente (receta_id, ingrediente_id, texto_original) VALUES (%s,%s,%s)",
        filas_relacion,
    )
    conexion.commit()
    print("MySQL: %d ingredientes, %d recetas, %d relaciones cargadas en la base %s." % (
        len(ids_ingrediente), len(filas_receta), len(filas_relacion), args.bd))
    cursor.close()
    conexion.close()


def main():
    parser = argparse.ArgumentParser(description="Limpia RecetasDeLaAbuel@ y la carga en MySQL")
    parser.add_argument("--csv", help="ruta al CSV descargado; si se omite se intenta descargar con la libreria datasets")
    parser.add_argument("--subconjunto", default="version_1", help="subconjunto del dataset al descargar con datasets")
    parser.add_argument("--salida", default="salida", help="carpeta para informes y CSV de revision")
    parser.add_argument("--min-frec", type=int, default=5, dest="min_frec",
                        help="un ingrediente que aparece en menos recetas se considera dudoso")
    parser.add_argument("--min-ratio", type=float, default=1.0, dest="min_ratio",
                        help="proporcion minima de lineas fiables para aceptar una receta")
    parser.add_argument("--aprobados", help="CSV revisado (ingredientes_frecuencia.csv con la columna aprobado); solo entran recetas cuyos ingredientes esten aprobados")
    parser.add_argument("--auto-aprobar", type=int, default=15, dest="auto_aprobar",
                        help="en la primera pasada se marcan como aprobados los ingredientes que aparecen en al menos tantas recetas")
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--mysql", action="store_true", help="cargar el resultado en MySQL")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--puerto", type=int, default=3306)
    parser.add_argument("--usuario", default="root")
    parser.add_argument("--bd", default="recipai")
    parser.add_argument("--reiniciar", action="store_true", help="borrar las tablas antes de cargar")
    args = parser.parse_args()

    df = cargar_datos(args)
    recetas, descartadas, estadisticas, frecuencia = procesar(df, args)
    escribir_salidas(recetas, descartadas, estadisticas, frecuencia, args)
    if args.mysql:
        cargar_mysql(recetas, args)


if __name__ == "__main__":
    main()
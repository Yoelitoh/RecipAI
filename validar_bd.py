import argparse
import getpass
import os
import re
import sys

import mysql.connector

from normalizacion import BASICOS, SINONIMOS, UNIDADES_FUERTES, UTENSILIOS, IGNORAR_PALABRA, clave


def conectar(args):
    contrasena = os.environ.get("MYSQL_PASSWORD") or getpass.getpass("Contrasena de MySQL: ")
    return mysql.connector.connect(
        host=args.host, port=args.puerto, user=args.usuario, password=contrasena, database=args.bd
    )


def consulta(cursor, sql, params=None):
    cursor.execute(sql, params or ())
    return cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(description="Valida la base de datos de recetas de RecipAI")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--puerto", type=int, default=3306)
    parser.add_argument("--usuario", default="root")
    parser.add_argument("--bd", default="recipai")
    args = parser.parse_args()

    conexion = conectar(args)
    cursor = conexion.cursor()
    graves, avisos = [], []

    def grave(mensaje):
        graves.append(mensaje)
        print("  [GRAVE] " + mensaje)

    def aviso(mensaje):
        avisos.append(mensaje)
        print("  [AVISO] " + mensaje)

    n_recetas = consulta(cursor, "SELECT COUNT(*) FROM receta")[0][0]
    n_ingredientes = consulta(cursor, "SELECT COUNT(*) FROM ingrediente")[0][0]
    n_relaciones = consulta(cursor, "SELECT COUNT(*) FROM receta_ingrediente")[0][0]
    print("Recetas: %d | Ingredientes: %d | Relaciones: %d" % (n_recetas, n_ingredientes, n_relaciones))
    if n_recetas == 0:
        grave("La tabla receta esta vacia")

    print("\n1. Integridad referencial")
    huerfanas_ri = consulta(cursor, """
        SELECT COUNT(*) FROM receta_ingrediente ri
        LEFT JOIN receta r ON r.id = ri.receta_id
        LEFT JOIN ingrediente i ON i.id = ri.ingrediente_id
        WHERE r.id IS NULL OR i.id IS NULL""")[0][0]
    if huerfanas_ri:
        grave("%d relaciones apuntan a recetas o ingredientes que no existen" % huerfanas_ri)
    sin_ingredientes = consulta(cursor, """
        SELECT r.id, r.nombre FROM receta r
        LEFT JOIN receta_ingrediente ri ON ri.receta_id = r.id
        WHERE ri.receta_id IS NULL""")
    if sin_ingredientes:
        grave("%d recetas sin ningun ingrediente (ej.: %s)" % (len(sin_ingredientes), sin_ingredientes[0][1]))
    ingredientes_sin_receta = consulta(cursor, """
        SELECT i.nombre FROM ingrediente i
        LEFT JOIN receta_ingrediente ri ON ri.ingrediente_id = i.id
        WHERE ri.ingrediente_id IS NULL""")
    if ingredientes_sin_receta:
        aviso("%d ingredientes no se usan en ninguna receta" % len(ingredientes_sin_receta))

    print("\n2. Calidad de las recetas")
    pocas = consulta(cursor, """
        SELECT r.id, r.nombre FROM receta r
        JOIN receta_ingrediente ri ON ri.receta_id = r.id
        JOIN ingrediente i ON i.id = ri.ingrediente_id
        GROUP BY r.id, r.nombre
        HAVING SUM(i.es_basico = 0) < 1""")
    if pocas:
        grave("%d recetas sin ningun ingrediente no basico (ej.: %s)" % (len(pocas), pocas[0][1]))
    cortas = consulta(cursor, "SELECT COUNT(*) FROM receta WHERE CHAR_LENGTH(instrucciones) < 40")[0][0]
    if cortas:
        grave("%d recetas con instrucciones demasiado cortas" % cortas)
    mojibake = consulta(cursor, """
        SELECT COUNT(*) FROM receta
        WHERE nombre COLLATE utf8mb4_bin LIKE '%Ã%'
           OR instrucciones COLLATE utf8mb4_bin LIKE '%Ã©%'
           OR instrucciones COLLATE utf8mb4_bin LIKE '%Ã³%'
           OR instrucciones COLLATE utf8mb4_bin LIKE '%Ã±%'""")[0][0]
    if mojibake:
        grave("%d recetas con caracteres mal codificados" % mojibake)
    duplicadas = consulta(cursor, """
        SELECT nombre, COUNT(*) FROM receta GROUP BY nombre, MD5(instrucciones) HAVING COUNT(*) > 1""")
    if duplicadas:
        aviso("%d recetas duplicadas (mismo nombre e instrucciones), ej.: %s" % (len(duplicadas), duplicadas[0][0]))
    sin_tipo = consulta(cursor, "SELECT COUNT(*) FROM receta WHERE tipo_plato = 'otros'")[0][0]
    if n_recetas and sin_tipo / n_recetas > 0.15:
        aviso("%.1f %% de las recetas sin tipo de plato (otros)" % (100 * sin_tipo / n_recetas))

    print("\n3. Calidad de los ingredientes")
    nombres = consulta(cursor, """
        SELECT i.id, i.nombre, COUNT(ri.receta_id) FROM ingrediente i
        LEFT JOIN receta_ingrediente ri ON ri.ingrediente_id = i.id
        GROUP BY i.id, i.nombre""")
    ruido = UNIDADES_FUERTES | UTENSILIOS | IGNORAR_PALABRA
    sospechosos = []
    for _, nombre, usos in nombres:
        k = clave(nombre)
        if len(k) < 3 or re.search(r"\d", k) or not re.fullmatch(r"[a-z ]+", k) or k in ruido:
            sospechosos.append((nombre, usos))
    if sospechosos:
        grave("%d ingredientes con aspecto de ruido (medidas, numeros, simbolos): %s" % (
            len(sospechosos), ", ".join("%s (%d)" % s for s in sospechosos[:15])))
    sin_normalizar = [n for _, n, _ in nombres if clave(n) in SINONIMOS and clave(SINONIMOS[clave(n)]) != clave(n)]
    if sin_normalizar:
        grave("%d ingredientes con nombre no normalizado al castellano de Espana: %s" % (
            len(sin_normalizar), ", ".join(sin_normalizar[:15])))
    por_clave = {}
    for _, nombre, _ in nombres:
        base = clave(nombre)
        base = base[:-1] if base.endswith("s") and len(base) > 4 else base
        por_clave.setdefault(base, []).append(nombre)
    parecidos = [v for v in por_clave.values() if len(v) > 1]
    if parecidos:
        aviso("%d grupos de ingredientes casi duplicados, ej.: %s" % (len(parecidos), " / ".join(parecidos[0])))
    una_vez = sum(1 for _, _, usos in nombres if usos == 1)
    if nombres and una_vez / len(nombres) > 0.25:
        aviso("%d ingredientes (%.0f %%) aparecen en una sola receta: revisalos" % (una_vez, 100 * una_vez / len(nombres)))
    basicos_bd = {clave(n[0]) for n in consulta(cursor, "SELECT nombre FROM ingrediente WHERE es_basico = 1")}
    faltan = [b for b in BASICOS if b not in basicos_bd]
    if faltan:
        aviso("Basicos esperados que no estan marcados o no existen: %s" % ", ".join(faltan))

    print("\n4. Prueba funcional de la busqueda")
    prueba = consulta(cursor, """
        SELECT r.id FROM receta r
        JOIN receta_ingrediente ri ON ri.receta_id = r.id
        JOIN ingrediente i ON i.id = ri.ingrediente_id
        GROUP BY r.id
        HAVING SUM(i.es_basico = 0 AND i.nombre NOT IN ('huevo', 'cebolla', 'tomate')) = 0
        LIMIT 1""")
    print("  La consulta de 'solo estos ingredientes' se ejecuta correctamente (%d resultados de ejemplo)." % len(prueba))

    print("\nRESUMEN: %d problemas graves, %d avisos" % (len(graves), len(avisos)))
    cursor.close()
    conexion.close()
    sys.exit(1 if graves else 0)


if __name__ == "__main__":
    main()
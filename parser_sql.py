import re
from estructuras.sequential_file import SequentialFile
from estructuras.isam import ISAM
from estructuras.extendible_hash import ExtendibleHash
from estructuras.bplus_tree import BPlusTree
from estructuras.rtree import RTree
from utils.meta_tablas import guardar_tablas, cargar_tablas
from utils.logger import medir_tiempo

# Diccionario que almacena todas las tablas creadas
tablas_cargadas = {}

def parsear_vector(texto):
    return [float(x) for x in texto.replace('[', '').replace(']', '').split()]

def parsear_sql(sentencia):
    sentencia = sentencia.strip().rstrip(";")

    def ejecutar():
        if sentencia.upper().startswith("CREATE TABLE"):
            return _crear_tabla(sentencia)
        elif sentencia.upper().startswith("INSERT INTO"):
            return insertar_registro(sentencia)
        elif sentencia.upper().startswith("SELECT"):
            return seleccionar(sentencia)
        elif sentencia.upper().startswith("DELETE"):
            return eliminar(sentencia)
        else:
            return {"status": "error", "mensaje": "Sentencia no reconocida"}

    return medir_tiempo(ejecutar, sentencia)

def _crear_tabla(sentencia):
    pattern = r"CREATE TABLE\s+(\w+)\s*\(([\s\S]+)\)"
    match = re.match(pattern, sentencia, re.IGNORECASE)
    if not match:
        return {"status": "error", "mensaje": "Error de sintaxis en CREATE TABLE"}

    nombre_tabla = match.group(1)
    campos_raw = match.group(2)

    campos = []
    tipo_indice = None
    campo_clave = None
    campo_vectorial = None

    definiciones = [c.strip() for c in campos_raw.split(",")]
    for definicion in definiciones:
        partes = definicion.split()
        nombre = partes[0]
        tipo = partes[1].upper()
        campos.append(nombre)

        if "PRIMARY" in definicion and "INDEX" in definicion:
            campo_clave = nombre
            if "SEQ" in definicion.upper():
                tipo_indice = "SEQ"
            elif "ISAM" in definicion.upper():
                tipo_indice = "ISAM"
            elif "HASH" in definicion.upper():
                tipo_indice = "HASH"
            elif "BTREE" in definicion.upper():
                tipo_indice = "BTREE"
        elif "INDEX RTREE" in definicion.upper():
            campo_vectorial = nombre
            tipo_indice = "RTREE"

    if tipo_indice == "SEQ":
        instancia = SequentialFile(f"datos/{nombre_tabla}.csv", campos, campo_clave)
    elif tipo_indice == "ISAM":
        instancia = ISAM(f"datos/{nombre_tabla}.csv", f"datos/{nombre_tabla}_index.idx", campos, campo_clave)
    elif tipo_indice == "HASH":
        instancia = ExtendibleHash(clave=campo_clave)
    elif tipo_indice == "BTREE":
        instancia = BPlusTree()
    elif tipo_indice == "RTREE":
        instancia = RTree()
    else:
        return {"status": "error", "mensaje": "Índice desconocido"}

    tablas_cargadas[nombre_tabla] = {
        "estructura": instancia,
        "campos": campos,
        "clave": campo_clave,
        "tipo": tipo_indice,
        "vector": campo_vectorial
    }

    guardar_tablas(tablas_cargadas)

    return {"status": "ok", "mensaje": f"Tabla '{nombre_tabla}' creada con índice {tipo_indice}."}

def insertar_registro(sentencia):
    match = re.match(r"INSERT INTO (\w+)\s+VALUES\s*\((.+)\)", sentencia, re.IGNORECASE)
    if not match:
        return {"status": "error", "mensaje": "Error de sintaxis en INSERT"}

    nombre_tabla = match.group(1)
    valores_raw = match.group(2)
    valores = [v.strip().strip("'") for v in valores_raw.split(",")]

    if nombre_tabla not in tablas_cargadas:
        return {"status": "error", "mensaje": "Tabla no encontrada"}

    info = tablas_cargadas[nombre_tabla]
    campos = info['campos']
    estructura = info['estructura']
    tipo = info['tipo']
    clave = info['clave']
    vector = info['vector']

    if len(valores) != len(campos):
        return {"status": "error", "mensaje": "Cantidad incorrecta de valores"}

    registro = {}
    for i, campo in enumerate(campos):
        if vector and campo == vector:
            registro[campo] = parsear_vector(valores[i])
        elif campo == clave:
            registro[campo] = int(valores[i])
        else:
            registro[campo] = valores[i]

    try:
        if tipo == "SEQ" or tipo == "ISAM" or tipo == "HASH":
            estructura.add(registro)
        elif tipo == "BTREE":
            estructura.add({"clave": registro[clave], **registro})
        elif tipo == "RTREE":
            estructura.add({"punto": registro[vector], **registro})

        if hasattr(estructura, "contador"):
            accesos = estructura.contador.obtener()
            print(f"[DEBUG] Accesos - Lecturas: {accesos['lecturas']}, Escrituras: {accesos['escrituras']}")
            estructura.contador.reset()

        return {"status": "ok", "mensaje": "Registro insertado"}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

def seleccionar(sentencia):
    match_where = re.match(r"SELECT \* FROM (\w+)\s+WHERE\s+(\w+)\s*=\s*(.+)", sentencia, re.IGNORECASE)
    match_all = re.match(r"SELECT \* FROM (\w+)$", sentencia, re.IGNORECASE)
    match_near = re.match(r"SELECT \* FROM (\w+)\s+WHERE\s+(\w+)\s+NEAR\s+(\[.+?\])\s+DIST\s+([\d.]+)", sentencia, re.IGNORECASE)

    if match_where:
        tabla, campo, valor = match_where.groups()
        valor = valor.strip().strip("'")

        if tabla not in tablas_cargadas:
            return {"status": "error", "mensaje": "Tabla no encontrada"}

        info = tablas_cargadas[tabla]
        estructura = info['estructura']
        tipo = info['tipo']
        clave = info['clave']
        vector = info['vector']

        try:
            if campo == clave:
                resultado = estructura.search(int(valor))
                return {"status": "ok", "datos": resultado if isinstance(resultado, list) else [resultado]}
            elif tipo == "RTREE" and campo == vector:
                punto = parsear_vector(valor)
                resultado = estructura.search(punto, radio=0)
                return {"status": "ok", "datos": resultado if resultado else []}
            else:
                return {"status": "error", "mensaje": "Campo no soportado para búsqueda"}
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}

    elif match_near:
        tabla, campo, punto_raw, dist_raw = match_near.groups()
        punto = parsear_vector(punto_raw)
        distancia = float(dist_raw)

        if tabla not in tablas_cargadas:
            return {"status": "error", "mensaje": "Tabla no encontrada"}

        info = tablas_cargadas[tabla]
        estructura = info['estructura']
        tipo = info['tipo']
        vector = info['vector']

        if tipo != "RTREE" or campo != vector:
            return {"status": "error", "mensaje": "Solo se puede usar NEAR con campos vectoriales RTREE"}

        try:
            resultado = estructura.range_search(punto, distancia)
            return {"status": "ok", "datos": resultado}
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}

    elif match_all:
        tabla = match_all.group(1)

        if tabla not in tablas_cargadas:
            return {"status": "error", "mensaje": "Tabla no encontrada"}

        estructura = tablas_cargadas[tabla]['estructura']
        try:
            todos = estructura.all()
            return {"status": "ok", "datos": todos}
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}

    else:
        return {"status": "error", "mensaje": "Sintaxis no válida para SELECT"}

def eliminar(sentencia):
    match = re.match(r"DELETE FROM (\w+)\s+WHERE\s+(\w+)\s*=\s*(.+)", sentencia, re.IGNORECASE)
    if not match:
        return {"status": "error", "mensaje": "Error de sintaxis en DELETE"}

    tabla, campo, valor = match.groups()
    valor = valor.strip().strip("'")

    if tabla not in tablas_cargadas:
        return {"status": "error", "mensaje": "Tabla no encontrada"}

    info = tablas_cargadas[tabla]
    estructura = info['estructura']
    tipo = info['tipo']
    clave = info['clave']
    vector = info['vector']

    try:
        if campo == clave:
            resultado = estructura.remove(int(valor))
        elif tipo == "RTREE" and campo == vector:
            resultado = estructura.remove(parsear_vector(valor))
        else:
            return {"status": "error", "mensaje": "Campo no válido para eliminación"}

        if resultado:
            return {"status": "ok", "mensaje": "Registro eliminado"}
        else:
            return {"status": "error", "mensaje": "Registro no encontrado"}

    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

def cargar_definiciones_guardadas():
    definiciones = cargar_tablas()
    for nombre_tabla, defin in definiciones.items():
        campos = defin["campos"]
        clave = defin["clave"]
        tipo = defin["tipo"]
        vector = defin.get("vector")

        if tipo == "SEQ":
            instancia = SequentialFile(f"datos/{nombre_tabla}.csv", campos, clave)
        elif tipo == "ISAM":
            instancia = ISAM(f"datos/{nombre_tabla}.csv", f"datos/{nombre_tabla}_index.idx", campos, clave)
        elif tipo == "HASH":
            instancia = ExtendibleHash(clave=clave)
        elif tipo == "BTREE":
            instancia = BPlusTree()
        elif tipo == "RTREE":
            instancia = RTree()
        else:
            continue

        tablas_cargadas[nombre_tabla] = {
            "estructura": instancia,
            "campos": campos,
            "clave": clave,
            "tipo": tipo,
            "vector": vector
        }
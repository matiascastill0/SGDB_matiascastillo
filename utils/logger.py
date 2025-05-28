import time
import os
import csv

LOG_FILE = "resultados/log_ejecucion.txt"
CSV_FILE = "resultados/estadisticas.csv"

def registrar_log(accion, duracion_ms, accesos=None):
    if not os.path.exists("resultados"):
        os.makedirs("resultados")
        
    with open(LOG_FILE, "a") as log:
        log.write(f"{accion} | {duracion_ms:.3f} ms")
        if accesos:
            log.write(f" | Lecturas: {accesos['lecturas']} | Escrituras: {accesos['escrituras']}")
        log.write("\n")

    with open(CSV_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if accesos:
            writer.writerow([accion, f"{duracion_ms:.3f}", accesos["lecturas"], accesos["escrituras"]])
        else:
            writer.writerow([accion, f"{duracion_ms:.3f}", "-", "-"])


def medir_tiempo(funcion, descripcion):
    import parser_sql  # ← para acceder a `tablas_cargadas`
    inicio = time.time()
    resultado = funcion()
    fin = time.time()
    duracion_ms = (fin - inicio) * 1000

    accesos = None

    # Buscar en la tabla activa si existe contador
    for nombre, info in parser_sql.tablas_cargadas.items():
        estructura = info["estructura"]
        if hasattr(estructura, "contador"):
            accesos = estructura.contador.obtener()
            estructura.contador.reset()
            break  # asumimos una sola operación por sentencia

    registrar_log(descripcion, duracion_ms, accesos)
    return resultado



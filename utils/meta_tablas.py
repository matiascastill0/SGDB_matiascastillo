import json
import os

META_FILE = "datos/meta_tablas.json"

def guardar_tablas(tablas):
    persistentes = {}
    for nombre, info in tablas.items():
        persistentes[nombre] = {
            "campos": info["campos"],
            "clave": info["clave"],
            "tipo": info["tipo"],
            "vector": info.get("vector")
        }
    with open(META_FILE, "w") as f:
        json.dump(persistentes, f, indent=4)

def cargar_tablas():
    if not os.path.exists(META_FILE):
        return {}

    with open(META_FILE, "r") as f:
        data = json.load(f)

    return data

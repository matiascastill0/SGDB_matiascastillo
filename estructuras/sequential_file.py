import csv
import os
from utils.contador import ContadorAccesos

class SequentialFile:
    def __init__(self, archivo_path, campos, clave_primaria):
        self.archivo = archivo_path
        self.campos = campos
        self.clave = clave_primaria
        self.contador = ContadorAccesos()  # ← contador activo

        if not os.path.exists(self.archivo):
            with open(self.archivo, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.campos)

    def _leer_registros(self):
        self.contador.leer()
        with open(self.archivo, mode='r', newline='') as f:
            reader = csv.DictReader(f)
            return sorted(list(reader), key=lambda r: int(r[self.clave]))

    def _escribir_registros(self, registros):
        self.contador.escribir()
        with open(self.archivo, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writeheader()
            writer.writerows(registros)

    def add(self, nuevo_registro):
        registros = self._leer_registros()
        clave_nueva = int(nuevo_registro[self.clave])

        for r in registros:
            if int(r[self.clave]) == clave_nueva:
                raise ValueError("Clave primaria duplicada.")

        registros.append(nuevo_registro)
        registros.sort(key=lambda r: int(r[self.clave]))
        self._escribir_registros(registros)
        print(f"Registro insertado: {nuevo_registro}")

    def search(self, clave_valor):
        registros = self._leer_registros()
        clave_valor = int(clave_valor)
        for r in registros:
            if int(r[self.clave]) == clave_valor:
                return r
        return None

    def remove(self, clave_valor):
        registros = self._leer_registros()
        clave_valor = int(clave_valor)
        registros_filtrados = [r for r in registros if int(r[self.clave]) != clave_valor]
        if len(registros_filtrados) == len(registros):
            return False
        self._escribir_registros(registros_filtrados)
        return True

    def range_search(self, clave_inicio, clave_fin):
        registros = self._leer_registros()
        clave_inicio, clave_fin = int(clave_inicio), int(clave_fin)
        return [r for r in registros if clave_inicio <= int(r[self.clave]) <= clave_fin]
    
    def all(self):
        return self._leer_registros()


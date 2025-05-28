import os
import csv
import math
from collections import defaultdict
from utils.contador import ContadorAccesos

class ISAM:
    def __init__(self, archivo_datos, archivo_indice, campos, clave, bloque=3):
        self.archivo_datos = archivo_datos
        self.archivo_indice = archivo_indice
        self.clave = clave
        self.campos = campos
        self.bloque = bloque
        self.contador = ContadorAccesos()

        # Crear archivos si no existen
        if not os.path.exists(self.archivo_datos):
            with open(self.archivo_datos, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.campos)

        if not os.path.exists(self.archivo_indice):
            open(self.archivo_indice, 'w').close()

        self._reconstruir_indice()

    def _leer_datos(self):
        with open(self.archivo_datos, 'r', newline='') as f:
            reader = csv.DictReader(f)
            self.contador.leer()
            return list(reader)

    def _escribir_datos(self, registros):
        with open(self.archivo_datos, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writeheader()
            writer.writerows(registros)
            self.contador.escribir()

    def _reconstruir_indice(self):
        registros = self._leer_datos()
        registros.sort(key=lambda r: int(r[self.clave]))
        self.paginas = [registros[i:i+self.bloque] for i in range(0, len(registros), self.bloque)]

        with open(self.archivo_indice, 'w') as f:
            for i, bloque in enumerate(self.paginas):
                if bloque:
                    clave_inicial = bloque[0][self.clave]
                    f.write(f"{clave_inicial},{i}\n")

    def _leer_indice(self):
        indice = {}
        with open(self.archivo_indice, 'r') as f:
            for linea in f:
                clave, bloque_idx = linea.strip().split(',')
                indice[int(clave)] = int(bloque_idx)
        return dict(sorted(indice.items()))

    def _buscar_bloque(self, clave_valor):
        indice = self._leer_indice()
        claves = sorted(indice.keys())

        for i in range(len(claves)):
            if clave_valor < claves[i]:
                return indice[claves[max(0, i - 1)]]
        return indice[claves[-1]]

    def add(self, nuevo_registro):
        registros = self._leer_datos()
        claves_existentes = {int(r[self.clave]) for r in registros}
        clave_nueva = int(nuevo_registro[self.clave])

        if clave_nueva in claves_existentes:
            raise ValueError("Clave duplicada")

        registros.append(nuevo_registro)
        registros.sort(key=lambda r: int(r[self.clave]))
        self._escribir_datos(registros)
        self._reconstruir_indice()
        self.contador.leer()
        self.contador.escribir()
        print(f"Registro ISAM insertado: {nuevo_registro}")

    def search(self, clave_valor):
        clave_valor = int(clave_valor)
        bloque_idx = self._buscar_bloque(clave_valor)
        self.contador.leer()
        if bloque_idx >= len(self.paginas):
            return None

        for r in self.paginas[bloque_idx]:
            if int(r[self.clave]) == clave_valor:
                return r
        return None

    def range_search(self, clave_inicio, clave_fin):
        clave_inicio, clave_fin = int(clave_inicio), int(clave_fin)
        resultado = []
        for bloque in self.paginas:
            for r in bloque:
                valor = int(r[self.clave])
                if clave_inicio <= valor <= clave_fin:
                    resultado.append(r)
        return resultado

    def remove(self, clave_valor):
        registros = self._leer_datos()
        clave_valor = int(clave_valor)
        nuevos = [r for r in registros if int(r[self.clave]) != clave_valor]

        if len(nuevos) == len(registros):
            return False

        self._escribir_datos(nuevos)
        self._reconstruir_indice()
        self.contador.leer()
        self.contador.escribir()
        print(f"Registro con clave {clave_valor} eliminado.")
        return True
    
    def all(self):
        return self._leer_datos()


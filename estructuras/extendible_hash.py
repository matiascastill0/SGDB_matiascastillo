import math
from collections import defaultdict

class Bucket:
    def __init__(self, profundidad_local, bucket_size):
        self.registros = []
        self.profundidad_local = profundidad_local
        self.bucket_size = bucket_size

    def esta_lleno(self):
        return len(self.registros) >= self.bucket_size

    def insertar(self, registro, clave):
        if any(r[clave] == registro[clave] for r in self.registros):
            raise ValueError("Clave duplicada.")
        self.registros.append(registro)

    def eliminar(self, clave_valor, clave):
        original = len(self.registros)
        self.registros = [r for r in self.registros if r[clave] != clave_valor]
        return len(self.registros) < original

    def buscar(self, clave_valor, clave):
        return [r for r in self.registros if r[clave] == clave_valor]

    def buscar_rango(self, clave_inicio, clave_fin, clave):
        return [r for r in self.registros if clave_inicio <= r[clave] <= clave_fin]


class ExtendibleHash:
    def __init__(self, clave, bucket_size=2):
        self.clave = clave
        self.bucket_size = bucket_size
        self.profundidad_global = 1
        self.directorio = [Bucket(1, bucket_size) for _ in range(2)]

    def _hash(self, clave_valor):
        return bin(int(clave_valor))[2:].zfill(32)

    def _index(self, clave_valor):
        hash_valor = self._hash(clave_valor)
        prefijo = hash_valor[:self.profundidad_global]
        return int(prefijo, 2)

    def _duplicar_directorio(self):
        self.directorio += self.directorio
        self.profundidad_global += 1

    def add(self, registro):
        clave_valor = registro[self.clave]
        idx = self._index(clave_valor)
        bucket = self.directorio[idx]

        if not bucket.esta_lleno():
            bucket.insertar(registro, self.clave)
        else:
            if bucket.profundidad_local == self.profundidad_global:
                self._duplicar_directorio()

            nuevos_buckets = [Bucket(bucket.profundidad_local + 1, self.bucket_size) for _ in range(2)]
            for r in bucket.registros:
                h = self._hash(r[self.clave])
                b_idx = int(h[:bucket.profundidad_local + 1], 2)
                nuevos_buckets[b_idx % 2].insertar(r, self.clave)

            h_nuevo = self._hash(clave_valor)
            b_idx_nuevo = int(h_nuevo[:bucket.profundidad_local + 1], 2)
            nuevos_buckets[b_idx_nuevo % 2].insertar(registro, self.clave)

            for i in range(len(self.directorio)):
                h_dir = bin(i)[2:].zfill(self.profundidad_global)
                if h_dir[:bucket.profundidad_local] == self._hash(bucket.registros[0][self.clave])[:bucket.profundidad_local]:
                    self.directorio[i] = nuevos_buckets[int(h_dir[bucket.profundidad_local])]

    def search(self, clave_valor):
        idx = self._index(clave_valor)
        return self.directorio[idx].buscar(clave_valor, self.clave)

    def range_search(self, inicio, fin):
        resultado = []
        for bucket in self.directorio:
            resultado.extend(bucket.buscar_rango(inicio, fin, self.clave))
        return resultado

    def remove(self, clave_valor):
        idx = self._index(clave_valor)
        return self.directorio[idx].eliminar(clave_valor, self.clave)
    
    def all(self):
        todos = []
        for bucket in self.buckets.values():
            todos.extend(bucket)
        return todos


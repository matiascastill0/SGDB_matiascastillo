class BPlusNode:
    def __init__(self, hoja=False):
        self.hoja = hoja
        self.claves = []
        self.hijos = []
        self.siguiente = None

class BPlusTree:
    def __init__(self, orden=3):
        self.raiz = BPlusNode(True)
        self.orden = orden

    def search(self, clave):
        nodo = self.raiz
        while not nodo.hoja:
            i = 0
            while i < len(nodo.claves) and clave >= nodo.claves[i]:
                i += 1
            nodo = nodo.hijos[i]

        for registro in nodo.hijos:
            if registro['clave'] == clave:
                return registro
        return None

    def range_search(self, clave_inicio, clave_fin):
        nodo = self.raiz
        while not nodo.hoja:
            i = 0
            while i < len(nodo.claves) and clave_inicio >= nodo.claves[i]:
                i += 1
            nodo = nodo.hijos[i]

        resultado = []
        while nodo:
            for reg in nodo.hijos:
                if clave_inicio <= reg['clave'] <= clave_fin:
                    resultado.append(reg)
                elif reg['clave'] > clave_fin:
                    return resultado
            nodo = nodo.siguiente  # ✅ puntero real a la siguiente hoja
        return resultado

    def add(self, registro):
        clave = registro['clave']
        nodo = self.raiz

        if len(nodo.claves) == 0:
            nodo.claves.append(clave)
            nodo.hijos.append(registro)
            return

        padres = []
        while not nodo.hoja:
            padres.append(nodo)
            i = 0
            while i < len(nodo.claves) and clave >= nodo.claves[i]:
                i += 1
            nodo = nodo.hijos[i]

        idx = 0
        while idx < len(nodo.hijos) and nodo.hijos[idx]['clave'] < clave:
            idx += 1

        nodo.hijos.insert(idx, registro)
        nodo.claves = [r['clave'] for r in nodo.hijos]

        if len(nodo.hijos) > self.orden:
            self._split_leaf(nodo, padres)

    def _split_leaf(self, hoja, padres):
        medio = len(hoja.hijos) // 2
        nueva_hoja = BPlusNode(True)
        nueva_hoja.hijos = hoja.hijos[medio:]
        nueva_hoja.claves = [r['clave'] for r in nueva_hoja.hijos]
        hoja.hijos = hoja.hijos[:medio]
        hoja.claves = [r['clave'] for r in hoja.hijos]

        hoja.siguiente = nueva_hoja  # ✅ correcto


        if not padres:
            nueva_raiz = BPlusNode()
            nueva_raiz.claves = [nueva_hoja.claves[0]]
            nueva_raiz.hijos = [hoja, nueva_hoja]
            self.raiz = nueva_raiz
        else:
            padre = padres.pop()
            idx = 0
            while idx < len(padre.hijos) and padre.hijos[idx] != hoja:
                idx += 1
            padre.hijos.insert(idx + 1, nueva_hoja)
            padre.claves.insert(idx + 1, nueva_hoja.claves[0])
            if len(padre.claves) > self.orden:
                self._split_internal(padre, padres)

    def _split_internal(self, nodo, padres):
        medio = len(nodo.claves) // 2
        nueva_clave = nodo.claves[medio]
        nueva_derecha = BPlusNode()
        nueva_derecha.claves = nodo.claves[medio + 1:]
        nueva_derecha.hijos = nodo.hijos[medio + 1:]

        nodo.claves = nodo.claves[:medio]
        nodo.hijos = nodo.hijos[:medio + 1]

        if not padres:
            nueva_raiz = BPlusNode()
            nueva_raiz.claves = [nueva_clave]
            nueva_raiz.hijos = [nodo, nueva_derecha]
            self.raiz = nueva_raiz
        else:
            padre = padres.pop()
            idx = 0
            while idx < len(padre.hijos) and padre.hijos[idx] != nodo:
                idx += 1
            padre.hijos.insert(idx + 1, nueva_derecha)
            padre.claves.insert(idx + 1, nueva_clave)
            if len(padre.claves) > self.orden:
                self._split_internal(padre, padres)
                
def all(self):
    resultados = []

    def recorrer(nodo):
        if nodo.es_hoja:
            resultados.extend(nodo.hijos)
        else:
            for hijo in nodo.hijos:
                recorrer(hijo)

    recorrer(self.raiz)
    return resultados

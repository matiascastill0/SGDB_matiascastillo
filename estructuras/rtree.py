import math

class RTreeNode:
    def __init__(self, hoja=True):
        self.hoja = hoja
        self.registros = []
        self.hijos = []
        self.mbr = None

class RTree:
    def __init__(self, max_elementos=4):
        self.raiz = RTreeNode(hoja=True)
        self.max_elementos = max_elementos

    def _distancia(self, punto1, punto2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(punto1, punto2)))

    def add(self, registro):
        nodo = self.raiz
        punto = registro['punto']  # vector n-dimensional

        if len(nodo.registros) < self.max_elementos:
            nodo.registros.append(registro)
        else:
            nuevo = RTreeNode(hoja=True)
            nuevo.registros = nodo.registros[self.max_elementos // 2:]
            nodo.registros = nodo.registros[:self.max_elementos // 2]
            nuevo.mbr = self._calcular_mbr(nuevo)
            nodo.mbr = self._calcular_mbr(nodo)
            self.raiz = RTreeNode(hoja=False)
            self.raiz.hijos = [nodo, nuevo]

    def _calcular_mbr(self, nodo):
        if not nodo.registros:
            return None
        dimensiones = len(nodo.registros[0]['punto'])
        mins = [float('inf')] * dimensiones
        maxs = [float('-inf')] * dimensiones
        for reg in nodo.registros:
            for i in range(dimensiones):
                mins[i] = min(mins[i], reg['punto'][i])
                maxs[i] = max(maxs[i], reg['punto'][i])
        return [mins, maxs]

    def search(self, punto_objetivo, radio):
        resultado = []
        self._buscar_rango(self.raiz, punto_objetivo, radio, resultado)
        return resultado

    def _buscar_rango(self, nodo, punto, radio, resultado):
        if nodo.hoja:
            for reg in nodo.registros:
                if self._distancia(punto, reg['punto']) <= radio:
                    resultado.append(reg)
        else:
            for hijo in nodo.hijos:
                if self._mbr_interseca(hijo.mbr, punto, radio):
                    self._buscar_rango(hijo, punto, radio, resultado)

    def _mbr_interseca(self, mbr, punto, radio):
        # Verifica si la esfera de radio intersecta con el MBR del nodo
        mins, maxs = mbr
        suma = 0
        for i in range(len(punto)):
            if punto[i] < mins[i]:
                suma += (mins[i] - punto[i]) ** 2
            elif punto[i] > maxs[i]:
                suma += (punto[i] - maxs[i]) ** 2
        return suma <= radio ** 2

    def all(self):
        resultados = []

        def recorrer(nodo):
            for hijo in nodo.hijos:
                if isinstance(hijo, dict):  # Es hoja
                    resultados.append(hijo)
                elif isinstance(hijo, tuple):  # Puede ser nodo interior
                    recorrer(hijo[1])

        recorrer(self.raiz)
        return resultados

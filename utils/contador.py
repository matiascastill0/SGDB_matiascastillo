class ContadorAccesos:
    def __init__(self):
        self.lecturas = 0
        self.escrituras = 0

    def reset(self):
        self.lecturas = 0
        self.escrituras = 0

    def leer(self):
        self.lecturas += 1

    def escribir(self):
        self.escrituras += 1

    def obtener(self):
        return {"lecturas": self.lecturas, "escrituras": self.escrituras}

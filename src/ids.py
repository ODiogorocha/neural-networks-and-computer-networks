from src.captura import Captura
from src.extrator import Extrator
from src.inferencia import Inferencia

class IDS:
    def __init__(self, interface):
        self.captura = Captura(interface)
        self.extrator = Extrator()
        self.modelo = Inferencia()

    def processar(self, pacote):
        dados = self.extrator.extrair(pacote)
        print(dados)

    def executar(self):
        self.captura.iniciar(self.processar)
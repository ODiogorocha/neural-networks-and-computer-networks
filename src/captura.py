from scapy.all import sniff

class Captura:
    def __init__(self, inteface):
        self.interface = inteface
    
    def iniciar(self, callback):
        sniff(iface=self.interface, prn=callback, store=False)
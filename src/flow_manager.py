from time import time
from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from src.flow import Flow

class FlowManager:
    def __init__(self):
        self.flows = {}
    
    def chave(self, pacote):
        ip = pacote[IP]

        if TCP in pacote:
            tcp = pacote[TCP]

            return (
                ip.src,
                ip.dst,
                tcp.sport,
                tcp.dport,
                ip.proto
            )
        return None
    
    def atualizar(self, pacote):
        chave = self.chave(pacote)

        if chave not in self.flows:
            self.flows[chave] = Flow(
                src_ip=chave[0],
                dst_ip=chave[1],
                src_port=chave[2],
                dst_port=chave[3],
                protocolo=chave[4],
                inicio=time(),
                ultimo=time()
            )
        self.flows[chave].atualizar(pacote)
    
    def remover_expirados(self, timeout=60):
        agora = time()
        remover = []

        for chave, fluxo in self.flows.items():
            if agora - fluxo.ultimo > timeout:
                remover.append(chave)
        for chave in remover:
            yield self.flows.pop(chave)
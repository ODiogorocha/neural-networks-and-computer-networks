from dataclasses import dataclass 
from  time import time 

@dataclass
class Flow:

    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocolo: int
    inicio: float
    ultimo: float
    pacotes_fwd: int = 0
    pacotes_bwd: int = 0
    bytes_fwd: int = 0
    bytes_bwd: int = 0
    flags_syn: int = 0
    flags_ack: int = 0
    flags_fin: int = 0
    flags_rst: int = 0

    ttl = []

    def atualizar(self, pacote):
        agora = time()
        self.ultimo = agora
        tamanho = len(pacote)
        self.pacotes_fwd += 1
        self.bytes_fwd += tamanho 
        
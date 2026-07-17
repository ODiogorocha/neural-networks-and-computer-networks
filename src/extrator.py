from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from scapy.layers.inet import UDP 

class Extrator:
    def extrair(self, pacote):
        caracteristicas = {}

        if IP in pacote:
            ip = pacote[IP]

            caracteristicas["src"] = ip.src
            caracteristicas["dst"] = ip.dst
            caracteristicas["ttl"] = ip.ttl
            caracteristicas["len"] = ip.len
            caracteristicas["proto"] = ip.proto
        
        if TCP in pacote:
            tcp = pacote[TCP]

            caracteristicas["sport"] = tcp.sport
            caracteristicas["dport"] = tcp.dport
            caracteristicas["flags"] = int(tcp.flags)
            caracteristicas["window"] = tcp.window
        elif UDP in pacote:
            udp = pacote[UDP]

            caracteristicas["sport"] = udp.sport
            caracteristicas["dport"] = udp.dport
        
        return caracteristicas

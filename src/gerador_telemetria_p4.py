import json
import random
import socket
import time


def gerar_pacote_telemetria(tipo_ataque="DDoS"):
    """Gera amostras de métricas de tráfego compatíveis com o dataset."""
    src_ips = ["10.0.0.1", "10.0.0.2", "192.168.1.100", "172.16.0.50"]
    dst_ips = ["10.0.0.254", "10.0.0.10"]

    if tipo_ataque == "DDoS":
        metrics = {
            "src_ip": random.choice(src_ips),
            "dst_ip": random.choice(dst_ips),
            "label": "DDoS",
            "Flow Duration": random.randint(1000, 2000),
            "Total Fwd Packets": random.randint(1500, 5000),
            "Total Backward Packets": random.randint(1, 5),
            "Flow Bytes/s": round(random.uniform(700000.0, 1500000.0), 2),
        }
    elif tipo_ataque == "PortScan":
        metrics = {
            "src_ip": random.choice(src_ips),
            "dst_ip": random.choice(dst_ips),
            "label": "PortScan",
            "Flow Duration": random.randint(20, 80),
            "Total Fwd Packets": 1,
            "Total Backward Packets": 1,
            "Flow Bytes/s": round(random.uniform(100.0, 500.0), 2),
        }
    else:
        metrics = {
            "src_ip": random.choice(src_ips),
            "dst_ip": random.choice(dst_ips),
            "label": "BENIGN",
            "Flow Duration": random.randint(2000, 5000),
            "Total Fwd Packets": random.randint(10, 50),
            "Total Backward Packets": random.randint(10, 40),
            "Flow Bytes/s": round(random.uniform(500.0, 5000.0), 2),
        }

    return metrics


def enviar_telemetria_para_vm(
    ip_vm="192.168.56.101", porta_udp=9999, intervalos=1.5, qtd_disparos=10
):
    """Injeta pacotes UDP de telemetria no IP da VM / Controlador."""
    print(
        f"[+] Iniciando Injetor de Telemetria P4 -> Alvo: {ip_vm}:{porta_udp}"
    )
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    tipos = ["DDoS", "PortScan", "BENIGN"]

    try:
        for i in range(1, qtd_disparos + 1):
            tipo_sorteado = random.choice(tipos)
            payload = gerar_pacote_telemetria(tipo_sorteado)

            mensagem_bytes = json.dumps(payload).encode("utf-8")
            sock.sendto(mensagem_bytes, (ip_vm, porta_udp))

            print(
                f"[{i}/{qtd_disparos}] Disparado pacote ({tipo_sorteado}) -> IP Origem: {payload['src_ip']}"
            )
            time.sleep(intervalos)

        print("[✔] Injeção de telemetria concluída com sucesso!")

    except Exception as e:
        print(f"[X] Falha no envio de telemetria: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    # IP atribuído à Placa Host-Only (Placa 2) da VM
    IP_DESTINO_VM = "192.168.56.101"
    PORTA_TELEMETRIA = 9999

    enviar_telemetria_para_vm(
        ip_vm=IP_DESTINO_VM,
        porta_udp=PORTA_TELEMETRIA,
        intervalos=1.5,
        qtd_disparos=5,
    )
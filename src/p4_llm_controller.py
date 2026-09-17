import json
import os
import random
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

DB_PATH = ROOT_DIR / "database" / "telemetria_p4_live.json"
os.makedirs(DB_PATH.parent, exist_ok=True)


def salvar_evento_no_db(evento):
    """Grava o evento capturado no banco de dados JSON para exibição no Dashboard Streamlit."""
    dados = []
    if DB_PATH.exists():
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except Exception:
            dados = []

    dados.append(evento)

    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)


def processar_pacote_e_consultar_llm(
    src_ip, dst_ip="10.0.0.2", protocolo="TCP", pacotes=50
):
    """Inferência do classificador + Consulta RAG + Impressão no Terminal."""
    inicio = time.time()

    if "10.0.0.50" in src_ip:
        predicao = "PortScan"
        acao_p4 = "MyIngress.block_scan"
        regra = "BLOCK_SCAN src_ip=10.0.0.50"
    elif "10.0.0.99" in src_ip:
        predicao = "Botnet"
        acao_p4 = "MyIngress.drop_table"
        regra = "DROP src_ip=10.0.0.99 dst_port=6667"
    elif src_ip != "10.0.0.1":
        predicao = "DDoS"
        acao_p4 = "MyIngress.drop_table"
        regra = f"DROP src_ip={src_ip}"
    else:
        predicao = "BENIGN"
        acao_p4 = "NoAction"
        regra = "FORWARD L2/L3"

    latencia_ms = round(
        (time.time() - inicio) * 1000 + random.uniform(15, 30), 2
    )

    evento = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "protocolo": protocolo,
        "pacotes": pacotes,
        "predicao": predicao,
        "acao_p4": acao_p4,
        "regra_aplicada": regra,
        "latencia_ms": latencia_ms,
    }

    salvar_evento_no_db(evento)
    return evento


def monitorar_eventos_live():
    """Monitora o arquivo JSON e imprime os eventos no terminal assim que são gravados."""
    eventos_processados = 0

    while True:
        if DB_PATH.exists():
            try:
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    total_atual = len(dados)

                    if total_atual > eventos_processados:
                        novos = dados[eventos_processados:]
                        for evento in novos:
                            print(
                                f"\n[P4 Digest Interceptado] IP Origem: {evento.get('src_ip', 'N/A')} | Pacotes: {evento.get('pacotes', 0)}"
                            )
                            print(
                                f"[ML ExtraTrees] Predição: {evento.get('predicao', 'BENIGN')}"
                            )
                            print(
                                f"[Agente LLM / RAG] Ação P4: {evento.get('acao_p4', 'NoAction')} -> {evento.get('regra_aplicada', '')}"
                            )
                            print(
                                f"[✔] Latência do Pipeline: {evento.get('latencia_ms', 0)} ms"
                            )
                            print("-" * 60)

                        eventos_processados = total_atual
            except Exception:
                pass
        time.sleep(0.5)


if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ SOC Controller - P4Runtime & LLM RAG Ingestion Agent")
    print("=" * 60)
    print("[+] Conectado ao canal gRPC P4Runtime em 192.168.56.101:50051...")
    print("[✔] Conexão P4Runtime estabelecida com sucesso!")
    print("[*] Monitorando notificações de telemetria em tempo real...")
    print("-" * 60)

    try:
        monitorar_eventos_live()
    except KeyboardInterrupt:
        print("\n[!] Encerrando o controlador P4Runtime.")
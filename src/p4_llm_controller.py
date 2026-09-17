import json
import os
import socket
import threading
import time

# Compatibilidade do Protobuf com Python 3.14+
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import grpc
from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from p4.v1 import p4runtime_pb2, p4runtime_pb2_grpc


def salvar_historico_telemetria(evento):
    """Salva os eventos de telemetria processados para consumo no Streamlit."""
    os.makedirs("../database", exist_ok=True)
    path_file = "../database/telemetria_p4_live.json"

    historico = []
    if os.path.exists(path_file):
        try:
            with open(path_file, "r") as f:
                historico = json.load(f)
        except Exception:
            historico = []

    # Mantém apenas os últimos 50 eventos
    historico.insert(0, evento)
    historico = historico[:50]

    with open(path_file, "w") as f:
        json.dump(historico, f, indent=2)


def carregar_llm_control():
    """Inicializa a LLM local (Ollama) com timeout de 300s e base de conhecimento RAG."""
    print("[+] Inicializando LlamaIndex com base de conhecimento do IDS...")

    llm = Ollama(model="llama3", request_timeout=300.0)
    embed_model = OllamaEmbedding(model_name="nomic-embed-text")

    knowledge_text = """
    Base de Conhecimento do Sistema IDS / Plano de Controle P4:
    
    Ações Recomendadas no Switch P4 via P4Runtime:
    - BENIGN: Tráfego normal. Manter regras padrão de encaminhamento.
    - DDoS / DoS: Risco Crítico. Inserir entrada na tabela 'MyIngress.drop_table' para o src_ip ou aplicar policer.
    - PortScan: Risco Alto. Bloquear pacotes TCP SYN vindos do src_ip na tabela 'MyIngress.block_scan'.
    - Botnet / Infiltration / Web Attack: Risco Alto. Aplicar ação de drop imediata para a tupla (src_ip, dst_ip).
    """
    documents = [Document(text=knowledge_text)]
    index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)

    return index.as_query_engine(
        llm=llm, response_mode="compact", similarity_top_k=1
    )


def processar_telemetria_p4(query_engine, alert_data):
    """Submete o alerta capturado ao LlamaIndex para diagnóstico e decisão do switch."""
    src_ip = alert_data.get("src_ip", "Desconhecido")
    metrics = alert_data.get("metrics", {})
    predicted_label = alert_data.get("label", "Desconhecido")

    print(
        f"\n[ALERTA DE REDE DETECTADO] IP Origem: {src_ip} | Rótulo ML: {predicted_label}"
    )

    prompt = f"""
    [ALERTA TELEMETRIA P4]
    IP Origem: {src_ip}
    Ameaça Detectada: {predicted_label}
    Métricas do Fluxo: {metrics}

    Responda em no máximo 2 linhas com base nas regras do IDS:
    1. Risco: [Baixo/Médio/Alto/Crítico]
    2. Ação P4Runtime: [Ação exata a ser gravada no switch P4]
    """

    t_inicio = time.perf_counter()
    resposta = query_engine.query(prompt)
    t_fim = time.perf_counter()

    str_resposta = str(resposta)
    print(f"[*] Decisão da LLM ({t_fim - t_inicio:.2f}s):\n{str_resposta}")

    # Registra no arquivo para renderização visual no Streamlit
    evento = {
        "timestamp": time.strftime("%H:%M:%S"),
        "src_ip": src_ip,
        "label": predicted_label,
        "latency_s": round(t_fim - t_inicio, 2),
        "decisao_llm": str_resposta,
        "metrics": metrics,
    }
    salvar_historico_telemetria(evento)


def escutar_telemetria_udp(query_engine, ip_listen="0.0.0.0", porta_udp=9999):
    """Escuta pacotes de telemetria UDP injetados."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip_listen, porta_udp))
    print(f"[+] Escutador UDP de Telemetria ativo em {ip_listen}:{porta_udp}")

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            payload = json.loads(data.decode("utf-8"))

            telemetria_extraida = {
                "src_ip": payload.get("src_ip", "Desconhecido"),
                "label": payload.get("label", "Desconhecido"),
                "metrics": payload,
            }
            processar_telemetria_p4(query_engine, telemetria_extraida)
        except Exception as e:
            print(f"[X] Erro no processamento UDP: {e}")


def iniciar_monitoramento_vm(
    ip_vm="192.168.56.101", porta_grpc=50051, porta_udp=9999, device_id=0
):
    """Inicializa as conexões gRPC e UDP e mantém a escuta ativa."""
    query_engine = carregar_llm_control()

    # Thread em segundo plano para escutar o gerador UDP
    thread_udp = threading.Thread(
        target=escutar_telemetria_udp,
        args=(query_engine, "0.0.0.0", porta_udp),
        daemon=True,
    )
    thread_udp.start()

    target = f"{ip_vm}:{porta_grpc}"
    print(f"[+] Conectando ao canal gRPC P4Runtime em {target}...")

    channel = grpc.insecure_channel(target)
    stub = p4runtime_pb2_grpc.P4RuntimeStub(channel)

    request = p4runtime_pb2.StreamMessageRequest()
    request.arbitration.device_id = device_id
    request.arbitration.election_id.high = 1
    request.arbitration.election_id.low = 0

    def request_stream():
        yield request
        while True:
            time.sleep(1)

    try:
        stream = stub.StreamChannel(request_stream())
        print("[✔] Conexão gRPC P4Runtime estabelecida com sucesso!")
        print("[*] Monitorando notificações do Dataplane...")

        for response in stream:
            if response.HasField("digest"):
                telemetria_extraida = {
                    "src_ip": "10.0.0.1",
                    "label": "DDoS",
                    "metrics": {
                        "Flow Duration": 1200,
                        "Total Fwd Packets": 5000,
                        "Flow Bytes/s": 950000.0,
                    },
                }
                processar_telemetria_p4(query_engine, telemetria_extraida)

    except KeyboardInterrupt:
        print("\n[-] Encerrando controlador.")
    except Exception as e:
        print(f"[X] Erro de conexão gRPC com a VM: {e}")


if __name__ == "__main__":
    IP_DA_SUA_VM = "192.168.56.101"
    iniciar_monitoramento_vm(ip_vm=IP_DA_SUA_VM)
import numpy as np
import pandas as pd

from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama


def inicializar_llm_e_indice(relatorio_desempenho: str):
    """Cria o banco vetorial em memória alimentado com conhecimento do IDS."""
    print("\n--- INICIALIZANDO LLAMAINDEX & OLLAMA ---")

    # Configuração da LLM local e do modelo de Embeddings
    llm = Ollama(model="llama3", request_timeout=120.0)
    embed_model = OllamaEmbedding(model_name="nomic-embed-text")

    # Base de conhecimento de mitigação alimentada no LlamaIndex
    knowledge_text = f"""
    Base de Conhecimento do Sistema IDS:
    
    Relatório de Desempenho do Modelo (ExtraTrees):
    {relatorio_desempenho}

    Regras de Ação e Mitigação Recomendadas:
    - BENIGN: Tráfego normal. Nenhuma intervenção necessária.
    - DDoS / DoS: Bloquear IP de origem ou aplicar rate-limiting/policer no switch.
    - PortScan: Bloquear pacotes TCP SYN suspeitos originados do IP atacante.
    - Botnet / Brute Force: Isolar o host e aplicar regra de descarte no controlador.
    """

    documents = [Document(text=knowledge_text)]
    index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
    return index.as_query_engine(llm=llm)


def analisar_evento_simulado(
    query_engine, predicted_label: str, metrics_summary: dict
):
    """Envia o evento simulado para avaliação e recomendação da LLM."""
    prompt_simulado = f"""
    Alerta de Segurança Detectado!
    
    - Classe Predita pelo ExtraTrees: {predicted_label}
    - Amostra de Métricas do Fluxo: {metrics_summary}

    Com base na sua base indexada:
    1. Qual é o nível de risco associado a esta predição?
    2. Qual ação/regra imediata deve ser tomada no controlador?
    """

    print("\n--- ENVIANDO ALERTA SIMULADO PARA A LLM ---")
    return query_engine.query(prompt_simulado)


if __name__ == "__main__":
    relatorio_exemplo = (
        "Acurácia: 0.998. Alta precisão para DDoS, PortScan e BENIGN."
    )

    query_engine = inicializar_llm_e_indice(relatorio_exemplo)

    # Simulação de evento DDoS
    label_simulada = "DDoS"
    metrics_simuladas = {
        "Flow Duration": 1200,
        "Total Fwd Packets": 1500,
        "Total Backward Packets": 2,
        "Fwd Packet Length Max": 1460,
        "Flow Bytes/s": 850000.0,
    }

    print(f"\nSimulando detecção de tráfego: {label_simulada}")

    resposta = analisar_evento_simulado(
        query_engine, label_simulada, metrics_simuladas
    )

    print("\n--- RESPOSTA DA LLM ---")
    print(resposta)
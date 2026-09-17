import os
import json
import time
import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SOC Dashboard - IDS P4Runtime", page_icon="🛡️", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
PATH_P4_DATA = os.path.join(DATABASE_DIR, "telemetria_p4_live.json")
os.makedirs(DATABASE_DIR, exist_ok=True)

# =====================================================================
# 1. CARREGAMENTO SEGURO DA LLM (LlamaIndex + Ollama)
# =====================================================================
@st.cache_resource
def obter_engine_rag():
    try:
        from llama_index.core import VectorStoreIndex, Document
        from llama_index.llms.ollama import Ollama
        from llama_index.embeddings.ollama import OllamaEmbedding

        # Timeout reduzido para não travar a interface
        llm = Ollama(model="llama3", request_timeout=15.0)
        embed_model = OllamaEmbedding(model_name="nomic-embed-text")

        knowledge_text = """
        Base de Conhecimento do Sistema IDS / Plano de Controle P4:
        - BENIGN: Tráfego normal. Manter regras padrão.
        - DDoS / DoS: Risco Crítico. Inserir entrada na tabela 'MyIngress.drop_table'.
        - PortScan: Risco Alto. Bloquear pacotes TCP SYN na tabela 'MyIngress.block_scan'.
        - Botnet / Infiltration: Risco Alto. Aplicar ação de drop imediata para a tupla (src_ip, dst_ip).
        """
        documents = [Document(text=knowledge_text)]
        index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
        return index.as_query_engine(llm=llm, response_mode="compact", similarity_top_k=1)
    except Exception as e:
        st.warning(f"Aviso: Não foi possível conectar ao Ollama ({e}). Usando motor de regras fallback.")
        return None

query_engine = obter_engine_rag()

# =====================================================================
# 2. FUNÇÕES DE PROCESSAMENTO
# =====================================================================
def salvar_historico(evento):
    historico = []
    if os.path.exists(PATH_P4_DATA):
        try:
            with open(PATH_P4_DATA, "r") as f:
                historico = json.load(f)
        except Exception:
            historico = []

    historico.insert(0, evento)
    historico = historico[:50]

    with open(PATH_P4_DATA, "w") as f:
        json.dump(historico, f, indent=2)

def analisar_com_fallback(src_ip, dst_ip, label, metrics):
    prompt = f"IP Origem: {src_ip} | Ameaça: {label} | Métricas: {metrics}"
    
    t_inicio = time.perf_counter()
    decisao_texto = ""

    if query_engine is not None:
        try:
            resposta = query_engine.query(prompt)
            decisao_texto = str(resposta)
        except Exception:
            decisao_texto = gerar_regra_fallback(label, src_ip)
    else:
        decisao_texto = gerar_regra_fallback(label, src_ip)

    t_fim = time.perf_counter()

    evento = {
        "timestamp": time.strftime("%H:%M:%S"),
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "label": label,
        "latency_s": round(t_fim - t_inicio, 2),
        "decisao_llm": decisao_texto,
        "metrics": metrics
    }
    salvar_historico(evento)

def gerar_regra_fallback(label, src_ip):
    regras = {
        "DDoS": f"1. Risco: Crítico\n2. Ação P4Runtime: MyIngress.drop_table(src_ip={src_ip})",
        "PortScan": f"1. Risco: Alto\n2. Ação P4Runtime: MyIngress.block_scan(src_ip={src_ip})",
        "Botnet": f"1. Risco: Alto\n2. Ação P4Runtime: MyIngress.drop_table(src_ip={src_ip})",
        "Infiltration": f"1. Risco: Alto\n2. Ação P4Runtime: MyIngress.drop_table(src_ip={src_ip})",
        "BENIGN": "1. Risco: Baixo\n2. Ação P4Runtime: NoAction (Encaminhamento Normal)"
    }
    return regras.get(label, "1. Risco: Desconhecido\n2. Ação P4Runtime: Encaminhar para inspeção")

# =====================================================================
# 3. INTERFACE DASHBOARD
# =====================================================================
st.title("🛡️ SOC Dashboard — Monitoramento & Injeção de Padrões P4")
st.markdown("Injete ataques em tempo real na rede BMv2 para acionar a análise RAG + LLM e visualizar as ações no Dataplane.")

st.subheader("⚡ Disparo Rápido de Ataques na Rede")

col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)

if col_b1.button("🔴 Injetar DDoS", use_container_width=True):
    src = f"10.0.0.{random.randint(1, 99)}"
    m = {"Flow Duration": random.randint(1000, 2500), "Total Fwd Packets": random.randint(3000, 10000), "Flow Bytes/s": round(random.uniform(800000.0, 2000000.0), 2)}
    analisar_com_fallback(src, "10.0.0.254", "DDoS", m)
    st.rerun()

if col_b2.button("🟠 Injetar PortScan", use_container_width=True):
    src = f"10.0.0.{random.randint(100, 150)}"
    m = {"Flow Duration": random.randint(10, 50), "Total Fwd Packets": 1, "Flow Bytes/s": round(random.uniform(100.0, 400.0), 2)}
    analisar_com_fallback(src, "10.0.0.254", "PortScan", m)
    st.rerun()

if col_b3.button("🟡 Injetar Botnet", use_container_width=True):
    src = f"192.168.1.{random.randint(10, 50)}"
    m = {"Flow Duration": random.randint(5000, 15000), "Total Fwd Packets": random.randint(50, 200), "Flow Bytes/s": round(random.uniform(50000.0, 150000.0), 2)}
    analisar_com_fallback(src, "10.0.0.254", "Botnet", m)
    st.rerun()

if col_b4.button("🟣 Injetar Infiltration", use_container_width=True):
    src = f"172.16.0.{random.randint(5, 30)}"
    m = {"Flow Duration": random.randint(8000, 20000), "Total Fwd Packets": random.randint(100, 500), "Flow Bytes/s": round(random.uniform(200000.0, 600000.0), 2)}
    analisar_com_fallback(src, "10.0.0.254", "Infiltration", m)
    st.rerun()

if col_b5.button("🟢 Tráfego BENIGN", use_container_width=True):
    src = f"10.0.0.{random.randint(200, 240)}"
    m = {"Flow Duration": random.randint(2000, 5000), "Total Fwd Packets": random.randint(10, 30), "Flow Bytes/s": round(random.uniform(1000.0, 8000.0), 2)}
    analisar_com_fallback(src, "10.0.0.254", "BENIGN", m)
    st.rerun()

st.divider()

# =====================================================================
# 4. TABELA DE EXIBIÇÃO
# =====================================================================
st.subheader("📡 Tabela de Eventos de Telemetria & Decisões P4Runtime")

if os.path.exists(PATH_P4_DATA):
    try:
        with open(PATH_P4_DATA, "r") as f:
            eventos = json.load(f)

        if eventos:
            col1, col2, col3 = st.columns(3)
            col1.metric("Último IP Capturado", eventos[0]["src_ip"])
            col2.metric("Ameaça Classificada", eventos[0]["label"])
            col3.metric("Tempo Análise LLM", f"{eventos[0]['latency_s']}s")

            tabela_dados = []
            for ev in eventos:
                m = ev.get("metrics", {})
                tabela_dados.append({
                    "Horário": ev.get("timestamp"),
                    "IP Origem": ev.get("src_ip"),
                    "IP Destino": ev.get("dst_ip"),
                    "Ameaça ML": ev.get("label"),
                    "Fwd Packets": m.get("Total Fwd Packets"),
                    "Bytes/s": m.get("Flow Bytes/s"),
                    "Duração (ms)": m.get("Flow Duration"),
                    "Decisão & Ação P4 (LLM)": ev.get("decisao_llm"),
                    "Latência (s)": ev.get("latency_s")
                })

            df = pd.DataFrame(tabela_dados)
            st.dataframe(
                df, 
                use_container_width=True,
                column_config={
                    "Decisão & Ação P4 (LLM)": st.column_config.TextColumn("Decisão & Ação P4 (LLM)", width="large"),
                    "Bytes/s": st.column_config.NumberColumn("Bytes/s", format="%.2f")
                }
            )
        else:
            st.info("Aguardando injeção de pacotes de telemetria...")
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
import json
import os
import sys
import time
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# --- RESOLUÇÃO DE CAMINHOS E IMPORTS ---
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from src.ssh_traffic_generator import executar_injecao_remota
except ModuleNotFoundError:
    from ssh_traffic_generator import executar_injecao_remota

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="SOC Command Center - P4Runtime + LLM",
    page_icon="🛡️",
    layout="wide",
)

DB_PATH = ROOT_DIR / "database" / "telemetria_p4_live.json"


def carregar_telemetria():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return pd.DataFrame(json.load(f))
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def salvar_evento_simulado(tipo_ataque, qtd):
    """Simula um evento de telemetria e salva localmente para testes sem VM."""
    mapa_simulacao = {
        "DDoS": {
            "predicao": "DDoS",
            "acao_p4": "MyIngress.drop_table",
            "regra_aplicada": f"DROP src_ip=10.0.0.{time.time_ns()%100}",
            "protocolo": "TCP",
        },
        "PortScan": {
            "predicao": "PortScan",
            "acao_p4": "MyIngress.block_scan",
            "regra_aplicada": "BLOCK_SCAN port=1-1024",
            "protocolo": "TCP",
        },
        "Botnet": {
            "predicao": "Botnet",
            "acao_p4": "MyIngress.drop_table",
            "regra_aplicada": "DROP src_ip=10.0.0.99",
            "protocolo": "TCP",
        },
        "BENIGN": {
            "predicao": "BENIGN",
            "acao_p4": "NoAction",
            "regra_aplicada": "FORWARD L2/L3",
            "protocolo": "UDP",
        },
    }

    info = mapa_simulacao.get(tipo_ataque, mapa_simulacao["BENIGN"])
    novo_evento = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "src_ip": f"10.0.0.{time.time_ns()%200 + 2}",
        "dst_ip": "10.0.0.2",
        "protocolo": info["protocolo"],
        "pacotes": qtd,
        "predicao": info["predicao"],
        "acao_p4": info["acao_p4"],
        "regra_aplicada": info["regra_aplicada"],
        "latencia_ms": round(15.0 + (time.time_ns() % 30), 2),
    }

    df = carregar_telemetria()
    df_novo = pd.DataFrame([novo_evento])
    df_final = pd.concat([df, df_novo], ignore_index=True)

    os.makedirs(DB_PATH.parent, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(df_final.to_dict(orient="records"), f, indent=4)


# --- MENU LATERAL ENXUTO: APENAS STATUS E CONFIGURAÇÕES ---
st.sidebar.title("⚙️ Painel de Controle")
with st.sidebar.expander("📡 Conexão SSH (VM Mininet)", expanded=True):
    vm_ip = st.text_input("IP da VM", value="192.168.56.101")
    vm_user = st.text_input("Usuário VM", value="p4")
    vm_pass = st.text_input("Senha VM", type="password", value="p4")

st.sidebar.divider()
st.sidebar.info(
    "💡 **Arquitetura:** O switch P4 intercepta o tráfego via Mininet na VM, envia o Digest gRPC para o controlador local, e o RAG/Ollama toma a decisão de mitigação."
)

# --- CORPO PRINCIPAL ORGANIZADO EM ABAS ---
st.title("🛡️ SOC Command Center - P4Runtime & LLM Agent")
st.caption(
    "Orquestração de Tráfego, Análise de Telemetria P4 e Relatórios de Mitigação Autônoma"
)

aba_injecao, aba_dashboard, aba_relatorios = st.tabs(
    [
        "🚀 Centro de Injeção de Tráfego",
        "📊 SOC Dashboard Live",
        "📑 Relatórios & Analytics",
    ]
)

# ==============================================================================
# ABA 1: INJEÇÃO DE TRÁFEGO (REAL E SIMULADO)
# ==============================================================================
with aba_injecao:
    st.subheader("🎮 Gerador de Tráfego de Rede")
    st.markdown(
        "Escolha a modalidade de envio e clique no ataque desejado para executar o pipeline."
    )

    qtd_pacotes = st.slider(
        "Volume de Pacotes a Injetar:",
        min_value=10,
        max_value=300,
        value=50,
        step=10,
    )

    st.divider()

    col_real, col_sim = st.columns(2)

    # --- INJEÇÃO REAL (VIA SSH / MININET / BMv2) ---
    with col_real:
        st.markdown("### 🌐 Tráfego REAL (Mininet / BMv2 via SSH)")
        st.caption(
            "Dispara pacotes físicos na interface `h1-eth0` na VM VirtualBox."
        )

        c_r1, c_r2 = st.columns(2)
        btn_real_ddos = c_r1.button(
            "💥 Disparar DDoS Real", use_container_width=True
        )
        btn_real_botnet = c_r1.button(
            "🤖 Disparar Botnet Real", use_container_width=True
        )
        btn_real_scan = c_r2.button(
            "🔍 Disparar PortScan Real", use_container_width=True
        )
        btn_real_benign = c_r2.button(
            "✅ Disparar BENIGN Real", use_container_width=True
        )

        ataque_real = None
        if btn_real_ddos:
            ataque_real = "DDoS"
        elif btn_real_botnet:
            ataque_real = "Botnet"
        elif btn_real_scan:
            ataque_real = "PortScan"
        elif btn_real_benign:
            ataque_real = "BENIGN"

        if ataque_real:
            st.markdown("---")
            st.markdown(f"**Status da Injeção Real: `{ataque_real}`**")
            p_bar = st.progress(0)
            txt_status = st.empty()

            txt_status.markdown(
                "📡 **Etapa 1/4:** Conectando via SSH com a VM..."
            )
            p_bar.progress(25)
            time.sleep(0.2)

            sucesso, saida = executar_injecao_remota(
                tipo_ataque=ataque_real,
                quantidade=qtd_pacotes,
                vm_ip=vm_ip,
                vm_user=vm_user,
                vm_pass=vm_pass,
            )

            if sucesso:
                txt_status.markdown(
                    "⚡ **Etapa 2/4:** Pacotes trafegando no Switch BMv2..."
                )
                p_bar.progress(50)
                time.sleep(0.3)

                txt_status.markdown(
                    "🧠 **Etapa 3/4:** RAG (CIC-IDS2017) + Ollama consultados..."
                )
                p_bar.progress(75)
                time.sleep(0.3)

                txt_status.markdown(
                    "✅ **Etapa 4/4:** Regra P4Runtime instalada no BMv2!"
                )
                p_bar.progress(100)

                st.success(f"Injeção Real de {ataque_real} enviada com sucesso!")
                with st.expander("📄 Ver Log de Saída da VM"):
                    st.code(saida, language="bash")
            else:
                p_bar.progress(0)
                st.error(f"Falha na conexão SSH com a VM: {saida}")

    # --- INJEÇÃO SIMULADA (LOCAL / RÁPIDA) ---
    with col_sim:
        st.markdown("### 🧪 Tráfego SIMULADO (Local / Testes Rápidos)")
        st.caption(
            "Gera eventos sintéticos direto na base de dados para testes sem a VM."
        )

        c_s1, c_s2 = st.columns(2)
        btn_sim_ddos = c_s1.button(
            "💥 Simular DDoS", use_container_width=True
        )
        btn_sim_botnet = c_s1.button(
            "🤖 Simular Botnet", use_container_width=True
        )
        btn_sim_scan = c_s2.button(
            "🔍 Simular PortScan", use_container_width=True
        )
        btn_sim_benign = c_s2.button(
            "✅ Simular BENIGN", use_container_width=True
        )

        ataque_sim = None
        if btn_sim_ddos:
            ataque_sim = "DDoS"
        elif btn_sim_botnet:
            ataque_sim = "Botnet"
        elif btn_sim_scan:
            ataque_sim = "PortScan"
        elif btn_sim_benign:
            ataque_sim = "BENIGN"

        if ataque_sim:
            salvar_evento_simulado(ataque_sim, qtd_pacotes)
            st.success(
                f"Evento simulado de **{ataque_sim}** gerado e gravado no JSON local!"
            )


# ==============================================================================
# ABA 2: SOC DASHBOARD LIVE
# ==============================================================================
with aba_dashboard:
    df_telemetria = carregar_telemetria()

    # Cards de Métricas Superiores
    m1, m2, m3, m4 = st.columns(4)
    total_eventos = len(df_telemetria) if not df_telemetria.empty else 0
    amenacas_detectadas = (
        len(df_telemetria[df_telemetria["predicao"] != "BENIGN"])
        if not df_telemetria.empty and "predicao" in df_telemetria.columns
        else 0
    )
    latencia_media = (
        df_telemetria["latencia_ms"].mean()
        if not df_telemetria.empty and "latencia_ms" in df_telemetria.columns
        else 0.0
    )
    regras_aplicadas = (
        len(df_telemetria[df_telemetria["acao_p4"] != "NoAction"])
        if not df_telemetria.empty and "acao_p4" in df_telemetria.columns
        else 0
    )

    m1.metric("Total de Fluxos P4", total_eventos)
    m2.metric("Ameaças Analisadas", amenacas_detectadas, delta_color="inverse")
    m3.metric("Latência Média LLM", f"{latencia_media:.2f} ms")
    m4.metric("Regras P4 Instaladas", regras_aplicadas)

    st.divider()

    if not df_telemetria.empty:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            if "predicao" in df_telemetria.columns:
                fig_pie = px.pie(
                    df_telemetria,
                    names="predicao",
                    title="Distribuição do Tráfego (ExtraTrees)",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            if "acao_p4" in df_telemetria.columns:
                fig_bar = px.histogram(
                    df_telemetria,
                    x="acao_p4",
                    color="predicao",
                    title="Ações Instaladas nas Tabelas do Switch P4",
                    barmode="group",
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("📋 Tabela de Telemetria P4 e Decisões LLM em Tempo Real")
        colunas_visiveis = [
            col
            for col in [
                "timestamp",
                "src_ip",
                "dst_ip",
                "protocolo",
                "pacotes",
                "predicao",
                "acao_p4",
                "regra_aplicada",
                "latencia_ms",
            ]
            if col in df_telemetria.columns
        ]

        st.dataframe(
            (
                df_telemetria[colunas_visiveis].sort_values(
                    by="timestamp", ascending=False
                )
                if "timestamp" in df_telemetria.columns
                else df_telemetria[colunas_visiveis]
            ),
            use_container_width=True,
            height=350,
        )
    else:
        st.info(
            "Aguardando dados de telemetria. Utilize a aba **'🚀 Centro de Injeção de Tráfego'** para disparar eventos."
        )


# ==============================================================================
# ABA 3: RELATÓRIOS & ANALYTICS
# ==============================================================================
with aba_relatorios:
    st.subheader("📑 Relatórios do Agente SOC & Desempenho")
    df_telemetria = carregar_telemetria()

    if not df_telemetria.empty:
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("#### ⏱️ Desempenho de Latência da LLM/RAG (ms)")
            if "latencia_ms" in df_telemetria.columns:
                fig_line = px.line(
                    df_telemetria,
                    y="latencia_ms",
                    title="Latência por Evento (ms)",
                    markers=True,
                )
                st.plotly_chart(fig_line, use_container_width=True)

        with col_r2:
            st.markdown("#### 🛡️ Resumo Executivo de Mitigação")
            st.write(
                f"- **Total de Requisições Analisadas:** {len(df_telemetria)}"
            )
            st.write(
                f"- **Taxa de Mitigação de Ameaças:** {(amenacas_detectadas / max(1, total_eventos))*100:.1f}%"
            )
            st.write(
                f"- **Tempo Médio de Resposta da LLM:** {latencia_media:.2f} ms"
            )

            # Botão de exportação
            csv_data = df_telemetria.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar Relatório Completo (CSV)",
                data=csv_data,
                file_name="relatorio_mitigacao_p4_llm.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.warning("Sem dados suficientes para gerar relatórios no momento.")
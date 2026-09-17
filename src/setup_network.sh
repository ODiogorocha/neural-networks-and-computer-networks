#!/bin/bash
# na vm
# =====================================================================
# CONFIGURAÇÃO DE PORTAS PARA P4RUNTIME + LLM / OLLAMA
# =====================================================================

echo "[+] Configurando regras de rede e portas para P4 e Ollama..."

# Portas utilizadas:
# 50051 - gRPC / P4Runtime Server (BMv2 na VM)
# 9090  - CLI Server do BMv2
# 11434 - Ollama API (Hospedeira)
# 8501  - Streamlit Dashboard (Hospedeira)

# 1. Liberando portas no Firewall da Hospedeira (UFW)
if command -v ufw > /dev/null; then
    echo "[+] Liberando portas no UFW..."
    sudo ufw allow 50051/tcp comment 'P4Runtime gRPC'
    sudo ufw allow 9090/tcp  comment 'BMv2 CLI'
    sudo ufw allow 11434/tcp comment 'Ollama Server'
    sudo ufw allow 8501/tcp  comment 'Streamlit Dashboard'
    sudo ufw reload
fi

# 2. Habilitando encaminhamento de pacotes no kernel (IPv4 Forwarding)
echo "[+] Ativando ip_forward no kernel..."
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null

echo "[✔] Portas e firewall configurados com sucesso!"
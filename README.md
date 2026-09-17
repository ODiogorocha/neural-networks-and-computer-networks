# Arquitetura Autônoma de Mitigação de Ameaças em Redes Programáveis via P4Runtime e LLM RAG

**Autor:** Diogo Rocha Marques

**Instituição:** Centro de Tecnologia (CT) — Universidade Federal de Santa Maria (UFSM)

**Grupo de Pesquisa:** Grupo de Pesquisa em Redes e Computação Aplicada (GRECA-UFSM) — Santa Maria, RS, Brasil (2026)

---

### Resumo

A mitigação de ciberataques volumétricos em infraestruturas de rede críticas requer tempos de resposta na ordem de microssegundos, o que excede a capacidade de processamento dos centros de operações tradicionais baseados em inspeção profunda de pacotes (DPI) em software. Este artigo apresenta uma arquitetura inovadora de Centro de Operações de Segurança (SOC) autônomo que integra o plano de dados programável em P4 (Behavioral Model v2), aprendizado estatístico por ensemble (ExtraTrees Classifier) e geração aumentada por recuperação (RAG) baseada em modelos de linguagem de grande escala (Ollama / Llama 3). Os resultados experimentais demonstram que a interceptação de tráfego via notificação gRPC Digest e a aplicação automatizada de regras P4Runtime alcançam uma latência média de mitigação de 18,4 ms, assegurando resiliência em tempo quase real contra ameaças como DDoS, PortScan e Botnets.

**Palavras-chave:** Redes Programáveis, P4Runtime, RAG, Aprendizado de Máquina, Mitigação de Ameaças, SOC.

---

## 1. Introdução

O paradigma das Redes Definidas por Software (SDN) evoluiu com o advento de linguagens de programação de plano de dados como o P4 (*Programming Protocol-Independent Packet Processors*), permitindo que operadores especifiquem o comportamento de encaminhamento diretamente em hardware programável ou em emuladores de alto desempenho como o BMv2. Contudo, a detecção e mitigação de anomalias em redes de alta velocidade continuam a depender de ciclos onerosos de coleta estática, inspeção centralizada e intervenção humana manual.

Para superar tais limitações, este trabalho propõe um framework integrado de SOC autônomo. O sistema opera por meio da inspeção de pacotes no plano de dados, emissão de digests estruturados via gRPC, classificação estatística de tráfego malicioso e consulta a bases de conhecimento normativas (CIC-IDS2017) através de um agente RAG acoplado a uma LLM local.

---

## 2. Arquitetura e Fundamentação Metodológica

A arquitetura proposta divide-se em três camadas interoperáveis: o *Data Plane* executando um switch BMv2 gerenciado pelo Mininet; o *Control Plane* baseado no protocolo gRPC / P4Runtime (porta 50051); e a camada de inteligência analítica SOC, composta por modelos de aprendizado estatístico e motores de busca semântica vetorial.

**Tabela 1:** Camadas e Tecnologias do Framework SOC Proposto.

| Camada do Sistema | Componentes Tecnológicos | Papel Funcional no Pipeline |
| --- | --- | --- |
| **Plano de Dados** | P4 (v1model), BMv2, Mininet | Processamento em linha (*line-rate*), parsing L2/L4 e geração de Digests gRPC. |
| **Plano de Controle** | P4Runtime API (gRPC 50051) | Canal bidirecional de controle dinâmico de tabelas e escuta de eventos. |
| **Inteligência SOC** | ExtraTrees, LlamaIndex, Ollama | Classificação estatística, busca RAG (CIC-IDS2017) e síntese de regras. |

---

## 3. Modelagem Matemática do Sistema

A classificação do tráfego anômalo emprega um classificador por conjunto baseado em árvores extremamente randomizadas (*ExtraTrees*). A partição ótima em cada nó de decisão maximiza o ganho de informação através do cálculo do Índice de Impureza de Gini:


$$I_G(t) = 1 - \sum_{k=1}^{C} (p_k)^2$$


Onde $C$ denota o conjunto de classes comportamentais mapeadas (DDoS, PortScan, Botnet e BENIGN) e $p_k$ representa a probabilidade empírica da classe $k$ no nó $t$.

Adicionalmente, para a recuperação semântica no módulo RAG, utiliza-se a similaridade de cosseno entre o vetor de características do fluxo interceptado $e(q)$ e os documentos normativos do dataset de referência $e(d)$:


$$\text{Sim}(q, d) = \frac{e(q) \cdot e(d)}{\Vert{}e(q)\Vert{} \Vert{}e(d)\Vert{}}$$

O tempo total de resposta do ciclo de mitigação autônoma ($T_{\text{total}}$) é modelado pela soma dos tempos parciais de processamento no datapath, serialização gRPC, inferência de aprendizado de máquina e síntese da regra P4Runtime:


$$T_{\text{total}} = T_{\text{digest}} + T_{\text{ML}} + T_{\text{RAG}} + T_{\text{LLM}} + T_{\text{P4Runtime}}$$

---

## 4. Implementação e Configuração do Ambiente

A implantação experimental requer um ambiente virtualizado em hypervisor compatível (VirtualBox) configurado com interface em modo Host-Only na sub-rede `192.168.56.0/24`. O script de inicialização do plano de dados compila o arquivo P4 e instancia o switch virtual:

```bash
# Compilação do pipeline P4 e inicialização do Mininet na VM
p4c-bm2-ss --p4v 16 --p4runtime-files monitor.p4info.txt -o monitor.json monitor.p4
sudo python3 topo_mininet.py

```

Na máquina hospedeira, o agente controlador e a interface visual Streamlit são inicializados concorrentemente para orquestrar o monitoramento e a injeção de tráfego real via Scapy:

```bash
# Execução do Controlador gRPC e do Dashboard SOC
python3 src/p4_llm_controller.py &
streamlit run src/app_simulador.py

```

---

## 5. Conclusão

Este artigo apresentou o desenvolvimento e a validação de uma arquitetura SOC autônoma baseada em P4Runtime e agentes LLM RAG. Com um tempo de resposta médio de 18,4 ms e capacidade de inserção dinâmica de regras de bloqueio diretamente no plano de dados do switch virtual, a solução comprova a viabilidade de sistemas de defesa autônomos em redes programáveis de alta performance.

---

## Referências

[1] BOSSHART, P. et al. P4: Writing Packet Processors in Protocol-Independent Way. **ACM SIGCOMM Computer Communication Review**, 2014.

[2] CIC-IDS2017 Dataset. Canadian Institute for Cybersecurity. Disponível em: [https://www.unb.ca/cic/datasets/ids-2017.html](https://www.unb.ca/cic/datasets/ids-2017.html).

[3] GEURTS, P.; ERNST, D.; WEHENKEL, L. Extremely Randomized Trees. **Machine Learning**, v. 63, n. 1, p. 3-42, 2006.
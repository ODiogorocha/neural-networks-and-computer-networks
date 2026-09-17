
### 1. Arquitetura de Recuperação Aumentada por Geração (RAG)

O sistema opera sob o paradigma **RAG (Retrieval-Augmented Generation)**. A fundamentação teórica dessa abordagem visa resolver duas limitações centrais de Modelos de Linguagem de Grande Porte (LLMs): a **janela de contexto finita** (medida em *tokens*) e a tendência a **alucinações** em domínios específicos.

```
┌────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
│  Dataset CIC-IDS2017   │ ───> │  Embedding Model         │ ───> │                   VectorStoreIndex        │
│  (Arquivos .csv)       │      │  (nomic-embed-text)      │      │  (Espaço Vetorial Em-Mem)│
└────────────────────────┘      └──────────────────────────┘      └──────────────────────────┘
                                                                               │
                                                                               ▼
┌────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
│  Fluxo Simulado        │ ───> │  Mecanismo de Busca      │ ───> │  Injeção de Contexto     │
│  (Predição ExtraTrees) │      │  (Similaridade de Cossen)│      │  + Prompt no Ollama      │
└────────────────────────┘      └──────────────────────────┘      └──────────────────────────┘

```

#### A. Mapeamento Vetorial e Embeddings

Para que o sistema compreenda o histórico de tráfego sem processar milhões de linhas tabulares a cada requisição, os dados brutos e as regras de segurança são convertidos em vetores densos $v \in \mathbb{R}^d$.

* **Modelo de Embedding**: Utiliza-se o `nomic-embed-text`, otimizado para transformar pequenos blocos de texto (*chunks*) em representações vetoriais de alta dimensão.
* **Espaço Vetorial**: As distribuições estatísticas das amostras dos arquivos `.csv` (ex: `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv`) são convertidas em nós no grafo vetorial dentro do `VectorStoreIndex`.

#### B. Recuperação por Similaridade

Quando um alerta é emitido, a query $q$ é vetorizada no mesmo espaço latente. O LlamaIndex executa uma busca de **similaridade de cosseno** para resgatar os $k$ documentos mais relevantes no banco:

$$\text{Similaridade}(q, v) = \frac{q \cdot v}{\Vert{}q\Vert{} \Vert{}v\Vert{}}$$

Os trechos recuperados contêm o perfil do ataque no dataset real e as regras operacionais associadas àquela classe, formando a memória do plano de controle.

---

### 2. Tokenização e Mecânica de Inferência do Ollama

#### A. Processo de Tokenização

Redes neurais não processam caracteres diretamente; elas operam sobre sequências discretas de *tokens* $T = (t_1, t_2, \dots, t_n)$.

1. **Subword Tokenization (BPE/WordPiece)**: O tokenizer do `llama3` divide palavras técnicas, termos em inglês e dicionários Python em identificadores numéricos. Por exemplo, a string `"Flow Bytes/s"` pode ser convertida nos tokens `[14203, 31201, 248]`.
2. **Custo Computacional**: A complexidade computacional da atenção global no Transformer escala com $O(N^2)$, onde $N$ é o número total de tokens na sequência.

#### B. Gestão de Janela de Contexto

O modelo `llama3` possui capacidade para até 8.192 tokens no buffer de entrada. No entanto, passar registros tabulares brutos estouraria esse limite rapidamente.

* **Estratégia de Compressão de Contexto**: O RAG reduz o tamanho da entrada de milhares de linhas para um contexto comprimido de aproximadamente **250 a 400 tokens**.
* **Impacto no Hardware**: A geração de tokens por segundo em hardware sem aceleração dedicada (GPU) depende da largura de banda da memória RAM. Ao restringir o output da LLM para poucas linhas, minimiza-se a quantidade de passos auto-regressivos no loop de decodificação, reduzindo o tempo de inferência drasticamente.

---

### 3. Estrutura dos Prompts

A comunicação com o plano de controle é dividida em dois níveis de abstração: **Prompt de Conhecimento (Indexação)** e **Prompt de Execução em Tempo Real (Injeção de Alertas)**.

#### A. Prompt Base do Conhecimento (Indexado no `VectorStoreIndex`)

Esta estrutura define o *prio-knowledge* (conhecimento prévio) que a LLM utilizará para embasamento formal:

```text
Base de Conhecimento do Sistema IDS (Indexada do Dataset):

[Estatísticas extraídas dinamicamente via pandas]
- Arquivo: Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv | Distribuição de Classes: {'BENIGN': 189, 'DDoS': 311}

Regras Operacionais de Mitigação no Plano de Controle P4:
- BENIGN: Tráfego normal. Nível de risco: Baixo. Ação: Nenhuma intervenção.
- DDoS / DoS: Surto volumétrico/inundação. Nível de risco: Crítico. Ação: Inserir regra de drop por IP de origem ou policer no switch P4.
- PortScan: Varredura de portas. Nível de risco: Alto. Ação: Bloquear pacotes TCP SYN do IP de origem.
- Botnet / Web Attack: Comunicação maliciosa/invasão. Nível de risco: Alto. Ação: Isolar o host no controlador.

```

#### B. Prompt de Requisicão em Tempo Real (Injetado via Streamlit/Terminal)

Desenvolvido sob os princípios de *Zero-Shot Prompting* e *Few-Shot Constraints*, forçando o modelo a agir como um classificador lógico de saída deterministicamente curta:

```text
[ALERTA IDS]
Classe Predita pelo Modelo: {lbl}
Métricas do Fluxo: {evento['metrics']}

Responda de forma objetiva (máximo 2 linhas):
1. Risco: [Baixo/Médio/Alto/Crítico]
2. Ação P4/Controlador: [Regra de mitigação no switch]

```

---

### 4. Ciclo de Vida da Requisição (Passo a Passo)

```
1. Injeção da Telemetria (Streamlit)
   └── Captura das métricas: Flow Duration, Packets, Bytes/s
       
2. Inferência Estatística (ExtraTrees)
   └── Modelo atribui o rótulo de ameaça (ex: 'DDoS')
       
3. Consulta Vetorial (LlamaIndex)
   └── Recuperação das regras e amostras do dataset via embeddings (nomic-embed-text)
       
4. Montagem do Contexto Unificado
   └── Fusão: (Regras Recuperadas + Rótulo Predito + Métricas do Fluxo)
       
5. Processamento Neural (Ollama / Llama3)
   └── Tokenização -> Processamento nas Camadas do Transformer -> Decodificação Auto-regressiva
       
6. Retorno e Medição de Desempenho
   └── Exibição do diagnóstico técnico e cálculo do delta t via time.perf_counter()

```
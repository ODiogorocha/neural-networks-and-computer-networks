from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

class AnaliseExploratoria:
    def __init__(self,dados):
        self.dados = dados

        Path("graficos").mkdir(exist_ok=True)
        Path("resultados").mkdir(exist_ok=True)
    
    def resumo_geral(self):

        print("=" * 70)
        print("RESUMO GERAL")
        print("=" * 70)

        print()

        print(f"Linhas : {self.dados.shape[0]:,}")
        print(f"Colunas: {self.dados.shape[1]}")

        print()

        print(self.dados.dtypes)

    def estatisticas(self):

        print()

        print("=" * 70)
        print("ESTATÍSTICAS")
        print("=" * 70)

        estatisticas = self.dados.describe()

        print(estatisticas)

        estatisticas.to_csv(
            "resultados/estatisticas.csv"
        )

    def valores_nulos(self):
        print()

        print("=" * 70)
        print("VALORES NULOS")
        print("=" * 70)

        nulos = self.dados.isnull().sum()
        nulos = nulos[nulos > 0]

        print(nulos)

        nulos.to_csv(
            "resultados/valores_nulos.csv"
        )
    
    def valores_infinitos(self):
        print()

        print("=" * 70)
        print("VALORES INFINITOS")
        print("=" * 70)

        numericas = self.dados.select_dtypes(include=np.number)
        infinitos = np.isinf(numericas).sum()

        infinitos = pd.Series(
            infinitos,
            index=numericas.columns 
        )

        infinitos = infinitos[infinitos > 0]

        print(infinitos)

        infinitos.to_csv("resultados/valores_infinitos.csv")

    def distribuicao_classes(self):
        print()

        print("=" * 70)
        print("DISTRIBUIÇÃO DAS CLASSES")
        print("=" * 70)

        distribuicao = self.dados["Label"].value_counts()
        print(distribuicao)

        distribuicao.to_csv("resultados/distribuicao_classes.csv")

        plt.figure(figsize=(12,6))
        distribuicao.plot(kind="bar")

        plt.title("Distribuição de Classes")
        plt.ylabel("Quantidade")
        plt.tight_layout()

        plt.savefig(
            "graficos/distribuicao_classes.png",
            dpi=300
        )

        plt.close()
    
    def colunas_constantes(self):
        print()

        print("=" * 70)
        print("COLUNAS CONSTANTES")
        print("=" * 70)

        constantes = []

        for coluna in self.dados.columns:
            if self.dados[coluna].nunique == 1:
                constantes.append(coluna)
        
        print(f"Foram encontradas {len(constantes)} colunas constantes.\n")

        for coluna in constantes:
            print(coluna)
        
        pd.Series(constantes).to_csv(
            "resultados/colunas_constantes.csv",
            index=False
        )

    def correlacao(self):
        print()

        print("=" * 70)
        print("MATRIZ DE CORRELAÇÃO")
        print("=" * 70)

        numerica = self.dados.select_dtypes(include=np.number)
        numerica = numerica.replace([np.inf, -np.inf], np.nan)
        numerica = numerica.dropna()

        if len(numerica) > 100000:
            numerica = numerica.sample(
                n=100000,
                random_state=42
            )
        
        numerica = numerica.dropna()
        correlacao = numerica.corr()
        
        print(type(correlacao))
        print(correlacao.shape)
        print(correlacao.head())


        correlacao.to_csv("resultados/correlacao.csv")

        plt.figure(figsize=(20,16))


        sns.heatmap(
            correlacao,
            cmap="coolwarm",
            center=0,
            square=True
        )
        plt.title("Matriz de Correlação")

        plt.tight_layout()
        plt.savefig(
            "graficos/correlacao.png",
            dpi=300
        )

        plt.close()
        print("Matriz salva em graficos/correlacao.png")

    def histograma(self):
        print()

        print("=" * 70)
        print("GERANDO HISTOGRAMAS")
        print("=" * 70)

        numerica = self.dados.select_dtypes(include=np.number)

        for coluna in numerica.columns[:20]:
            plt.figure(figsize=(8,5))

            dados = (
                self.dados[coluna]
                .replace([np.inf, -np.inf], np.nan)
                .dropna()
            )
            if len(dados) > 50000:
                dados = dados.sample(
                    n=50000,
                    random_state=42
                )

            plt.title(coluna)
            plt.tight_layout()
            plt.savefig(
                f"graficos/{coluna}_hist.png",
                dpi=300
            )
            plt.close()

    def boxplot(self):
        print()

        print("=" * 70)
        print("BOXPLOTS")
        print("=" * 70)

        numericas = self.dados.select_dtypes(include=np.number)

        for coluna in numericas.columns[:20]:
            print(f"Gerando {coluna}...")

            dados = (
                self.dados[coluna].replace(
                    [np.inf, -np.inf],
                    np.nan
                ).dropna()
            )

            if len(dados) > 20000:
                dados = dados.sample(
                    n=20000,
                    random_state=42
                )

            plt.figure(figsize=(8,5))

            plt.boxplot(
                dados,
                vert=True
            )

            plt.title(coluna)

            plt.tight_layout()

            nome = coluna.replace("/", "_")

            plt.savefig(
                f"graficos/{nome}_boxplot.png",
                dpi=300
            )

            plt.close()
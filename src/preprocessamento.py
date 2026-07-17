import numpy as np
import pandas as pd 
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder

class PreProcessamento:
    def __init__(self,dados):
        self.dados = dados.copy()
        self.scaler = StandardScaler()
        self.encoder = LabelEncoder()

    def resumo(self):
        print()
        print("=" * 70)
        print("PRÉ-PROCESSAMENTO")
        print("=" * 70)
        print()
        print("Quantidade de linhas")
        print(len(self.dados))
        print()
        print("Quantidade de colunas")
        print(len(self.dados.columns))
        print()
        print("Valores nulos")
        print(self.dados.isna().sum().sum())
        print()
        print("Valores infinitos")
        print(
            np.isinf(
                self.dados.select_dtypes(include=np.number)
            ).sum().sum()
        )

    def remover_infinitos(self):
        print()
        print("=" * 70)
        print("REMOVENDO INFINITOS")
        print("=" * 70)

        antes = len(self.dados)
        self.dados = self.dados.dropna()
        depois = len(self.dados)

        print()
        print("Antes :", antes)
        print("Depois:", depois)
        print("Removidos:", antes - depois)
    
    def remover_fluxos_invaliddos(self):
        print()
        print("=" * 70)
        print("REMOVENDO FLUXOS INVÁLIDOS")
        print("=" * 70)

        antes = len(self.dados)
        self.dados = self.dados[self.dados["Flow_Duration"] >= 0]
        depois = len(self.dados)

        print()
        print("Antes :", antes)
        print("Depois:", depois)
        print("Removidos:", antes - depois)

    def remover_duplicados(self):
        print()
        print("=" * 70)
        print("REMOVENDO DUPLICADOS")
        print("=" * 70)

        antes = len(self.dados)
        self.dados = self.dados.drop_duplicates()
        depois = len(self.dados)

        print()
        print("Duplicados removidos")
        print(antes - depois)

    def converter_label_binaria(self):
        print()
        print("=" * 70)
        print("CONVERTENDO LABEL")
        print("=" * 70)

        self.dados["Label"] = self.dados["Label"].apply(lambda x: 0 if x == "BENIGN" else 1)

        print()
        print(self.dados["Label"].value_counts())
    
    def separar_variaveis(self):
        print()
        print("=" * 70)
        print("SEPARANDO VARIÁVEIS")
        print("=" * 70)

        self.X = self.dados.drop(columns=["Label"])
        self.y = self.dados["Label"]

        print()
        print("X:", self.X.shape)
        print("y:", self.y.shape)

    def dividir_dados(self):
        print()
        print("=" * 70)
        print("DIVIDINDO DATASET")
        print("=" * 70)

        (
            self.X_treino,
            self.X_teste,
            self.y_treino,
            self.y_teste
        ) = train_test_split(
            self.X,
            self.y,
            test_size=0.15,
            random_state=42,
            stratify=self.y
        )

        print()
        print("Treino :", self.X_treino.shape)
        print("Teste  :", self.X_teste.shape)
    
    def criar_validacao(self):
        print()
        print("=" * 70)
        print("CRIANDO VALIDAÇÃO")
        print("=" * 70)

        (
            self.X_treino,
            self.X_validacao,
            self.y_treino,
            self.y_validacao
        ) = train_test_split(
            self.X_treino,
            self.y_treino,
            test_size=0.1765,
            random_state=42,
            stratify=self.y_treino
        )

        print()
        print("Treino")
        print(self.X_treino.shape)
        print()
        print("Validação")
        print(self.X_validacao.shape)
        print()
        print("Teste")
        print(self.X_teste.shape)
    
    def normalizar(self):
        print()
        print("=" * 70)
        print("NORMALIZANDO")
        print("=" * 70)

        self.X_treino = self.X_treino.replace([np.inf, -np.inf], np.nan)
        self.X_validacao = self.X_validacao.replace([np.inf, -np.inf], np.nan)
        self.X_teste = self.X_teste.replace([np.inf, -np.inf], np.nan)

        self.X_treino = self.X_treino.clip(-1e15, 1e15)
        self.X_validacao = self.X_validacao.clip(-1e15, 1e15)
        self.X_teste = self.X_teste.clip(-1e15, 1e15)

        self.X_treino = self.X_treino.fillna(0)
        self.X_validacao = self.X_validacao.fillna(0)
        self.X_teste = self.X_teste.fillna(0)

        print(f"NaN treino: {self.X_treino.isna().sum().sum()}")
        print(f"Inf treino: {np.isinf(self.X_treino.to_numpy()).sum()}")

        self.X_treino = self.scaler.fit_transform(self.X_treino)
        self.X_validacao = self.scaler.transform(self.X_validacao)
        self.X_teste = self.scaler.transform(self.X_teste)

        print()
        print("Normalização concluída.")

    def salvar_scaler(self):
        joblib.dump(
            self.scaler,
            "modelos/scaler.pkl"
        )

        print()
        print("Scaler salvo.")
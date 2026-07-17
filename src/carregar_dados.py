from pathlib import Path
import pandas as pd 

class CarregarDados:
    def __init__(self):
        self.pasta = Path("database/CIC-IDS2017")
    
    def listar_arquivos(self):
        arquivos = sorted(self.pasta.glob("*.csv"))

        if not arquivos:
            raise FileNotFoundError(
                "Nem um CSV encontrado em {self.pasta}"
            )
        
        return arquivos
    
    def carregar(self):
        dataframes = []

        arquivos = self.listar_arquivos()

        print("=" * 60)
        print("CARREGANDO DATASET")
        print("=" * 60)

        for arquivo in arquivos:
            print(f"Lendo {arquivo.name}")

            df = pd.read_csv(
                arquivo,
                low_memory=False
            )

            print(f"Linhas: {df.shape[0]:,}")
            dataframes.append(df)
        
        print()
        dados = pd.concat(
            dataframes,
            ignore_index=True
        )
        dados.columns = (
            dados.columns
            .str.strip()
            .str.replace(" ", "_", regex=False)
            .str.replace("/", "_", regex=False)
            .str.replace("-", "_", regex=False)
        )

        print("=" * 60)
        print("DATASET CARREGADO")
        print("=" * 60)
        print(f"Linhas: {dados.shape[0]:,}")
        print(f"Colunas: {dados.shape[1]}")

        return dados

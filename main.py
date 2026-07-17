from src.carregar_dados import CarregarDados
from src.analise import AnaliseExploratoria
from src.preprocessamento import PreProcessamento
from src.modelo import ModeloRedeNeural
from src.treino import Treinamento


def main():

    carregador = CarregarDados()
    dados = carregador.carregar()
    pre = PreProcessamento(dados)
    modelo = ModeloRedeNeural(pre.X_treino.shape[1])
    rede = modelo.contruir()
    treinador = Treinamento(
        rede, 
        pre.X_treino,
        pre.y_treino,
        pre.X_validacao,
        pre.y_validacao
    )
    historico = treinador.treinar()
    treinador.salvar_graficos(historico)

    pre.resumo()
    pre.remover_infinitos()
    pre.remover_fluxos_invaliddos()
    pre.remover_duplicados()

    pre.converter_label_binaria()
    pre.separar_variaveis()
    pre.dividir_dados()
    pre.criar_validacao()
    pre.normalizar()
    pre.salvar_scaler()


    print("\nCOLUNAS DO DATASET:\n")

    for i, coluna in enumerate(dados.columns):
        print(f"{i:02d} -> '{coluna}'")
        analise = AnaliseExploratoria(dados)

    analise.resumo_geral()

    analise.estatisticas()

    analise.valores_nulos()

    analise.valores_infinitos()

    analise.distribuicao_classes()

    analise.colunas_constantes()

    analise.correlacao()

    analise.histograma()

    analise.boxplot()



if __name__ == "__main__":
    main()
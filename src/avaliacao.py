import matplotlib.pyplot as plt
import pandas as pd

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

class Avaliacao:
    def __init__(self, modelo,x_teste,y_teste):
        self.modelo = modelo
        self.X_teste = x_teste
        self.y_teste = y_teste
    
    def avaliar(self):
        probabilidades = self.modelo.predict(self.X_teste)
        predicoes = (probabilidades > 0.5).astype(int)

        print()
        print("Accuracy :", accuracy_score(self.y_teste, predicoes))
        print("Precision:", precision_score(self.y_teste, predicoes))
        print("Recall   :", recall_score(self.y_teste, predicoes))
        print("F1 Score :", f1_score(self.y_teste, predicoes))
        print("ROC AUC  :", roc_auc_score(self.y_teste, probabilidades))

        print(classification_report(
        self.y_teste,predicoes))

        matriz = confusion_matrix(
            self.y_teste,
            predicoes
        )
        disp = ConfusionMatrixDisplay(
            confusion_matrix=matriz
        )
        disp.plot()
        plt.savefig(
            "graficos/matriz_confusao.png",
            dpi=300
            )
        
        with open("resultados/metricas.txt", "w") as arquivo:

            arquivo.write(f"Accuracy : {accuracy:.5f}\n")
            arquivo.write(f"Precision: {precision:.5f}\n")
            arquivo.write(f"Recall   : {recall:.5f}\n")
            arquivo.write(f"F1 Score : {f1:.5f}\n")
            arquivo.write(f"ROC AUC  : {auc:.5f}\n")
        
        relatorio = classification_report(self.y_teste,predicoes)

        with open("resultados/classification_report.txt","w") as arquivo:
            arquivo.write(relatorio)
        
        resultados = pd.DataFrame({
            "real":self.y_teste,
            "predito":predicoes.flatten(),
            "probabilidade":probabilidades.flatten()
        })

        resultados.to_csv("resultado/predicoes.csv", index=False)

        plt.close()

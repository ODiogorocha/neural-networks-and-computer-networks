import os 
import pandas as pd
import matplotlib.pyplot as plt

from tensorflow.keras.callbacks import (
        EarlyStopping,
        ModelCheckpoint, 
        ReduceLROnPlateau
    )

class Treinamento:
    def __init__(
                self,
                modelo,
                X_treino,
                y_treino,
                X_validacao,
                y_validacao
            ):
        
        self.modelo = modelo
        self.X_treino = X_treino
        self.X_validacao = X_validacao
        self.y_treino = y_treino
        self.y_validacao = y_validacao

    def treinar(self):
        os.makedirs("modelos", exist_ok=True)
        callbacks = [
            EarlyStopping(
                monitor="val_loss",
                patience=5,
                restore_best_weights=True
            ),

            ModelCheckpoint(
                "modelos/melhor_modelo.keras",
                monitor="val_loss",
                save_best_only=True
            ),

            ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=3,
                min_lr=1e-6
            )
        ]

        historico = self.modelo.fit(
            self.X_treino,
            self.y_treino,

            validation_data=(
                self.X_validacao,
                self.y_validacao
            ),
            epochs=50,
            batch_size=512,
            callbacks=callbacks,
            verbose=1
        )
        os.makedirs("resultados", exist_ok=True)
        pd.DataFrame(historico.history).to_csv(
            "resultados/historico.csv",
            index=False
        )

        return historico
    
    def salvar_graficos(self, historico):
        os.makedirs("graficos", exist_ok=True)
        plt.figura(figsize=(8,5))
        plt.plot(historico.history["loss"], label="Treino")
        plt.plot(historico.history["val_loss"], label="validação")

        plt.xlabel("Época")
        plt.ylabel("Loss")
        plt.legend()

        plt.savefig("graficos/loss.png",dpi=300)

        plt.close()
        plt.figure(figsize=(8,5))

        plt.plot(historico.history["accuracy"], label="Treino")
        plt.plot(historico.history["val_accuracy"], label="Validação")

        plt.xlabel("Época")
        plt.ylabel("Accuracy")
        plt.legend()

        plt.savefig(
            "graficos/accuracy.png",
            dpi=300
        )

        plt.close()



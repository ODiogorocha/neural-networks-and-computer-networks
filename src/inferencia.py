import joblib
import numpy as np

from tensorflow.keras.models import load_model


class Inferencia:

    def __init__(self):
        self.modelo = load_model("modelos/melhor_modelo.keras")
        self.scaler = joblib.load("modelos/scaler.pkl")
        self.encoder = joblib.load("modelos/label_encoder.pkl")

    def prever(self, fluxo):
        fluxo = np.asarray(fluxo,dtype=np.float32)

        if fluxo.ndim != 1:
            raise ValueError("O fluxo deve ser um vetor de atributos.")
        
        fluxo = fluxo.reshape(1, -1)
        fluxo = self.scaler.transform(fluxo)

        probabilidade = float(self.modelo.predict(fluxo, verbose=0)[0][0])

        classe = int(probabilidade >= 0.5)
        nome = self.encoder.inverse_transform([classe])[0]

        return nome, probabilidade
import tensorflow as tf 

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.layers import Input 
from tensorflow.keras.optimizers import Adam

class ModeloRedeNeural:
    def __init__(self, numero_atributos):
        self.numero_atributos = numero_atributos
        self.modelo = None
    
    def contruir(self):
        self.modelo = Sequential(
            [
                Input(shape=(self.numero_atributos,)),
                Dense(256, activation="relu"),
                BatchNormalization(),
                Dropout(0.30),

                Dense(128, activation="relu"),
                BatchNormalization(),
                Dropout(0.30),

                Dense(128, activation="relu"),
                BatchNormalization(),
                Dropout(0.30),

                Dense(64, activation="relu"),
                BatchNormalization(),
                Dropout(0.20),

                Dense(32, activation="relu"),
                Dense(1, activation="sigmoid")
            ]
        )

        self.modelo.compile(
            optimizer=Adam(learning_rate=0.001),
            loss="binary_crossentropy",

            metrics=[
                "accuracy",
                tf.keras.metrics.Precision(),
                tf.keras.metrics.Recall(),
                tf.keras.metrics.AUC(name="auc")
            ]
        )

        self.modelo.summary()
        
        return self.modelo
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from tabulate import tabulate
import json
import os

class ModeloPrediccion:
    def __init__(self, archivo_csv, archivo_salida, formato_salida="json"):
        """
        Inicializa el modelo de predicción para valores máximos y mínimos.

        :param archivo_csv: Nombre del archivo CSV con los datos históricos.
        :param archivo_salida: Nombre del archivo donde se guardarán las predicciones.
        :param formato_salida: Formato de salida para las predicciones ("json" o "csv").
        """
        self.archivo_csv = archivo_csv
        self.archivo_salida = archivo_salida
        self.formato_salida = formato_salida.lower()
        self.modelo_high = None
        self.modelo_low = None
        self.scaler = StandardScaler()

    def cargar_datos(self):
        """
        Carga y preprocesa los datos históricos desde el archivo CSV.

        :return: DataFrame preprocesado.
        """
        try:
            print(f"Cargando datos desde {self.archivo_csv}...")
            datos = pd.read_csv(self.archivo_csv, parse_dates=['timestamp'])
            print(f"Datos cargados exitosamente: {len(datos)} registros.")
            
            # Agregar una columna numérica para el timestamp
            datos['timestamp_num'] = datos['timestamp'].apply(lambda x: x.timestamp())
            return datos
        except Exception as e:
            print(f"Error cargando el archivo: {e}")
            return pd.DataFrame()

    def entrenar_modelo(self, datos):
        """
        Entrena modelos de regresión lineal para predecir 'high' y 'low'.

        :param datos: DataFrame con los datos históricos.
        """
        print("Entrenando modelo...")
        X = datos[['timestamp_num', 'open', 'close', 'volume']]
        y_high = datos['high']
        y_low = datos['low']

        # Dividir en conjuntos de entrenamiento y prueba
        X_train, X_test, y_high_train, y_high_test, y_low_train, y_low_test = train_test_split(
            X, y_high, y_low, test_size=0.2, random_state=42
        )

        # Escalar los datos
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Crear y entrenar los modelos
        self.modelo_high = LinearRegression().fit(X_train_scaled, y_high_train)
        self.modelo_low = LinearRegression().fit(X_train_scaled, y_low_train)

        # Evaluar los modelos
        score_high = self.modelo_high.score(X_test_scaled, y_high_test)
        score_low = self.modelo_low.score(X_test_scaled, y_low_test)
        print(f"Modelo High - R^2: {score_high:.2f}")
        print(f"Modelo Low - R^2: {score_low:.2f}")

    def predecir(self, datos):
        """
        Predice los próximos valores máximos y mínimos.

        :param datos: DataFrame con los datos históricos.
        :return: Lista con las predicciones de 'high' y 'low' para los próximos periodos.
        """
        print("Realizando predicciones...")
        
        # Tomar el último registro como base para las predicciones
        ultimo_registro = datos.iloc[-1]
        timestamp_base = ultimo_registro['timestamp_num']
        open_base = ultimo_registro['open']
        close_base = ultimo_registro['close']
        volume_base = ultimo_registro['volume']

        # Crear datos para predicciones futuras
        predicciones = []
        for dias in range(1, 6):  # Predicciones para los próximos 5 días
            timestamp_pred = timestamp_base + (dias * 24 * 3600)  # Incrementar 1 día en segundos
            X_pred = pd.DataFrame([[timestamp_pred, open_base, close_base, volume_base]], 
                                  columns=['timestamp_num', 'open', 'close', 'volume'])
            X_pred_scaled = self.scaler.transform(X_pred)

            high_pred = self.modelo_high.predict(X_pred_scaled)[0]
            low_pred = self.modelo_low.predict(X_pred_scaled)[0]

            predicciones.append({
                'timestamp': datetime.fromtimestamp(timestamp_pred).isoformat(),
                'high_pred': high_pred,
                'low_pred': low_pred
            })

        return predicciones

    def guardar_predicciones(self, predicciones):
        """
        Guarda las predicciones en un archivo en formato JSON o CSV.

        :param predicciones: Lista con las predicciones.
        """
        if self.formato_salida == "json":
            with open(self.archivo_salida, "w") as f:
                json.dump(predicciones, f, indent=4)
            print(f"Predicciones guardadas en {self.archivo_salida} (JSON).")
        elif self.formato_salida == "csv":
            df = pd.DataFrame(predicciones)
            df.to_csv(self.archivo_salida, index=False)
            print(f"Predicciones guardadas en {self.archivo_salida} (CSV).")
        else:
            print(f"Formato de salida no reconocido: {self.formato_salida}. Usa 'json' o 'csv'.")

    def mostrar_predicciones(self, predicciones):
        """
        Muestra las predicciones de valores máximos y mínimos en formato tabular.

        :param predicciones: Lista con las predicciones.
        """
        print("\nPredicciones de Valores Máximos y Mínimos:")
        print(tabulate(predicciones, headers="keys", tablefmt="grid"))

    def ejecutar(self):
        """
        Ejecuta el modelo de predicción completo.
        """
        datos = self.cargar_datos()
        if datos.empty:
            print("No se pudieron cargar datos. Finalizando análisis.")
            return

        self.entrenar_modelo(datos)
        predicciones = self.predecir(datos)
        self.guardar_predicciones(predicciones)
        self.mostrar_predicciones(predicciones)

if __name__ == "__main__":
    # Cambia "historial_ETH_BTC.csv" por el nombre de tu archivo generado.
    archivo_entrada = "../datos/historial_ETH_BTC.csv"
    archivo_salida = "../datos/predicciones.json"  # Cambia a "predicciones.csv" si prefieres CSV
    modelo = ModeloPrediccion(archivo_csv=archivo_entrada, archivo_salida=archivo_salida, formato_salida="json")
    modelo.ejecutar()

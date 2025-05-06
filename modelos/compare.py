import ccxt
import json
import pandas as pd
from datetime import datetime
from sklearn.metrics import mean_absolute_error
from tabulate import tabulate

class ComparadorPredicciones:
    def __init__(self, archivo_predicciones, archivo_salida, par="ETH/BTC"):
        """
        Inicializa el comparador de predicciones.

        :param archivo_predicciones: Archivo JSON con las predicciones generadas.
        :param archivo_salida: Archivo CSV donde se guardarán los resultados.
        :param par: Par de criptomonedas a analizar (e.g., "ETH/BTC").
        """
        self.archivo_predicciones = archivo_predicciones
        self.archivo_salida = archivo_salida
        self.par = par

        # Inicializar conexión con Binance
        self.exchange = self.inicializar_exchange()

    def inicializar_exchange(self):
        """
        Inicializa la conexión con Binance.
        """
        try:
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            exchange.load_markets()
            print("[INFO] Conexión con Binance establecida exitosamente.")
            return exchange
        except Exception as e:
            print(f"[ERROR] Error al conectar con Binance: {e}")
            raise

    def cargar_predicciones(self):
        """
        Carga las predicciones desde el archivo JSON.

        :return: Lista con las predicciones.
        """
        try:
            with open(self.archivo_predicciones, "r") as f:
                predicciones = json.load(f)
                print(f"[INFO] Predicciones cargadas exitosamente desde {self.archivo_predicciones}.")
                return predicciones
        except Exception as e:
            print(f"[ERROR] Error al cargar las predicciones: {e}")
            return []

    def obtener_datos_reales(self, predicciones):
        """
        Obtiene los datos reales del mercado para los timestamps de las predicciones.

        :param predicciones: Lista con las predicciones.
        :return: Lista con los valores reales del mercado.
        """
        datos_reales = []
        for prediccion in predicciones:
            timestamp = prediccion["timestamp"]
            dt_obj = datetime.fromisoformat(timestamp)

            try:
                # Convertir timestamp a milisegundos para Binance
                since = int(dt_obj.timestamp() * 1000)

                # Consultar datos históricos del mercado
                ohlcv = self.exchange.fetch_ohlcv(self.par, timeframe="1d", since=since, limit=1)

                if ohlcv:
                    datos_reales.append({
                        "timestamp": timestamp,
                        "high_real": ohlcv[0][2],  # Precio más alto del mercado
                        "low_real": ohlcv[0][3],   # Precio más bajo del mercado
                    })
                else:
                    print(f"[WARN] No se encontraron datos reales para {timestamp}.")
            except Exception as e:
                print(f"[ERROR] Error al obtener datos reales para {timestamp}: {e}")

        return datos_reales

    def sincronizar_y_comparar(self, predicciones, datos_reales):
        """
        Sincroniza las predicciones con los datos reales, calcula las diferencias y genera una tabla detallada.

        :param predicciones: Lista con las predicciones.
        :param datos_reales: Lista con los valores reales del mercado.
        """
        datos_reales_dict = {r["timestamp"]: r for r in datos_reales}
        resultados = []

        for prediccion in predicciones:
            timestamp = prediccion["timestamp"]
            if timestamp in datos_reales_dict:
                real = datos_reales_dict[timestamp]
                resultados.append({
                    "timestamp": timestamp,
                    "high_pred": prediccion["high_pred"],
                    "high_real": real["high_real"],
                    "high_diff": prediccion["high_pred"] - real["high_real"],
                    "low_pred": prediccion["low_pred"],
                    "low_real": real["low_real"],
                    "low_diff": prediccion["low_pred"] - real["low_real"],
                })

        return resultados

    def guardar_resultados(self, resultados):
        """
        Guarda los resultados detallados en un archivo CSV.

        :param resultados: Lista con los resultados de la comparación.
        """
        try:
            df = pd.DataFrame(resultados)
            df.to_csv(self.archivo_salida, index=False)
            print(f"[INFO] Resultados guardados en {self.archivo_salida}.")
        except Exception as e:
            print(f"[ERROR] Error al guardar los resultados en el archivo CSV: {e}")

    def mostrar_tabla(self, resultados):
        """
        Muestra los resultados detallados en formato tabular en la consola.

        :param resultados: Lista con los resultados de la comparación.
        """
        print("\n[COMPARACIÓN DETALLADA]")
        print(tabulate(resultados, headers="keys", tablefmt="grid"))

    def ejecutar(self):
        """
        Ejecuta la comparación completa.
        """
        predicciones = self.cargar_predicciones()
        if not predicciones:
            print("[ERROR] No se pudieron cargar predicciones. Finalizando análisis.")
            return

        datos_reales = self.obtener_datos_reales(predicciones)
        if not datos_reales:
            print("[ERROR] No se pudieron obtener datos reales. Finalizando análisis.")
            return

        resultados = self.sincronizar_y_comparar(predicciones, datos_reales)
        if resultados:
            self.mostrar_tabla(resultados)
            self.guardar_resultados(resultados)
        else:
            print("[INFO] No se generaron resultados debido a falta de sincronización.")

if __name__ == "__main__":
    # Archivo de predicciones, archivo de salida y par de criptomonedas
    archivo_predicciones = "../datos/predicciones.json"
    archivo_salida = "../datos/resultados_comparacion.csv"
    par = "ETH/BTC"

    comparador = ComparadorPredicciones(archivo_predicciones=archivo_predicciones, archivo_salida=archivo_salida, par=par)
    comparador.ejecutar()

import os
import sys
import time
import json
import pandas as pd
from datetime import datetime
import ccxt

# Resolver dinámicamente la carpeta base
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Carpeta actual
BASE_DIR = os.path.dirname(CURRENT_DIR)  # Carpeta 'person'

# Agregar rutas necesarias a sys.path
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

if os.path.join(BASE_DIR, "modelos") not in sys.path:
    sys.path.append(os.path.join(BASE_DIR, "modelos"))

if os.path.join(BASE_DIR, "script") not in sys.path:
    sys.path.append(os.path.join(BASE_DIR, "script"))

# Importar módulos personalizados
from Test.candidatos.person.script.reg_logistica import ModeloPrediccion  # Importar el modelo de predicción
from script.arbitraje_person_model import HistorialBinanceBot  # Importar el bot de historial

class EstrategiaArbitrajeBot:
    def __init__(self, par, timeframe, cantidad_base, intervalo, api_key, api_secret):
        """
        Inicializa el bot maestro para estrategia de arbitraje.

        :param par: Par de criptomonedas a analizar (e.g., "ETH/BTC").
        :param timeframe: Intervalo de tiempo para las velas (e.g., "1h").
        :param cantidad_base: Cantidad base de BTC o ETH para iniciar.
        :param intervalo: Tiempo entre ejecuciones en segundos.
        :param api_key: API Key de Binance.
        :param api_secret: API Secret de Binance.
        """
        self.par = par
        self.timeframe = timeframe
        self.cantidad_base = cantidad_base
        self.intervalo = intervalo
        self.api_key = api_key
        self.api_secret = api_secret
        self.historial_archivo = os.path.join(BASE_DIR, "datos", f"historial_{par.replace('/', '_')}.csv")
        self.predicciones_archivo = os.path.join(BASE_DIR, "datos", "predicciones.json")
        self.exchange = self.inicializar_exchange()

    def inicializar_exchange(self):
        """
        Inicializa la conexión con Binance para ejecutar órdenes.
        """
        try:
            exchange = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True
            })
            exchange.load_markets()
            print("[INFO] Conexión con Binance establecida exitosamente.")
            return exchange
        except Exception as e:
            print(f"[ERROR] Error al conectar con Binance: {e}")
            raise

    def recopilar_datos(self):
        """
        Ejecuta el bot de recolección de datos para actualizar el historial.
        """
        print("[INFO] Iniciando recopilación de datos...")
        try:
            historial_bot = HistorialBinanceBot(par=self.par, timeframe=self.timeframe)
            historial_bot.ejecutar()
            print("[INFO] Recolección de datos completada.")
        except Exception as e:
            print(f"[ERROR] Error durante la recopilación de datos: {e}")

    def actualizar_predicciones(self):
        """
        Ejecuta el modelo de predicción para actualizar las predicciones.
        """
        print("[INFO] Actualizando predicciones...")
        try:
            modelo = ModeloPrediccion(
                archivo_csv=self.historial_archivo,
                archivo_salida=self.predicciones_archivo,
                formato_salida="json"
            )
            modelo.ejecutar()
            print("[INFO] Predicciones actualizadas correctamente.")
        except Exception as e:
            print(f"[ERROR] Error durante la actualización de predicciones: {e}")

    def analizar_predicciones(self):
        """
        Analiza las predicciones generadas y determina acciones.
        """
        print("[INFO] Analizando predicciones...")
        try:
            with open(self.predicciones_archivo, "r") as f:
                predicciones = json.load(f)

            # Obtener la predicción más cercana
            proxima_prediccion = predicciones[0]
            high_pred = proxima_prediccion["high_pred"]
            low_pred = proxima_prediccion["low_pred"]

            # Obtener el precio actual
            ticker = self.exchange.fetch_ticker(self.par)
            precio_actual = ticker['last']

            print(f"[INFO] Precio actual: {precio_actual}, Predicción High: {high_pred}, Predicción Low: {low_pred}")

            # Estrategia de compra/venta basada en predicciones
            if precio_actual < low_pred:
                print("[INFO] Recomendación: Comprar ETH")
                self.ejecutar_orden("buy", self.cantidad_base / precio_actual)  # Compra ETH
            elif precio_actual > high_pred:
                print("[INFO] Recomendación: Vender ETH")
                self.ejecutar_orden("sell", self.cantidad_base)  # Vende ETH
            else:
                print("[INFO] No se recomienda operar en este momento.")
        except Exception as e:
            print(f"[ERROR] Error durante el análisis de predicciones: {e}")

    def ejecutar_orden(self, tipo, cantidad):
        """
        Ejecuta una orden de compra o venta en Binance.

        :param tipo: "buy" o "sell".
        :param cantidad: Cantidad a comprar o vender.
        """
        print(f"[INFO] Ejecutando orden: {tipo} por cantidad: {cantidad}")
        try:
            orden = self.exchange.create_order(
                symbol=self.par,
                type="market",
                side=tipo,
                amount=cantidad
            )
            print(f"[INFO] Orden ejecutada: {orden}")
        except Exception as e:
            print(f"[ERROR] Error al ejecutar la orden: {e}")

    def ejecutar(self):
        """
        Ejecuta el ciclo continuo de la estrategia de arbitraje.
        """
        while True:
            try:
                print(f"\n[ {datetime.now()} ] Ciclo iniciado")
                self.recopilar_datos()
                self.actualizar_predicciones()
                self.analizar_predicciones()
                print(f"[INFO] Ciclo completado. Esperando {self.intervalo} segundos...")
                time.sleep(self.intervalo)
            except Exception as e:
                print(f"[ERROR] Error en el ciclo: {e}. Reintentando en {self.intervalo} segundos...")
                time.sleep(self.intervalo)

if __name__ == "__main__":
    bot = EstrategiaArbitrajeBot(
        par="ETH/BTC",
        timeframe="1h",
        cantidad_base=0.01,  # Ejemplo: 0.01 BTC
        intervalo=3600,  # Ejecutar cada hora
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET")
    )
    bot.ejecutar()

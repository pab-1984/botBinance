import ccxt
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta

class HistorialBinanceBot:
    def __init__(self, par, timeframe):
        """
        Inicializa el bot para obtener el historial del par especificado.

        :param par: Par de criptomonedas a analizar, por ejemplo "BTC/ETH".
        :param timeframe: Intervalo de tiempo de las velas (e.g., '1d', '1h').
        """
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')

        # Confirmar inicialización de atributos
        print(f"Inicializando bot con par: {par} y timeframe: {timeframe}")

        if not self.api_key or not self.api_secret:
            self.cargar_credenciales_desde_archivo()

        self.exchange = self.inicializar_exchange()
        self.par = par
        self.timeframe = timeframe

    def cargar_credenciales_desde_archivo(self):
        """
        Carga las credenciales de API desde un archivo de configuración
        """
        try:
            print("Cargando credenciales desde archivo...")
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.api_key = config.get('binance_api_key')
                self.api_secret = config.get('binance_api_secret')
                print("Credenciales cargadas exitosamente.")
        except FileNotFoundError:
            self.logger.error("Archivo de configuración config.json no encontrado")
            raise ValueError("No se encontraron credenciales de API. Por favor, configura tus credenciales.")

    def inicializar_exchange(self):
        """
        Inicializa la conexión con Binance
        """
        try:
            print("Inicializando conexión con Binance...")
            exchange = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            exchange.load_markets()
            self.logger.info("Conexión con Binance establecida exitosamente")
            return exchange
        except ccxt.AuthenticationError:
            self.logger.error("Error de autenticación. Verifica tus credenciales de API")
            raise

    def verificar_atributos(self):
        """
        Verifica el estado de los atributos del bot.
        """
        print(f"Estado actual del bot:")
        print(f"  Par: {self.par}")
        print(f"  Timeframe: {self.timeframe}")
        print(f"  API Key: {'Configurada' if self.api_key else 'No configurada'}")
        print(f"  API Secret: {'Configurada' if self.api_secret else 'No configurada'}")

    def obtener_historial(self, desde: str) -> pd.DataFrame:
        """
        Obtiene el historial de precios del par especificado.

        :param desde: Fecha de inicio en formato ISO (YYYY-MM-DD).
        :return: DataFrame con datos históricos del par.
        """
        try:
            print(f"Obteniendo historial para el par: {self.par} desde: {desde}")
            # Convertir fecha de inicio a timestamp
            timestamp_desde = int(datetime.fromisoformat(desde).timestamp() * 1000)
            
            # Lista para almacenar las velas históricas
            velas = []
            timestamp_actual = timestamp_desde

            while True:
                print(f"Solicitando datos desde timestamp: {timestamp_actual}")
                # Descargar velas usando fetch_ohlcv
                data = self.exchange.fetch_ohlcv(self.par, self.timeframe, since=timestamp_actual, limit=1000)
                if not data:
                    print("No se recibieron más datos. Finalizando descarga.")
                    break

                velas.extend(data)
                timestamp_actual = data[-1][0] + 1

                # Salir si ya no hay más datos
                if len(data) < 1000:
                    break

            # Convertir a DataFrame
            columnas = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df = pd.DataFrame(velas, columns=columnas)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            self.logger.info(f"Datos históricos descargados: {len(df)} registros.")
            return df
        except Exception as e:
            self.logger.error(f"Error obteniendo historial: {e}")
            return pd.DataFrame()

    def guardar_historial(self, df: pd.DataFrame, archivo: str):
        """
        Guarda el historial en un archivo CSV.

        :param df: DataFrame con los datos históricos.
        :param archivo: Nombre del archivo CSV.
        """
        try:
            print(f"Guardando historial en el archivo: {archivo}")
            df.to_csv(archivo, index=False)
            self.logger.info(f"Historial guardado en {archivo}")
        except Exception as e:
            self.logger.error(f"Error guardando el historial: {e}")

    def ejecutar(self):
        """
        Ejecuta el bot para obtener el historial del último año.
        """
        try:
            self.verificar_atributos()
            # Fecha de inicio hace un año
            fecha_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            historial = self.obtener_historial(fecha_inicio)
            
            if not historial.empty:
                archivo = f"../datos/historial_{self.par.replace('/', '_')}.csv"
                self.guardar_historial(historial, archivo)
            else:
                self.logger.warning("No se obtuvieron datos históricos.")
        except Exception as e:
            self.logger.error(f"Error en la ejecución del bot: {e}")

if __name__ == "__main__":
    bot = HistorialBinanceBot(par="ETH/BTC", timeframe="1h")
    bot.ejecutar()

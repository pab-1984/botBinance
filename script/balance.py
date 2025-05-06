import ccxt
import json
import logging
import os
import pandas as pd
from datetime import datetime

class BinanceSaldoBot:
    def __init__(self, par="ETH/BTC", timeframe="1h", archivo_csv = "../datos/saldo_binance.csv"):
        """
        Inicializa el bot para consultar y guardar el saldo de Binance.

        :param par: Par de criptomonedas a analizar.
        :param timeframe: Intervalo de tiempo.
        :param archivo_csv: Archivo CSV donde se guardará el saldo.
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
        self.archivo_csv = archivo_csv

    def cargar_credenciales_desde_archivo(self):
        """
        Carga las credenciales de API desde un archivo de configuración.
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
        Inicializa la conexión con Binance.
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

    def consultar_saldo(self):
        """
        Consulta el saldo en Binance y lo guarda en un archivo CSV.
        """
        try:
            print("Consultando saldo...")
            balance = self.exchange.fetch_balance()

            # Crear una lista para almacenar los datos
            registros = []
            timestamp = datetime.now().isoformat()

            for moneda, info in balance['total'].items():
                if info > 0:  # Solo incluir monedas con saldo positivo
                    registros.append({
                        "timestamp": timestamp,
                        "symbol": moneda,
                        "amount": round(info, 6)  # Redondear a 6 decimales
                    })

            # Guardar los registros en un archivo CSV
            self.guardar_en_csv(registros)
        except Exception as e:
            print(f"[ERROR] Ocurrió un error al consultar el saldo: {e}")

    def guardar_en_csv(self, registros):
        """
        Guarda los registros de saldo en un archivo CSV.

        :param registros: Lista de diccionarios con la información del saldo.
        """
        try:
            # Crear un DataFrame con los datos actuales
            df_nuevo = pd.DataFrame(registros)

            # Verificar si el archivo ya existe
            if os.path.exists(self.archivo_csv):
                # Leer el archivo existente
                df_existente = pd.read_csv(self.archivo_csv)

                # Concatenar los nuevos registros al archivo existente
                df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
            else:
                # Si no existe, el nuevo registro será el archivo inicial
                df_final = df_nuevo

            # Guardar el DataFrame actualizado en el archivo CSV
            df_final.to_csv(self.archivo_csv, index=False)
            print(f"[INFO] Saldo guardado en {self.archivo_csv}.")
        except Exception as e:
            print(f"[ERROR] Ocurrió un error al guardar el saldo en el archivo CSV: {e}")

if __name__ == "__main__":
    bot = BinanceSaldoBot()
    bot.consultar_saldo()

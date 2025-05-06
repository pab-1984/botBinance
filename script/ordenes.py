import ccxt
import json
import logging
import os
from datetime import datetime, timedelta
import csv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class OrdenesBot:
    def __init__(self, par="ETH/BTC", timeframe="1h", operaciones_archivo="../datos/operaciones.csv", comision=0.001, predicciones_archivo="../datos/predicciones.json", umbral_ganancia=0.5):
        """
        Inicializa el bot para colocar órdenes de compra o venta en Binance.

        :param par: Par de criptomonedas para operar (e.g., "ETH/BTC").
        :param timeframe: Intervalo de tiempo (opcional para consistencia con el login).
        :param operaciones_archivo: Archivo CSV para registrar las operaciones.
        :param comision: Comisión aplicada por operación (default: 0.1% -> 0.001).
        :param predicciones_archivo: Archivo JSON con predicciones de precios.
        :param umbral_ganancia: Ganancia mínima requerida para ejecutar la operación (en porcentaje).
        """
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.operaciones_archivo = operaciones_archivo
        self.comision = comision
        self.predicciones_archivo = predicciones_archivo
        self.umbral_ganancia = umbral_ganancia / 100  # Convertir porcentaje a decimal

        # Inicializar Rich Console
        self.console = Console()

        # Confirmar inicialización de atributos
        self.console.log(f"Inicializando bot para colocar órdenes en par: {par} y timeframe: {timeframe}")

        if not self.api_key or not self.api_secret:
            self.cargar_credenciales_desde_archivo()

        self.exchange = self.inicializar_exchange()
        self.par = par
        self.timeframe = timeframe

    def cargar_credenciales_desde_archivo(self):
        """
        Carga las credenciales de API desde un archivo de configuración.
        """
        try:
            self.console.log("Cargando credenciales desde archivo...")
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.api_key = config.get('binance_api_key')
                self.api_secret = config.get('binance_api_secret')
                self.console.log("Credenciales cargadas exitosamente.")
        except FileNotFoundError:
            self.logger.error("Archivo de configuración config.json no encontrado")
            raise ValueError("No se encontraron credenciales de API. Por favor, configura tus credenciales.")

    def inicializar_exchange(self):
        """
        Inicializa la conexión con Binance.
        """
        try:
            self.console.log("Inicializando conexión con Binance...")
            exchange = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            exchange.load_markets()
            self.console.log("Conexión con Binance establecida exitosamente.")
            return exchange
        except ccxt.AuthenticationError:
            self.logger.error("Error de autenticación. Verifica tus credenciales de API.")
            raise

    def obtener_saldo(self):
        """
        Obtiene el saldo disponible de ETH y BTC.

        :return: Diccionario con saldos de ETH y BTC.
        """
        try:
            balance = self.exchange.fetch_balance()
            saldo_eth = balance['free'].get('ETH', 0)
            saldo_btc = balance['free'].get('BTC', 0)
            return {"ETH": saldo_eth, "BTC": saldo_btc}
        except Exception as e:
            self.console.log(f"[ERROR] Error al obtener el saldo: {e}")
            return {"ETH": 0, "BTC": 0}

    def obtener_precio_actual(self):
        """
        Obtiene el precio actual del par operado.

        :return: Precio actual del par.
        """
        try:
            return self.exchange.fetch_ticker(self.par)['last']
        except Exception as e:
            self.console.log(f"[ERROR] Error al obtener el precio actual: {e}")
            return None

    def obtener_ultima_operacion(self):
        """
        Obtiene la última operación registrada en el archivo CSV.

        :return: Diccionario con los detalles de la última operación o None si no hay operaciones registradas.
        """
        try:
            if not os.path.exists(self.operaciones_archivo):
                self.console.log("[INFO] No se encontró el archivo de operaciones. Comenzando desde cero.")
                return None

            with open(self.operaciones_archivo, mode="r") as f:
                reader = csv.DictReader(f)
                operaciones = list(reader)
                if not operaciones:
                    self.console.log("[INFO] No hay operaciones registradas.")
                    return None
                return operaciones[-1]  # Última operación
        except Exception as e:
            self.console.log(f"[ERROR] Error al leer el archivo de operaciones: {e}")
            return None

    def registrar_operacion(self, moneda_inicial, cantidad_inicial, moneda_final, cantidad_final):
        """
        Registra una operación en el archivo CSV.

        :param moneda_inicial: Moneda inicial antes de la operación.
        :param cantidad_inicial: Cantidad de la moneda inicial.
        :param moneda_final: Moneda obtenida después de la operación.
        :param cantidad_final: Cantidad de la moneda final.
        """
        detalles = {
            "timestamp": datetime.now().isoformat(),
            "moneda_inicial": moneda_inicial,
            "cantidad_inicial": cantidad_inicial,
            "moneda_final": moneda_final,
            "cantidad_final": cantidad_final
        }

        try:
            with open(self.operaciones_archivo, mode="a") as f:
                writer = csv.DictWriter(f, fieldnames=detalles.keys())
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerow(detalles)
            self.console.log(f"[INFO] Operación registrada en {self.operaciones_archivo}.")
        except Exception as e:
            self.console.log(f"[ERROR] Error al registrar la operación: {e}")

    def colocar_orden(self):
        """
        Implementa la lógica principal del bot para decidir si comprar o vender basándose en las cantidades iniciales y finales.
        """
        # Verificar si el archivo de operaciones existe
        if not os.path.exists(self.operaciones_archivo):
            self.console.log("[INFO] Archivo de operaciones no encontrado. Creando uno nuevo...")
            moneda_inicial = input("Ingresa la moneda inicial (ETH o BTC): ").strip().upper()
            cantidad_inicial = float(input(f"Ingresa la cantidad inicial de {moneda_inicial}: ").strip())
            
            # Registrar la operación inicial
            self.registrar_operacion(
                moneda_inicial=moneda_inicial,
                cantidad_inicial=cantidad_inicial,
                moneda_final=moneda_inicial,
                cantidad_final=cantidad_inicial
            )
            self.console.log("[INFO] Operación inicial registrada. Listo para comenzar.")
            return

        # Continuar lógica normal si el archivo existe
        saldo = self.obtener_saldo()
        precio_actual = self.obtener_precio_actual()
        ultima_operacion = self.obtener_ultima_operacion()

        if not precio_actual:
            self.console.log("[WARN] No se pudo obtener el precio actual.")
            return

        if not ultima_operacion:
            self.console.log("[INFO] No hay operaciones previas registradas. Comenzando desde la operación inicial.")
            return

        moneda_inicial = ultima_operacion["moneda_inicial"]
        cantidad_inicial = float(ultima_operacion["cantidad_inicial"])
        moneda_final = ultima_operacion["moneda_final"]
        cantidad_final = float(ultima_operacion["cantidad_final"])

        if moneda_final == "BTC" and saldo["BTC"] > 0:
            # Evaluar si se puede comprar ETH con BTC y obtener más ETH del inicial
            cantidad_estimada_eth = saldo["BTC"] / precio_actual
            ganancia_requerida = cantidad_inicial * (1 + self.umbral_ganancia)

            if cantidad_estimada_eth > ganancia_requerida:
                self.console.log(f"[INFO] Decisión: Comprar ETH con BTC. Cantidad inicial: {cantidad_inicial:.6f} ETH, "
                                 f"Cantidad estimada: {cantidad_estimada_eth:.6f} ETH, "
                                 f"Ganancia mínima requerida: {ganancia_requerida:.6f} ETH")
                self.colocar_orden_mercado("buy", saldo["BTC"] / precio_actual)
                self.registrar_operacion("BTC", saldo["BTC"], "ETH", cantidad_estimada_eth)
            else:
                self.console.log(f"[WARN] No se realiza compra: Cantidad estimada ({cantidad_estimada_eth:.6f} ETH) no supera la ganancia mínima requerida ({ganancia_requerida:.6f} ETH).")

        if moneda_final == "ETH" and saldo["ETH"] > 0:
            # Evaluar si se puede vender ETH por BTC y obtener más BTC del inicial
            cantidad_estimada_btc = saldo["ETH"] * precio_actual
            ganancia_requerida = cantidad_inicial * (1 + self.umbral_ganancia)

            if cantidad_estimada_btc > ganancia_requerida:
                self.console.log(f"[INFO] Decisión: Vender ETH por BTC. Cantidad inicial: {cantidad_inicial:.6f} BTC, "
                                 f"Cantidad estimada: {cantidad_estimada_btc:.6f} BTC, "
                                 f"Ganancia mínima requerida: {ganancia_requerida:.6f} BTC")
                self.colocar_orden_mercado("sell", saldo["ETH"])
                self.registrar_operacion("ETH", saldo["ETH"], "BTC", cantidad_estimada_btc)
            else:
                self.console.log(f"[WARN] No se realiza venta: Cantidad estimada ({cantidad_estimada_btc:.6f} BTC) no supera la ganancia mínima requerida ({ganancia_requerida:.6f} BTC).")


    from rich.panel import Panel

    def mostrar_detalle_orden(self, orden):
        """
        Muestra un dashboard con los detalles de una operación ejecutada.

        :param orden: Detalles de la orden retornados por la API.
        """
        panel = Panel.fit(
            f"[cyan bold]Operación Ejecutada[/cyan bold]\n"
            f"[bold white]ID de la Orden:[/bold white] {orden.get('id')}\n"
            f"[bold white]Par Operado:[/bold white] {orden.get('symbol')}\n"
            f"[bold white]Tipo de Orden:[/bold white] {orden.get('type')}\n"
            f"[bold white]Lado:[/bold white] {orden.get('side')}\n"
            f"[bold white]Cantidad:[/bold white] {orden.get('amount'):.6f}\n"
            f"[bold white]Precio Promedio:[/bold white] {orden.get('average'):.8f}\n"
            f"[bold white]Estado:[/bold white] {orden.get('status')}\n"
            f"[bold white]Fecha y Hora:[/bold white] {datetime.now().isoformat()}",
            title="Detalles de la Operación",
            border_style="green"
        )
        self.console.print(panel)

    def colocar_orden_mercado(self, tipo, cantidad):
        """
        Coloca una orden en el mercado spot.

        :param tipo: 'buy' o 'sell'.
        :param cantidad: Cantidad a operar.
        """
        try:
            self.console.log(f"Intentando colocar una orden de tipo {tipo} para {cantidad:.6f} en {self.par}...")
            orden = self.exchange.create_order(
                symbol=self.par,
                type="market",
                side=tipo,
                amount=cantidad
            )

            if orden:
                self.console.log(f"[INFO] Orden de tipo {tipo} ejecutada exitosamente.")
                self.mostrar_detalle_orden(orden)  # Llamada a la nueva función
            else:
                self.console.log(f"[ERROR] La orden de tipo {tipo} no se ejecutó correctamente.")
        except Exception as e:
            self.console.log(f"[ERROR] Ocurrió un error al colocar la orden de tipo {tipo}: {e}")


if __name__ == "__main__":
    bot = OrdenesBot(par="ETH/BTC", timeframe="1h", operaciones_archivo="../datos/operaciones.csv")
    bot.colocar_orden()
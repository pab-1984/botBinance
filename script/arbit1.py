import asyncio
import ccxt.pro as ccxtpro
import json
import os
import csv
import time
import logging
from datetime import datetime
from rich.console import Console
from rich.table import Table

# Asumimos que ya tienes definida la clase OrdenesBot, la cual reutilizaremos.
class OrdenesBot:
    def __init__(self, par="ETH/BTC", timeframe="1h", operaciones_archivo="../datos/operaciones.csv", comision=0.001, predicciones_archivo="../datos/predicciones.json"):
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.operaciones_archivo = operaciones_archivo
        self.comision = comision
        self.predicciones_archivo = predicciones_archivo
        self.console = Console()
        self.console.log(f"Inicializando bot para colocar órdenes en par: {par} y timeframe: {timeframe}")
        if not self.api_key or not self.api_secret:
            self.cargar_credenciales_desde_archivo()
        self.exchange = self.inicializar_exchange()
        self.par = par
        self.timeframe = timeframe

    def cargar_credenciales_desde_archivo(self):
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
        try:
            balance = self.exchange.fetch_balance()
            saldo_eth = balance['free'].get('ETH', 0)
            saldo_btc = balance['free'].get('BTC', 0)
            return {"ETH": saldo_eth, "BTC": saldo_btc}
        except Exception as e:
            self.console.log(f"[ERROR] Error al obtener el saldo: {e}")
            return {"ETH": 0, "BTC": 0}

    def obtener_precio_actual(self):
        try:
            return self.exchange.fetch_ticker(self.par)['last']
        except Exception as e:
            self.console.log(f"[ERROR] Error al obtener el precio actual: {e}")
            return None

    def cargar_predicciones(self):
        try:
            with open(self.predicciones_archivo, "r") as f:
                predicciones = json.load(f)
                if isinstance(predicciones, list) and len(predicciones) > 0:
                    return predicciones[0]
                return predicciones
        except FileNotFoundError:
            self.console.log(f"[WARN] Archivo de predicciones {self.predicciones_archivo} no encontrado.")
            return None
        except Exception as e:
            self.console.log(f"[ERROR] Error al cargar predicciones: {e}")
            return None

    def obtener_ultima_operacion(self):
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
                return operaciones[-1]
        except Exception as e:
            self.console.log(f"[ERROR] Error al leer el archivo de operaciones: {e}")
            return None

    def mostrar_dashboard(self, saldo, precio_actual, predicciones):
        table = Table(title="Estado Actual del Bot")
        table.add_column("Elemento", justify="left", style="cyan", no_wrap=True)
        table.add_column("Valor", justify="right", style="magenta")
        table.add_row("Saldo ETH", f"{saldo['ETH']:.6f}")
        table.add_row("Saldo BTC", f"{saldo['BTC']:.6f}")
        table.add_row("Precio Actual", f"{precio_actual:.8f}")
        if predicciones:
            table.add_row("Precio Min Predicho", f"{predicciones.get('low_pred', 'N/A'):.8f}")
            table.add_row("Precio Max Predicho", f"{predicciones.get('high_pred', 'N/A'):.8f}")
        else:
            table.add_row("Predicciones", "No disponibles")
        self.console.print(table)

    def colocar_orden(self):
        saldo = self.obtener_saldo()
        precio_actual = self.obtener_precio_actual()
        predicciones = self.cargar_predicciones()
        tiempo_transcurrido = self.tiempo_desde_ultima_operacion()
        self.mostrar_dashboard(saldo, precio_actual, predicciones)
        if precio_actual is None:
            self.console.log("[WARN] No se pudo obtener el precio actual. Orden no colocada.")
            return
        if not predicciones:
            self.console.log("[WARN] No se encontraron predicciones. Se continuará con lógica estándar.")
        ultima_operacion = self.obtener_ultima_operacion()
        if ultima_operacion and ultima_operacion["tipo"] == "sell" and saldo["BTC"] > 0:
            precio_anterior = float(ultima_operacion["precio_promedio"])
            precio_min_predicho = predicciones.get("low_pred", precio_anterior) if predicciones else precio_anterior
            self.console.log(f"Último precio: {precio_anterior}, Precio actual: {precio_actual}, Precio mínimo predicho: {precio_min_predicho}")
            if tiempo_transcurrido and tiempo_transcurrido > 60:
                self.console.log(f"Ha pasado más de 1 hora desde la última operación ({tiempo_transcurrido:.2f} minutos). Evaluando proximidad al precio predicho.")
                if abs(precio_actual - precio_min_predicho) / precio_min_predicho < 0.1:
                    cantidad = saldo["BTC"] / precio_actual
                    self.console.log("Decisión: Comprar ETH con BTC debido a proximidad al precio predicho.")
                    self.colocar_orden_mercado("buy", cantidad)
                    return
            if precio_actual < max(precio_anterior, precio_min_predicho):
                cantidad = saldo["BTC"] / precio_actual
                self.console.log("Decisión: Comprar ETH con BTC")
                self.colocar_orden_mercado("buy", cantidad)
            else:
                self.console.log(f"No se realiza compra: Precio actual ({precio_actual}) >= Máximo ({max(precio_anterior, precio_min_predicho)}).")
        elif ultima_operacion and ultima_operacion["tipo"] == "buy" and saldo["ETH"] > 0:
            precio_anterior = float(ultima_operacion["precio_promedio"])
            self.console.log(f"Último precio: {precio_anterior}, Precio actual: {precio_actual}")
            if tiempo_transcurrido and tiempo_transcurrido > 60:
                self.console.log(f"Ha pasado más de 1 hora desde la última operación ({tiempo_transcurrido:.2f} minutos). Evaluando proximidad al precio predicho.")
                precio_max_predicho = predicciones.get("high_pred", precio_anterior) if predicciones else precio_anterior
                if abs(precio_actual - precio_max_predicho) / precio_max_predicho < 0.1:
                    cantidad = saldo["ETH"]
                    self.console.log("Decisión: Vender ETH por BTC debido a proximidad al precio predicho.")
                    self.colocar_orden_mercado("sell", cantidad)
                    return
            if precio_actual > precio_anterior:
                cantidad = saldo["ETH"]
                self.console.log("Decisión: Vender ETH por BTC")
                self.colocar_orden_mercado("sell", cantidad)
            else:
                self.console.log(f"No se realiza venta: Precio actual ({precio_actual}) <= Último precio ({precio_anterior}).")
        else:
            self.console.log("[WARN] No se pudo determinar la acción a realizar o no hay saldo suficiente.")

    def colocar_orden_mercado(self, tipo, cantidad):
        try:
            self.console.log(f"Intentando colocar una orden de tipo {tipo} para {cantidad} en {self.par}...")
            orden = self.exchange.create_order(
                symbol=self.par,
                type="market",
                side=tipo,
                amount=cantidad
            )
            if orden:
                self.console.log(f"Orden de tipo {tipo} ejecutada exitosamente.")
                self.mostrar_detalle_orden(orden)
                self.registrar_operacion(orden, tipo)
            else:
                self.console.log("[ERROR] La orden de tipo {tipo} no se ejecutó correctamente.")
        except Exception as e:
            self.console.log(f"[ERROR] Ocurrió un error al colocar la orden de tipo {tipo}: {e}")

    def registrar_operacion(self, orden, tipo):
        detalles = {
            "timestamp": datetime.now().isoformat(),
            "id": orden.get("id"),
            "par": orden.get("symbol"),
            "tipo": tipo,
            "cantidad": orden.get("amount"),
            "precio_promedio": orden.get("average"),
            "estado": orden.get("status")
        }
        try:
            with open(self.operaciones_archivo, mode="a") as f:
                writer = csv.DictWriter(f, fieldnames=detalles.keys())
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerow(detalles)
            self.console.log(f"Operación registrada en {self.operaciones_archivo}.")
        except Exception as e:
            self.console.log(f"[ERROR] Error al registrar la operación: {e}")

    def mostrar_detalle_orden(self, orden):
        self.console.log("[DETALLE DE LA ORDEN]")
        self.console.log(f"  - ID de la Orden: {orden.get('id')}")
        self.console.log(f"  - Par Operado: {orden.get('symbol')}")
        self.console.log(f"  - Tipo de Orden: {orden.get('type')}")
        self.console.log(f"  - Lado: {orden.get('side')}")
        self.console.log(f"  - Cantidad: {orden.get('amount')}")
        self.console.log(f"  - Precio Promedio: {orden.get('average')}")
        self.console.log(f"  - Estado: {orden.get('status')}")
        self.console.log(f"  - Fecha y Hora: {datetime.now().isoformat()}")

    def tiempo_desde_ultima_operacion(self):
        ultima_operacion = self.obtener_ultima_operacion()
        if ultima_operacion:
            timestamp_ultima = datetime.fromisoformat(ultima_operacion["timestamp"])
            tiempo_transcurrido = datetime.now() - timestamp_ultima
            return tiempo_transcurrido.total_seconds() / 60
        return None

# Ahora, creamos una subclase que extienda OrdenesBot para incorporar el monitoreo vía WebSocket usando ccxt.pro
class WebSocketOrdenesBot(OrdenesBot):
    async def run_websocket(self):
        # Reconfiguramos la conexión para usar ccxt.pro
        self.console.log("Inicializando conexión WebSocket con ccxt.pro...")
        self.exchange = ccxtpro.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        await self.exchange.load_markets()
        self.console.log("Conexión WebSocket establecida exitosamente.")
        while True:
            try:
                # Usamos watch_ticker para obtener actualizaciones en tiempo real
                ticker = await self.exchange.watch_ticker(self.par)
                current_price = ticker['last']
                self.console.log(f"Precio actual de {self.par}: {current_price:.8f}")
                
                # Aquí puedes integrar la lógica de tu estrategia para decidir cuándo operar.
                # Por ejemplo, podrías evaluar condiciones y, si se cumplen, llamar a self.colocar_orden()
                # En este ejemplo se llama a colocar_orden() de forma condicional (ejemplo simplificado):
                if current_price is not None:
                    # Esta es una condición de ejemplo; en la práctica integrarías tu lógica basada en predicciones
                    if current_price % 2 < 1:  # Condición arbitraria para disparar la orden
                        self.console.log("Condición de ejemplo cumplida, evaluando orden...")
                        self.colocar_orden()
                
                await asyncio.sleep(1)
            except Exception as e:
                self.console.log(f"[ERROR] Error en el monitoreo WebSocket: {e}")
                await asyncio.sleep(5)

async def main():
    bot = WebSocketOrdenesBot(par="ETH/BTC", timeframe="1h", operaciones_archivo="../datos/operaciones.csv")
    await bot.run_websocket()

if __name__ == "__main__":
    asyncio.run(main())

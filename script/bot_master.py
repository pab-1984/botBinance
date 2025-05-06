import os
import time
from arbitraje_person_model import HistorialBinanceBot
from balance import BinanceSaldoBot
from reg_logistica import ModeloPrediccion
from evaluacion_arb_eth import AnalizadorETHBTC
from ordenes import OrdenesBot

class BotMaster:
    def __init__(self):
        """
        Inicializa el bot maestro.
        """
        self.par = "ETH/BTC"
        self.timeframe = "1h"
        self.intervalo = 30  # 0.5 minutos
        self.datos_dir = "../datos/"
        self.historial_archivo = os.path.join(self.datos_dir, "historial_ETH_BTC.csv")
        self.saldo_archivo = os.path.join(self.datos_dir, "saldo_binance.csv")
        self.predicciones_archivo = os.path.join(self.datos_dir, "predicciones.json")
        self.operaciones_archivo = os.path.join(self.datos_dir, "operaciones.csv")

    def recopilar_datos(self):
        """
        Recopila datos históricos del mercado.
        """
        print("[INFO] Recopilando datos históricos...")
        bot = HistorialBinanceBot(par=self.par, timeframe=self.timeframe)
        bot.ejecutar()

    def consultar_saldo(self):
        """
        Consulta y registra el saldo actual.
        """
        print("[INFO] Consultando saldo...")
        bot = BinanceSaldoBot(par=self.par, timeframe=self.timeframe, archivo_csv=self.saldo_archivo)
        bot.consultar_saldo()

    def generar_predicciones(self):
        """
        Genera predicciones basadas en datos históricos.
        """
        print("[INFO] Generando predicciones...")
        modelo = ModeloPrediccion(
            archivo_csv=self.historial_archivo,
            archivo_salida=self.predicciones_archivo,
            formato_salida="json"
        )
        modelo.ejecutar()

    def evaluar_estrategia(self):
        """
        Evalúa estrategias basadas en datos históricos.
        """
        print("[INFO] Evaluando estrategias de arbitraje...")
        analizador = AnalizadorETHBTC(
            archivo_csv=self.historial_archivo,
            cantidad_base=0.001,  # Ajustar según el capital inicial
            moneda_inicial="BTC"
        )
        analizador.ejecutar()

    def ejecutar_ordenes(self):
        """
        Ejecuta órdenes en Binance basadas en la estrategia.
        """
        print("[INFO] Ejecutando órdenes...")
        bot = OrdenesBot(operaciones_archivo=self.operaciones_archivo)
        bot.colocar_orden()

    def run(self):
        """
        Ejecuta el ciclo completo del bot.
        """
        while True:
            try:
                self.recopilar_datos()
                self.consultar_saldo()
                self.generar_predicciones()
                self.evaluar_estrategia()
                self.ejecutar_ordenes()
                print(f"[INFO] Ciclo completo ejecutado. Esperando {self.intervalo} segundos...")
                time.sleep(self.intervalo)
            except Exception as e:
                print(f"[ERROR] Error en el ciclo principal: {e}")
                time.sleep(self.intervalo)

if __name__ == "__main__":
    bot_master = BotMaster()
    bot_master.run()

import pandas as pd
from tabulate import tabulate

class AnalizadorETHBTC:
    def __init__(self, archivo_csv, cantidad_base=0.001, moneda_inicial="BTC"):
        """
        Inicializa el analizador para ETH/BTC.

        :param archivo_csv: Nombre del archivo CSV con los datos históricos.
        :param cantidad_base: Cantidad inicial para la simulación.
        :param moneda_inicial: Moneda inicial de la simulación ("BTC" o "ETH").
        """
        self.archivo_csv = archivo_csv
        self.cantidad_base = cantidad_base
        self.moneda_inicial = moneda_inicial.upper()

    def cargar_datos(self):
        """
        Carga los datos históricos desde el archivo CSV.

        :return: DataFrame con los datos cargados.
        """
        try:
            print(f"Cargando datos desde {self.archivo_csv}...")
            datos = pd.read_csv(self.archivo_csv, parse_dates=['timestamp'])
            print(f"Datos cargados exitosamente: {len(datos)} registros.")
            return datos
        except Exception as e:
            print(f"Error cargando el archivo: {e}")
            return pd.DataFrame()

    def simular_operaciones(self, datos):
        """
        Simula operaciones de compra y venta en base al comportamiento de ETH/BTC.

        :param datos: DataFrame con los datos históricos.
        :return: Lista de operaciones realizadas.
        """
        operaciones = []

        if self.moneda_inicial == "BTC":
            self.simular_desde_btc(datos, operaciones)
        elif self.moneda_inicial == "ETH":
            self.simular_desde_eth(datos, operaciones)
        else:
            print("Moneda inicial no válida. Usa 'BTC' o 'ETH'.")
            return []

        return operaciones

    def simular_desde_btc(self, datos, operaciones):
        """
        Simula operaciones iniciando con BTC.

        :param datos: DataFrame con los datos históricos.
        :param operaciones: Lista donde se almacenarán las operaciones realizadas.
        """
        btc_actual = self.cantidad_base
        eth_actual = 0
        en_posesion_eth = False

        for i, fila in datos.iterrows():
            precio_eth_btc = fila['close']

            if not en_posesion_eth:
                if i > 0 and fila['close'] < datos.iloc[i - 1]['close']:
                    eth_actual = btc_actual / precio_eth_btc
                    operaciones.append({
                        'timestamp': fila['timestamp'],
                        'accion': 'Comprar ETH',
                        'precio_eth_btc': precio_eth_btc,
                        'btc_usado': btc_actual,
                        'eth_obtenido': eth_actual,
                        'btc_final': 0
                    })
                    btc_actual = 0
                    en_posesion_eth = True
            else:
                if i > 0 and fila['close'] > datos.iloc[i - 1]['close']:
                    btc_actual = eth_actual * precio_eth_btc
                    operaciones.append({
                        'timestamp': fila['timestamp'],
                        'accion': 'Vender ETH',
                        'precio_eth_btc': precio_eth_btc,
                        'eth_usado': eth_actual,
                        'btc_obtenido': btc_actual,
                        'btc_final': btc_actual
                    })
                    eth_actual = 0
                    en_posesion_eth = False

    def simular_desde_eth(self, datos, operaciones):
        """
        Simula operaciones iniciando con ETH.

        :param datos: DataFrame con los datos históricos.
        :param operaciones: Lista donde se almacenarán las operaciones realizadas.
        """
        eth_actual = self.cantidad_base
        btc_actual = 0
        en_posesion_btc = False

        for i, fila in datos.iterrows():
            precio_eth_btc = fila['close']

            if not en_posesion_btc:
                if i > 0 and fila['close'] > datos.iloc[i - 1]['close']:
                    btc_actual = eth_actual * precio_eth_btc
                    operaciones.append({
                        'timestamp': fila['timestamp'],
                        'accion': 'Comprar BTC',
                        'precio_eth_btc': precio_eth_btc,
                        'eth_usado': eth_actual,
                        'btc_obtenido': btc_actual,
                        'eth_final': 0
                    })
                    eth_actual = 0
                    en_posesion_btc = True
            else:
                if i > 0 and fila['close'] < datos.iloc[i - 1]['close']:
                    eth_actual = btc_actual / precio_eth_btc
                    operaciones.append({
                        'timestamp': fila['timestamp'],
                        'accion': 'Vender BTC',
                        'precio_eth_btc': precio_eth_btc,
                        'btc_usado': btc_actual,
                        'eth_obtenido': eth_actual,
                        'eth_final': eth_actual
                    })
                    btc_actual = 0
                    en_posesion_btc = False

    def filtrar_operaciones_favorables(self, operaciones):
        """
        Filtra las operaciones donde la cantidad final es mayor que la inicial.

        :param operaciones: Lista de operaciones realizadas.
        :return: Lista de operaciones favorables.
        """
        if self.moneda_inicial == "BTC":
            return [op for op in operaciones if op.get('btc_final', 0) > self.cantidad_base]
        elif self.moneda_inicial == "ETH":
            return [op for op in operaciones if op.get('eth_final', 0) > self.cantidad_base]

    def guardar_operaciones_favorables(self, operaciones, archivo_salida="operaciones_favorables.csv"):
        """
        Guarda las operaciones favorables en un archivo CSV.

        :param operaciones: Lista de operaciones favorables.
        :param archivo_salida: Nombre del archivo CSV donde se guardarán las operaciones.
        """
        if not operaciones:
            print("No se encontraron operaciones favorables para guardar.")
            return

        df = pd.DataFrame(operaciones)
        df.to_csv(archivo_salida, index=False)
        print(f"Operaciones favorables guardadas en {archivo_salida}.")

    def ejecutar(self):
        """
        Ejecuta la simulación de operaciones.
        """
        datos = self.cargar_datos()
        if datos.empty:
            print("No se pudieron cargar datos. Finalizando análisis.")
            return

        operaciones = self.simular_operaciones(datos)
        operaciones_favorables = self.filtrar_operaciones_favorables(operaciones)
        self.guardar_operaciones_favorables(operaciones_favorables)

if __name__ == "__main__":
    # Cambia "historial_ETH_BTC.csv" por el nombre de tu archivo generado.
    archivo = "../datos/historial_ETH_BTC.csv"
    moneda_inicial = "BTC"  # Cambia a "ETH" si deseas iniciar con ETH
    analizador = AnalizadorETHBTC(archivo_csv=archivo, cantidad_base=0.001, moneda_inicial=moneda_inicial)
    analizador.ejecutar()

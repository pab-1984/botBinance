
# Bot de Estrategia de Arbitraje
Este proyecto implementa un bot modular para ejecutar estrategias de arbitraje en el mercado spot de Binance. El bot utiliza datos históricos, genera predicciones de precios futuros y ejecuta órdenes de compra/venta basadas en las predicciones.

Estructura del Proyecto
```
person/
│
├── datos/                     # Datos generados por el bot
│   ├── historial_ETH_BTC.csv  # Datos históricos del par ETH/BTC.
│   ├── saldo_binance.csv      # Registros del saldo en Binance.
│   ├── predicciones.json      # Predicciones generadas por el modelo.
│   └── resultados_comparacion.csv # Comparación entre predicciones y datos reales.
│
├── modelos/                   # Scripts relacionados con el modelo de predicción
│   ├── reg_logistica.py       # Modelo de regresión lineal para predicciones.
│   └── compare.py             # Compara predicciones con datos reales.
│
├── script/                    # Scripts principales del bot
│   ├── arbitraje-person-model.py # Recopila datos históricos desde Binance.
│   ├── balance.py             # Consulta y guarda el saldo en Binance.
│   ├── estrategia_arbitraje.py # Orquestador principal del bot.
│   ├── evaluacion-arb-eth.py  # Simula y evalúa estrategias de arbitraje.
│   └── ordenes.py             # Coloca órdenes en Binance.
```
## Instalación
Clona este repositorio:

```
git clone https://github.com/tu_usuario/tu_repositorio.git
cd tu_repositorio
```

## Instala las dependencias:

```
pip install -r requirements.txt
```

## Configura tus credenciales de Binance:

Usa variables de entorno:
```
export BINANCE_API_KEY="tu_api_key"
export BINANCE_API_SECRET="tu_api_secret"
```
O crea un archivo config.json en el directorio raíz con este contenido:
json

```
{
    "binance_api_key": "tu_api_key",
    "binance_api_secret": "tu_api_secret"
}
```
Uso
### 1. Recopilar Datos Históricos
Ejecuta arbitraje-person-model.py para obtener datos históricos del par ETH/BTC:

bash
Copy code
python3 script/arbitraje-person-model.py
Salida: Archivo historial_ETH_BTC.csv en la carpeta datos/.
### 2. Consultar Saldo
Ejecuta balance.py para consultar y guardar tu saldo en Binance:

```
python3 script/balance.py
Salida: Archivo saldo_binance.csv en la carpeta datos/.
```
### 3. Generar Predicciones
Ejecuta reg_logistica.py para entrenar el modelo y generar predicciones:
```
python3 modelos/reg_logistica.py
Entrada: Archivo historial_ETH_BTC.csv.
Salida: Archivo predicciones.json.
```
### 4. Comparar Predicciones
Ejecuta compare.py  para comparar predicciones con datos reales:

```
python3 modelos/compare.py
Entrada: Archivo predicciones.json.
Salida: Archivo resultados_comparacion.csv.
```

### 5. Ejecutar Estrategias
Ejecuta estrategia_arbitraje.py para orquestar la estrategia completa:

```
python3 script/estrategia_arbitraje.py
```
Este script:

Recopila datos históricos.
Genera predicciones.
Decide si ejecutar órdenes de compra/venta.
Carpeta script/: Detalle de Archivos
arbitraje-person-model.py:

Recopila datos históricos de precios desde Binance y los guarda en un archivo CSV.
balance.py:

Consulta el saldo de Binance y lo guarda en un archivo CSV.
estrategia_arbitraje.py:

Orquestador principal que integra todas las funcionalidades del bot.
evaluacion-arb-eth.py:

Simula estrategias de arbitraje para ETH/BTC y evalúa su rendimiento.
ordenes.py:

Coloca órdenes de compra en el mercado spot de Binance.
Mejoras Futuras
Automatización:
Usar un orquestador para ejecutar scripts periódicamente.
Persistencia Avanzada:
Migrar de archivos CSV a una base de datos para mayor eficiencia.
Visualización de Datos:
Crear gráficos para analizar predicciones frente a datos reales.
Contribuciones
Haz un fork del repositorio.
Crea una nueva rama:
bash
Copy code
git checkout -b mi-nueva-funcionalidad
Realiza tus cambios y haz commit:
bash
Copy code
git commit -m "Agrego nueva funcionalidad"
Envía un pull request.
Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.

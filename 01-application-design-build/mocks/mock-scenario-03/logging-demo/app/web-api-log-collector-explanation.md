
# web-api.py

Este código implementa una API web en Python usando Flask con un sistema de logging avanzado y simulación de errores/carga. Te resumo sus funciones principales:

### 🛠️ Funcionalidad del código
1. Configuración de logs en distintos archivos:

access.log → registra todas las peticiones y respuestas (método, ruta, IP, agente, código de estado, etc.).

error.log → guarda errores de la aplicación (fallos simulados, validaciones, excepciones).

application.log → registra eventos internos de la aplicación (acciones, warnings, tareas de fondo).

2. Endpoints expuestos por la API:

/health → chequeo de salud, devuelve estado "healthy".

/users (GET) → lista todos los usuarios simulados en memoria.

/users/<id> (GET) → obtiene un usuario específico.

/users (POST) → crea un nuevo usuario, con validaciones y posibilidad de error simulado.

/simulate-load → genera carga artificial, múltiples logs y errores simulados para probar observabilidad.

3. Middleware de logging:

@app.before_request → registra cada petición entrante.

@app.after_request → registra cada respuesta, incluyendo un tiempo de procesamiento simulado.

4. Simulación de errores y carga:

Probabilidad de error en /users (10%).

Probabilidad de error en creación de usuario (15%).

Probabilidad de errores durante la simulación de carga (20%).

5. Tareas en segundo plano:

Un hilo (background_logger) genera logs periódicos cada 30 segundos simulando tareas de mantenimiento (limpieza de caché, chequeo de memoria, etc.).

6. Manejo de señales del sistema:

Captura SIGINT y SIGTERM para apagar la aplicación de forma ordenada, registrando el evento.

7. Ejecución del servidor Flask:

Corre en 0.0.0.0:8080, multihilo, sin modo debug.


### ✅ Beneficios de esta implementación
Observabilidad completa: logs separados para accesos, errores y eventos internos.

Resiliencia y pruebas: simula fallos y carga para validar cómo se comporta el sistema bajo estrés.

Mantenimiento continuo: tareas en segundo plano que generan métricas y alertas.

Escalabilidad y buenas prácticas: separación de responsabilidades entre API, logging y simulación.

Preparación para despliegue en contenedores/Kubernetes: directorio /logs puede montarse en volúmenes compartidos (ideal para sidecar de logging).

En pocas palabras: este código es una API de ejemplo con usuarios simulados y un sistema robusto de logging y monitoreo, diseñada para probar cómo se comporta una aplicación bajo carga y errores, y cómo se integraría con un patrón Sidecar de observabilidad.

# log-collector.py

Este código implementa un recolector de logs en Python que monitorea archivos .log, procesa sus líneas, las guarda en formato JSON y genera estadísticas periódicas. Aquí tienes una explicación detallada por secciones:

🧠 Propósito general
El script define una clase LogCollector que:

Lee archivos de log en /logs

Procesa cada línea (como JSON o texto plano)

Guarda los logs procesados en /collected-logs

Genera estadísticas sobre el proceso

Ejecuta todo en hilos paralelos

🧱 Componentes principales
1. Configuración inicial

```python
logging.basicConfig(...)
logger = logging.getLogger('log-collector')

```

Configura el sistema de logging para registrar eventos con timestamp, nombre, nivel y mensaje.

2. Clase LogCollector
🔧 __init__

Define rutas de entrada/salida.
Inicializa estructuras para:
-Posiciones de lectura por archivo (file_positions)
-Logs recolectados (collected_logs)
-Crea el directorio de salida si no existe.

📖 read_log_file(file_path)
Lee nuevas líneas desde la última posición registrada en un archivo.
Actualiza la posición para evitar leer líneas duplicadas.

🧪 process_log_line(line, source_file)
Intenta interpretar la línea como JSON.

Si falla, la trata como texto plano.

Añade metadatos como:
-Archivo fuente
-Timestamp de recolección
-Nivel de log (por defecto: INFO)

📥 collect_logs()
-Busca archivos .log en /logs.
-Lee nuevas líneas y las procesa.
-Agrupa los logs por archivo fuente.
-Se ejecuta continuamente en un hilo.

📤 write_collected_logs()
-Cada 5 segundos, escribe los logs recolectados en archivos separados por fuente.
-Los guarda en formato JSON línea por línea.
-Limpia los logs ya escritos.

📊 generate_collection_stats()
-Cada 30 segundos, genera estadísticas como:
-Número de archivos monitoreados
-Posiciones de lectura
-Cantidad de logs pendientes por archivo
-Guarda las estadísticas en collection_stats.json.

▶️ run()
Inicia tres hilos:

-Recolección de logs
-Escritura de logs
-Generación de estadísticas
-Mantiene el programa vivo hasta que se interrumpe (Ctrl+C).

🏁 Ejecución
python
if __name__ == '__main__':
    collector = LogCollector()
    collector.run()
Crea una instancia del recolector y lo pone en marcha.



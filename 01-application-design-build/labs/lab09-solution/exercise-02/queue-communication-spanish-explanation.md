Este manifiesto de Kubernetes implementa un sistema distribuido de procesamiento de tareas usando un Pod con múltiples contenedores y una ConfigMap que contiene scripts en Python. Aquí te explico todos los detalles clave:

🧾 1. ConfigMap: queue-scripts

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: queue-scripts
data:
  queue-manager.py: ...
  producer.py: ...
  consumer.py: ...
  monitor.py: ...
```

¿Qué hace?
Almacena scripts Python como texto plano.

Se monta como volumen en los contenedores para que puedan ejecutar los scripts sin necesidad de incluirlos en la imagen del contenedor.

🧠 2. Script queue-manager.py
Define una clase FileQueue que gestiona una cola persistente en disco usando un archivo JSON.

Funciones principales:
put(item): añade un ítem a la cola.

get(): obtiene el primer ítem (FIFO).

size(): devuelve el tamaño de la cola.

Usa fcntl.flock para evitar condiciones de carrera entre procesos concurrentes.

🏭 3. Script producer.py
Simula un productor de tareas que genera trabajos aleatorios y los añade a la cola.

Detalles:
Crea tareas con tipos como process_image, send_email, etc.

Cada tarea tiene un id, timestamp, priority y data.

Produce tareas con una frecuencia variable (entre 2 y 6 segundos).

🧑‍🔧 4. Script consumer.py
Simula un consumidor de tareas que toma trabajos de la cola y los procesa.

Detalles:
Procesa cada tipo de tarea con un tiempo diferente.

Guarda los resultados como archivos JSON en /shared-results.

Usa HOSTNAME para identificar qué contenedor procesó la tarea.

📈 5. Script monitor.py
Actúa como monitor del sistema, mostrando estadísticas en tiempo real.

Funciones:
Muestra el tamaño actual de la cola.

Cuenta tareas completadas.

Calcula el tiempo promedio de procesamiento.

Agrupa tareas por tipo.

📦 6. Pod queue-communication
```yaml
kind: Pod
metadata:
  name: queue-communication
spec:
  containers:
    - producer
    - consumer-1
    - consumer-2
    - monitor
```

Contenedores:
Producer: ejecuta producer.py.

Consumer-1 y Consumer-2: ejecutan consumer.py en paralelo.

Monitor: ejecuta monitor.py.

Volúmenes compartidos:
queue-scripts: montado desde la ConfigMap.

shared-queue: almacena la cola en tasks.json.

shared-results: almacena los resultados de procesamiento.

🧩 ¿Qué demuestra este diseño?
Este sistema simula un patrón clásico de productor-consumidor con monitoreo, usando solo herramientas básicas de Kubernetes:

ConfigMap	Distribuye scripts Python
emptyDir	Volumen compartido para datos temporales
Producer	Genera tareas
Consumers	Procesan tareas
Monitor	    Observa y reporta métricas






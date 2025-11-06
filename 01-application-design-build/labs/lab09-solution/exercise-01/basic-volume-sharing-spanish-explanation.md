Este manifiesto de Kubernetes define un Pod llamado volume-sharing-demo que contiene tres contenedores que comparten un volumen llamado shared-storage. El objetivo es demostrar cómo varios contenedores dentro de un mismo Pod pueden leer y escribir datos en un volumen compartido. Vamos a desglosarlo paso a paso 🧩:

🧾 Estructura general
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-sharing-demo
  labels:
    app: volume-demo
```
apiVersion: Versión de la API de Kubernetes.

kind: Tipo de recurso, en este caso un Pod.

metadata: Nombre y etiquetas del Pod.

📦 Volumen compartido
```yaml
volumes:
- name: shared-storage
  emptyDir: {}
```

Se define un volumen temporal llamado shared-storage usando emptyDir.

Este volumen se crea cuando el Pod inicia y se elimina cuando el Pod termina.

Todos los contenedores montan este volumen en la ruta /shared-data. Se borra cuando el Pod se elimina.

🧑‍🔧 Contenedor data-producer
Este contenedor genera datos continuamente y los escribe en el volumen compartido.

🔄 Comportamiento:
Inicia un contador.

Funciones clave:
Crea un archivo producer.log con entradas de texto.

Genera un archivo current-data.json con datos estructurados.

Usa un bucle infinito con sleep 5 para escribir cada 5 segundos.

Montaje de volumen:
```yaml
volumeMounts:
- name: shared-storage
  mountPath: /shared-data
```
Esto permite que el contenedor escriba en /shared-data, que está vinculado al volumen compartido.

📥 Contenedor 2: data-consumer
Este contenedor espera a que el productor cree datos, luego los lee y genera un archivo consumer.log.

Funciones clave:
Espera hasta que exista producer.log.

Cuenta las líneas (entradas) del archivo.

Muestra el contenido de current-data.json.

Escribe un resumen en consumer.log cada 10 segundos.

📊 Contenedor 3: data-monitor
Este contenedor actúa como un observador del sistema.

Funciones clave:
Espera 10 segundos para que los otros contenedores arranquen.

Cada 15 segundos:

Muestra cuántas entradas hay en producer.log y consumer.log.

Muestra el uso de disco del volumen compartido.

🧠 ¿Qué demuestra este Pod?
Este ejemplo muestra cómo varios contenedores dentro de un mismo Pod pueden comunicarse y compartir datos usando un volumen emptyDir. Es útil para entender patrones de diseño como:

Productor-consumidor

Monitoreo interno

Sincronización por archivos compartidos
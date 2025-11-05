Este manifiesto de Kubernetes define una arquitectura de pod con sidecar que genera, analiza y almacena logs de forma persistente.

📦 1. PersistentVolumeClaim: log-storage

```yaml
yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: log-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```
Este recurso solicita 1 GiB de almacenamiento persistente en el clúster.

ReadWriteOnce: solo puede ser montado en lectura/escritura por un único pod a la vez.

Se usará para guardar logs que persisten incluso si el pod se reinicia o se elimina.

2. Pod: persistent-log-demo
Este pod tiene dos contenedores y dos volúmenes:

🧱 A. Contenedor app (generador de logs)
Imagen: python:3.11-alpine

Ejecuta un script que:

Configura logging en /app-logs/application.log

Genera logs de tipo INFO, WARNING y ERROR cada pocos segundos

Imprime en consola el número de evento generado

🔁 Este contenedor simula una aplicación que genera actividad de logs constantemente.

🧱 B. Contenedor log-aggregator (sidecar analizador)
Imagen: busybox:1.35

Script en shell que:

Espera a que exista el archivo de logs

Cada 10 segundos:

Cuenta cuántos logs hay de cada tipo (INFO, WARNING, ERROR)

Escribe un resumen en /persistent-logs/summary.log

Extrae los errores (ERROR) a /persistent-logs/errors.log

📊 Este contenedor procesa los logs y los guarda en un volumen persistente.

📁 3. Volúmenes
yaml
volumes:
- name: app-logs
  emptyDir: {}
- name: persistent-logs
  persistentVolumeClaim:
    claimName: log-storage
app-logs: Volumen temporal compartido entre los dos contenedores para escribir y leer los logs.

persistent-logs: Volumen persistente basado en el PersistentVolumeClaim, donde se guardan los resúmenes y errores.

🔄 Interacción entre contenedores
Contenedor	Escribe en	             Lee desde	                 Propósito
app	        /app-logs/application.log	—	                 Genera logs
log-aggregator	/persistent-logs/*.log	     /app-logs/application.log	 Procesa y archiva logs

🧠 ¿Por qué es útil?
Separación de responsabilidades: la app genera logs, el sidecar los procesa.

Persistencia: los logs procesados sobreviven reinicios del pod.

Escalabilidad: puedes montar el volumen en otros pods para análisis externo.



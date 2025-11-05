Este manifiesto de Kubernetes define una arquitectura de pod con sidecars para procesar y reenviar logs de Nginx. Vamos por partes:

🧩 1. ConfigMap: log-processor-config
Este ConfigMap contiene un archivo Python (processor.py) que:

Lee el archivo de logs de Nginx (access.log)

Parsea cada línea usando expresiones regulares

Convierte los datos en JSON estructurado

Clasifica la severidad del log (INFO, WARN, ERROR)

Genera alertas si el código de estado HTTP es 5xx

🔍 El script espera a que el archivo exista, lo sigue en tiempo real (tail -f estilo Python), y emite alertas por stderr.

🧩 2. Pod: advanced-sidecar-demo
Este pod tiene tres contenedores:

🧱 A. web-app (contenedor principal)
Imagen: nginx:1.24-alpine

Expone el puerto 80

Usa una configuración personalizada de Nginx desde nginx-custom-config

Monta el volumen shared-logs en /var/log/nginx para que los logs estén disponibles para los sidecars

🧱 B. log-processor (sidecar de procesamiento)
Imagen: python:3.11-alpine

Ejecuta el script processor.py desde el ConfigMap

Monta:

/shared-logs para leer los logs

/scripts para acceder al script Python

Tiene límites de CPU y memoria definidos

🔁 Este contenedor transforma los logs en JSON y genera alertas si detecta errores HTTP 5xx.

🧱 C. log-forwarder (sidecar de reenvío)
Imagen: busybox:1.35

Script en shell que:

Monitorea el archivo access.log

Cuenta las líneas nuevas

Simula el envío de logs a un sistema externo

Monta /shared-logs para acceder al archivo

🔁 Este contenedor no analiza los logs, solo detecta cambios y los "envía".

🧩 3. ConfigMap: nginx-custom-config
Define una configuración personalizada para Nginx:

Ruta / sirve contenido estático

Ruta /api devuelve un JSON con timestamp

Ruta /error devuelve un error 500 simulado

Define access_log y error_log en /var/log/nginx

🔄 Comunicación entre contenedores
Todos los contenedores comparten el volumen shared-logs (emptyDir), lo que permite:

Nginx escribir los logs

El procesador leer y analizar

El reenviador detectar nuevos logs

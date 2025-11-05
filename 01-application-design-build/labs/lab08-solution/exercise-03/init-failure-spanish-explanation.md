Este manifiesto de Kubernetes define un Pod llamado init-failure-demo que ilustra cómo funcionan los init containers (contenedores de inicialización) y qué ocurre cuando uno de ellos falla. Vamos a desglosarlo paso a paso 🧩:

🧾 Estructura general

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-failure-demo
```  

apiVersion: Versión de la API de Kubernetes.

kind: Tipo de recurso, en este caso un Pod.

metadata.name: Nombre del Pod.

⚙️ Especificación del Pod (spec)
📦 Volumen compartido

```yaml
volumes:
- name: shared
  emptyDir: {}
```

Se define un volumen temporal llamado shared que será usado por los init containers para compartir datos.

🧨 Init Containers
Los init containers se ejecutan secuencialmente antes de que arranquen los contenedores principales. Si uno falla, los siguientes no se ejecutan y el Pod no se inicia.

✅ init-success
```yaml
- name: init-success
  image: busybox:1.35
  command:
    echo "Successful init container"
    echo "setup_complete=true" > /shared/status.txt
    exit 0
```
Este contenedor escribe un archivo en el volumen compartido indicando que la configuración se completó.

Termina exitosamente con exit 0.

❌ init-failure
```yaml
- name: init-failure
  image: busybox:1.35
  command:
    echo "This init container will fail after checking previous step"
    if [ -f /shared/status.txt ]; then
      cat /shared/status.txt
    fi
    echo "Simulating failure..."
    exit 1
```
Verifica si el archivo creado por el contenedor anterior existe.

Imprime su contenido.

Luego falla intencionalmente con exit 1.

🚫 init-never-runs
```yaml
- name: init-never-runs
  ...
```
Este contenedor nunca se ejecutará porque el anterior falló.

🧱 Contenedor principal (main-app)
```yaml
- name: main-app
  image: busybox:1.35
  command:
    echo "Main application starting..."
    while true; do
      echo "App running..."
      sleep 30
    done
```
Este contenedor nunca se iniciará porque los init containers no completaron exitosamente.


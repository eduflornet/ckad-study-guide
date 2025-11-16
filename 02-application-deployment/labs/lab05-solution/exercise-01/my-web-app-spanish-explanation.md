# my-web-app

## values.yaml

📦 Configuración general
replicaCount: 2 Número de réplicas del Deployment. Se desplegarán 2 pods de tu aplicación.

image

repository: nginx → Imagen base que se usará (Nginx).

tag: "1.21" → Versión de la imagen.

pullPolicy: IfNotPresent → Solo descarga la imagen si no está ya en el nodo.

imagePullSecrets: [] → Lista de secretos para acceder a repositorios privados (vacío = no se usan).

nameOverride / fullnameOverride Permiten sobrescribir el nombre generado por Helm para los recursos.

👤 Service Account
serviceAccount.create: true → Se crea una cuenta de servicio específica para los pods.
annotations: {} → Puedes añadir anotaciones personalizadas.
name: "" → Si lo dejas vacío, Helm genera un nombre automáticamente.

🛡️ Seguridad
podSecurityContext.fsGroup: 2000 → Grupo de archivos dentro del contenedor.

securityContext
capabilities.drop: ALL → Elimina todas las capacidades de Linux por defecto.
readOnlyRootFilesystem: true → El sistema de archivos raíz es solo lectura.
runAsNonRoot: true → Obliga a ejecutar como usuario no root.
runAsUser: 1000 → UID del usuario dentro del contenedor.
Esto endurece la seguridad del pod.

🌐 Servicio e Ingress
service
type: ClusterIP → Servicio interno en el cluster.
port: 80 → Expone el puerto 80.
ingress
enabled: false → No se crea un Ingress por defecto.
hosts → Configuración de host y paths si lo habilitas.
tls: [] → TLS deshabilitado por defecto.

⚙️ Recursos
resources
limits → Máximo de CPU (100m) y memoria (128Mi).
requests → Recursos mínimos garantizados (50m CPU, 64Mi memoria).

📈 Autoscaling
autoscaling.enabled: false → No se activa el Horizontal Pod Autoscaler.
Si lo activas, puedes definir minReplicas, maxReplicas y el % de CPU objetivo.

🗂️ Scheduling
nodeSelector, tolerations, affinity → Vacíos por defecto. Sirven para controlar en qué nodos se despliegan los pods.

⚙️ Configuración de la aplicación
app.environment: production → Entorno de ejecución.
app.debug: false → Desactiva modo debug.

features
enableMetrics: true → Activa métricas.
enableHealthCheck: true → Activa chequeos de salud.

🗄️ Base de datos
database.enabled: false → No se despliega base de datos.

Si lo habilitas:
host, port, name, username, password → Parámetros de conexión.
existingSecret → Puedes usar un secreto de Kubernetes para credenciales.

⚡ Redis
redis.enabled: false → No se despliega Redis.

Si lo habilitas:
host, port, password → Configuración de conexión.

✅ En resumen: este values.yaml define un despliegue seguro y básico de una aplicación web con Nginx, 2 réplicas, servicio interno en el cluster, recursos limitados, y configuraciones opcionales para base de datos y Redis.

## Task 1.4: Test Initial Chart

```sh
# Validate the chart
helm lint my-web-app/
```

```sh
# Render templates to see output
helm template my-web-app my-web-app/
```

Ese comando de Helm lo que hace es renderizar las plantillas del chart y mostrar el manifiesto resultante en YAML, sin instalar nada en el clúster.

📖 Desglose del comando
helm template → Renderiza las plantillas de un chart local o remoto usando los valores (values.yaml y/o --set) y devuelve los manifiestos Kubernetes listos para aplicar.

my-web-app → Es el release name, el nombre lógico que Helm asignaría a la instalación.

my-web-app/ → Es la ruta al chart (en este caso un directorio local llamado my-web-app).

🔎 Qué ocurre al ejecutarlo
Helm lee el chart en my-web-app/ (incluyendo Chart.yaml, values.yaml, y las plantillas en templates/).

Sustituye las variables de las plantillas con los valores definidos en values.yaml (o los que pases con --set).

Genera los manifiestos Kubernetes (Deployment, Service, ConfigMap, etc.).

Los imprime en la salida estándar (tu terminal). 👉 No se crea nada en el clúster, es solo una “vista previa”.

🎯 Usos típicos
Verificar qué recursos se van a desplegar antes de hacer helm install.
Depurar plantillas y valores.
Exportar los manifiestos para aplicarlos con kubectl apply -f.

Ejemplo de uso práctico:

```bash
helm template my-web-app my-web-app/ > salida.yaml
kubectl apply -f salida.yaml
```
Esto genera los manifiestos y luego los aplica manualmente, sin usar Helm para gestionar el release.


```sh
# Install the chart
kubectl create namespace custom-charts
helm install my-web-app my-web-app/ --namespace custom-charts

NAME: my-web-app
LAST DEPLOYED: Sun Nov 16 13:22:32 2025
NAMESPACE: custom-charts
STATUS: deployed
REVISION: 1
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace custom-charts -l "app.kubernetes.io/name=my-web-app,app.kubernetes.io/instance=my-web-app" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace custom-charts $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace custom-charts port-forward $POD_NAME 8080:$CONTAINER_PORT
```



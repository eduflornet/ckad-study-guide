🧱 1. Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: canary-demo
```
Crea un namespace llamado canary-demo para aislar los recursos relacionados con el despliegue canario.

🚀 2. Despliegue estable (app-stable)
```yaml
kind: Deployment
metadata:
  name: app-stable
  namespace: canary-demo
```
Despliega la versión estable de la aplicación.

Usa la imagen nginx:1.20.
Tiene 9 réplicas, lo que representa el 90% del tráfico.
Etiquetas: app: canary-app, version: stable.
Configura recursos mínimos y máximos (requests y limits).
Define una readiness probe para verificar que el contenedor esté listo antes de recibir tráfico.

🧪 3. Despliegue canario (app-canary)
```yaml
kind: Deployment
metadata:
  name: app-canary
  namespace: canary-demo
```
Despliega la versión canaria (experimental) de la aplicación.
Usa la imagen nginx:1.21.
Tiene 1 réplica, lo que representa el 10% del tráfico.
Etiquetas: app: canary-app, version: canary.
Misma configuración de recursos y readiness probe que la versión estable.

🌐 4. Servicio compartido (canary-service)
```yaml
kind: Service
metadata:
  name: canary-service
  namespace: canary-demo
spec:
  selector:
    app: canary-app
```
Crea un servicio que expone ambas versiones (estable y canaria).
El selector app: canary-app incluye ambos despliegues.
El tráfico se distribuye según el número de réplicas: 90% a estable, 10% a canaria.

📦 Aplicación del manifiesto
```bash
kubectl apply -f canary-setup.yaml
```
Aplica el archivo YAML a tu clúster de Kubernetes.
Crea el namespace, los dos despliegues y el servicio.




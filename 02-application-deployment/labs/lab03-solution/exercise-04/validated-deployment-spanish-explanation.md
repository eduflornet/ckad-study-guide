🔄 Estrategia de actualización
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```
Usa RollingUpdate: actualiza los pods uno por uno.
maxSurge: 1: puede crear un pod extra durante la actualización.
maxUnavailable: 0: asegura que no haya downtime (siempre habrá al menos 3 pods disponibles).

🎯 Selector y plantilla
```yaml
selector:
  matchLabels:
    app: validated-app
```
Selecciona pods con la etiqueta app: validated-app.

```yaml
template:
  metadata:
    labels:
      app: validated-app
```
La plantilla de pod tendrá esa etiqueta, lo que conecta el Deployment con el Service.

🐳 Contenedor
```yaml
containers:
- name: web
  image: nginx:1.20
  ports:
  - containerPort: 80
```
Contenedor llamado web.
Imagen: nginx:1.20.
Expone el puerto 80.

📊 Recursos
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "100m"
```
Requests: recursos mínimos garantizados (64Mi de RAM y 50 milicores de CPU).
Limits: máximo permitido (128Mi de RAM y 100 milicores de CPU).

✅ Probes
Readiness Probe: determina si el pod está listo para recibir tráfico.

```yaml
readinessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 3
  timeoutSeconds: 2
  successThreshold: 2
  failureThreshold: 3
```
Espera 5s antes de empezar.
Chequea cada 3s.
Necesita 2 respuestas correctas seguidas para marcarlo como listo.
Liveness Probe: verifica si el pod sigue vivo.

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 15
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

Empieza a los 15s.
Chequea cada 10s.
Si falla 3 veces seguidas, Kubernetes reinicia el contenedor.

🌐 Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: validated-service
  namespace: validated-demo
spec:
  selector:
    app: validated-app
  ports:
  - port: 80
    targetPort: 80
```
Crea un Service llamado validated-service.
Selecciona pods con la etiqueta app: validated-app.
Expone el puerto 80 y lo redirige al puerto 80 del contenedor.

🛠️ Paso 1: Crear el ConfigMap para HAProxy
Este archivo define cómo HAProxy redirige el tráfico desde localhost:5432 hacia external-db.example.com:5432.
```yaml
# db-ambassador-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: db-ambassador-config
data:
  haproxy.cfg: |
    global
      daemon
      maxconn 256

    defaults
      mode tcp
      timeout connect 10s
      timeout client 1m
      timeout server 1m

    frontend postgres_frontend
      bind *:5432
      default_backend postgres_backend

    backend postgres_backend
      server external-db external-db.example.com:5432
```
📦 Paso 2: Crear el manifiesto del Pod
Este Pod contiene dos contenedores: el ambassador (db-ambassador) y la aplicación (app). Ambos comparten el mismo namespace de red.

```yaml
# /tmp/ambassador-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-pod
spec:
  containers:
  - name: db-ambassador
    image: haproxy:2.8-alpine
    ports:
    - containerPort: 5432
    volumeMounts:
    - name: haproxy-config
      mountPath: /usr/local/etc/haproxy/haproxy.cfg
      subPath: haproxy.cfg
  - name: app
    image: busybox:1.35
    command: ["sh", "-c", "while true; do echo 'Connecting to database via ambassador on localhost:5432'; nc -z localhost 5432 && echo 'Connection successful' || echo 'Connection failed'; sleep 30; done"]
  volumes:
  - name: haproxy-config
    configMap:
      name: db-ambassador-config
  # Compartir el namespace de red
  shareProcessNamespace: true
```

🚀 Paso 3: Aplicar los recursos
Ejecuta estos comandos en tu terminal:

```bash
kubectl apply -f /tmp/db-ambassador-configmap.yaml
kubectl apply -f /tmp/ambassador-pod.yaml
```

🔍 Paso 4: Verificar que el ambassador escucha en el puerto 5432
Conéctate al contenedor db-ambassador:

```bash
kubectl exec -it ambassador-pod -c db-ambassador -- sh
```
Dentro del contenedor, ejecuta:

```sh
netstat -tnlp | grep 5432
```

Deberías ver que HAProxy está escuchando en 0.0.0.0:5432.

📋 Paso 5: Verificar los logs del contenedor de aplicación
Para ver los intentos de conexión:

```bash
kubectl logs ambassador-pod -c app -f
```
Verás líneas como:

```sh
Connecting to database via ambassador on localhost:5432
Connection successful

Connection failed
```








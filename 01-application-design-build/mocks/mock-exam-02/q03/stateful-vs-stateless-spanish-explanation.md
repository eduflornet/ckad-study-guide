📂 Parte A: Deployment (Stateless Web App)
Archivo: /tmp/stateful-vs-stateless/web-frontend-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: web-frontend
  template:
    metadata:
      labels:
        app: web-frontend
    spec:
      containers:
      - name: nginx
        image: nginx:1.24-alpine
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"

```

📂 Parte B: StatefulSet (Stateful Database)
Archivo: /tmp/stateful-vs-stateless/database-statefulset.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: database-svc
spec:
  ports:
  - port: 5432
    name: postgres
  clusterIP: None
  selector:
    app: database-cluster
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database-cluster
spec:
  serviceName: database-svc
  replicas: 3
  selector:
    matchLabels:
      app: database-cluster
  template:
    metadata:
      labels:
        app: database-cluster
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: testdb
        - name: POSTGRES_USER
          value: testuser
        - name: POSTGRES_PASSWORD
          value: testpass
        ports:
        - containerPort: 5432
          name: postgres
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi

```

🛠️ Pasos para aplicar y escalar
bash
# Crear directorio
mkdir -p /tmp/stateful-vs-stateless/

# Guardar ambos manifiestos en los archivos indicados
# Aplicar recursos
kubectl apply -f /tmp/stateful-vs-stateless/web-frontend-deployment.yaml
kubectl apply -f /tmp/stateful-vs-stateless/database-statefulset.yaml

# Escalar Deployment a 5 réplicas
kubectl scale deployment web-frontend --replicas=5

# Escalar StatefulSet a 5 réplicas
kubectl scale statefulset database-cluster --replicas=5

🔍 Observaciones esperadas
Archivo: /tmp/observations.txt

Contenido sugerido:

Código
Observaciones sobre Deployment vs StatefulSet:

1. Deployment (web-frontend):
   - Los pods se nombran de forma aleatoria, por ejemplo: web-frontend-5d7f9c8f7b-abcde.
   - No existe un orden estricto de arranque; los pods pueden iniciar en paralelo.
   - Al escalar de 3 a 5 réplicas, se crean dos pods adicionales con nombres aleatorios.
   - Los pods no mantienen identidad persistente: si se elimina uno, el nuevo tendrá un nombre distinto.

2. StatefulSet (database-cluster):
   - Los pods se nombran de forma ordenada y estable: database-cluster-0, database-cluster-1, database-cluster-2, etc.
   - Existe un orden de arranque: primero se crea el pod 0, luego el 1, y así sucesivamente.
   - Al escalar de 3 a 5 réplicas, se crean database-cluster-3 y database-cluster-4.
   - Cada pod mantiene su identidad y volumen persistente asociado (PVC), lo que garantiza almacenamiento estable.

🅰️ Parte A: Deployment (Stateless Web App)
```bash
# Crear el Deployment de nginx con 3 réplicas
kubectl create deployment web-frontend \
  --image=nginx:1.24-alpine \
  --replicas=3

# Añadir requests de recursos
kubectl set resources deployment web-frontend \
  --requests=cpu=50m,memory=64Mi

# Configurar estrategia de rolling update (máx 1 unavailable, máx 1 surge)
kubectl patch deployment web-frontend \
  -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxUnavailable":1,"maxSurge":1}}}}'

```


🅱️ Parte B: StatefulSet (Stateful Database)
Nota: Imperativamente no existe un comando directo para StatefulSet como sí para Deployment. Se hace con kubectl create statefulset (desde v1.25+) o con kubectl apply -f. Aquí te muestro la forma imperativa con kubectl create statefulset.

```bash
# Crear el servicio headless para el StatefulSet
kubectl create service clusterip database-svc \
  --tcp=5432:5432 \
  --clusterip=None \
  --dry-run=client -o yaml | kubectl apply -f -

# Crear el StatefulSet con 3 réplicas
kubectl create statefulset database-cluster \
  --image=postgres:15-alpine \
  --replicas=3 \
  --service=database-svc

# Añadir variables de entorno
kubectl set env statefulset database-cluster \
  POSTGRES_DB=testdb \
  POSTGRES_USER=testuser \
  POSTGRES_PASSWORD=testpass

# Añadir requests de recursos
kubectl set resources statefulset database-cluster \
  --requests=cpu=200m,memory=256Mi

# Añadir volumen persistente (PVC de 1Gi por pod)
kubectl patch statefulset database-cluster \
  -p '{"spec":{"volumeClaimTemplates":[{"metadata":{"name":"data"},"spec":{"accessModes":["ReadWriteOnce"],"resources":{"requests":{"storage":"1Gi"}}}}]}}'

```

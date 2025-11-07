#🅰️ Parte A: Deployment (Stateless Web App)
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

#🅱️ Parte B: StatefulSet (Stateful Database)
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


# 🔄 Escalado

# Escalar Deployment a 5 réplicas
kubectl scale deployment web-frontend --replicas=5

# Escalar StatefulSet a 5 réplicas
kubectl scale statefulset database-cluster --replicas=5

# 📊 Observaciones (imperativo)

# Ver pods del Deployment
kubectl get pods -l app=web-frontend

# Ver pods del StatefulSet
kubectl get pods -l app=database-cluster

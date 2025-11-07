📦 1. Database Instance (PostgreSQL)
```bash
kubectl create statefulset postgres-db --image=postgres:15 --port=5432
kubectl create pvc pgdata --access-modes=ReadWriteOnce --resources=storage=5Gi
```
⚠️ Nota: Para evitar reinicios automáticos por corrupción, necesitarías editar el StatefulSet después de crearlo para establecer restartPolicy: Never, lo cual no es posible directamente con kubectl create. Mejor usar YAML para eso.

🌐 2. Web Application (Stateless Web Service)
```bash
kubectl create deployment webapp --image=nginx:latest --replicas=3
kubectl expose deployment webapp --port=80 --target-port=80
```

📄 3. Log Processor (Job con reintentos)
```bash
kubectl create job log-processor --image=busybox --restart=Never -- /bin/sh -c "echo Processing logs... && exit 1"
kubectl patch job log-processor -p '{"spec":{"backoffLimit":3}}'
```

🛠️ 4. Monitoring Agent (DaemonSet)
```bash
kubectl create daemonset node-monitor --image=prom/node-exporter --port=9100
```
⚠️ kubectl create daemonset no permite especificar todos los detalles como recursos o labels. Para producción, mejor usar YAML.

🧠 5. Session Store (Redis Cache con orden de inicio/apagado)
```bash
kubectl create statefulset redis-cache --image=redis:7 --port=6379
kubectl create pvc redis-data --access-modes=ReadWriteOnce --resources=storage=1Gi
```

**Script Bash** completo que crea todos los recursos de forma imperativa en Kubernetes. Incluye configuraciones básicas como límites de recursos, reintentos, y notas para extensiones como probes o affinities.

🖥️ deploy_workloads.sh
```bash
#!/bin/bash

# 1. PostgreSQL Database (StatefulSet + PVC)
kubectl create pvc pgdata --access-modes=ReadWriteOnce --resources=storage=5Gi
kubectl create statefulset postgres-db --image=postgres:15 --port=5432
kubectl patch statefulset postgres-db -p '{"spec":{"template":{"spec":{"restartPolicy":"Never"}}}}'

# 2. Web Application (Deployment + Service)
kubectl create deployment webapp --image=nginx:latest --replicas=3
kubectl expose deployment webapp --port=80 --target-port=80
kubectl set resources deployment webapp --limits=cpu=250m,memory=256Mi

# 3. Log Processor (Job with retries)
kubectl create job log-processor --image=busybox --restart=Never -- /bin/sh -c "echo Processing logs... && exit 1"
kubectl patch job log-processor -p '{"spec":{"backoffLimit":3}}'
kubectl set resources job log-processor --limits=cpu=100m,memory=128Mi

# 4. Monitoring Agent (DaemonSet)
kubectl create daemonset node-monitor --image=prom/node-exporter --port=9100
kubectl set resources daemonset node-monitor --limits=cpu=100m,memory=100Mi

# 5. Redis Cache (StatefulSet + PVC)
kubectl create pvc redis-data --access-modes=ReadWriteOnce --resources=storage=1Gi
kubectl create statefulset redis-cache --image=redis:7 --port=6379
kubectl set resources statefulset redis-cache --limits=cpu=250m,memory=256Mi

echo "✅ Todos los recursos han sido creados de forma imperativa."
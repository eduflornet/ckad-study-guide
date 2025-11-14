
## blue-green-namespace.yaml

```sh
 k get svc -n blue-green-demo
NAME              TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
web-app-public    LoadBalancer   10.101.97.123   <pending>     80:31487/TCP   98s
web-app-service   ClusterIP      10.105.69.154   <none>        80/TCP         98s

```


🔍 Explicación Técnica
web-app-public (LoadBalancer)
Tipo LoadBalancer: expone el servicio al exterior mediante una IP pública (usualmente asignada por el proveedor cloud).

EXTERNAL-IP pendiente: aún no se ha asignado la IP pública. Esto puede tardar unos segundos/minutos dependiendo del entorno.

80:31487/TCP: el puerto 80 del contenedor está expuesto externamente en el puerto 31487 del nodo (NodePort), y el balanceador lo usará para enrutar tráfico.

web-app-service (ClusterIP)
Tipo ClusterIP: accesible solo dentro del clúster. Ideal para comunicación interna entre pods.

Sin EXTERNAL-IP: no se expone al exterior.

80/TCP: escucha en el puerto 80 dentro del clúster.


## green-deployment.yaml

🟢 Descripción general
Este manifiesto de Kubernetes define dos recursos en el namespace blue-green-demo:

Deployment llamado app-green

Service llamado web-app-green-service

Está diseñado para una estrategia de despliegue blue-green, donde se despliega una nueva versión (green) sin afectar la versión actual (blue), permitiendo pruebas antes del cambio de tráfico.

📦 Deployment: app-green
🔹 Metadatos
-Nombre: app-green
-Namespace: blue-green-demo
-Etiquetas: app=web-app, version=green, environment=staging

🔹 Especificación
-Réplicas: 3 pods
-Selector: busca pods con app=web-app y version=green
-Template de pod:
    -Imagen: nginx:1.21
-Variables de entorno:
    -VERSION=green-v1.21
    -ENVIRONMENT=staging

Recursos:
-Requests: 64Mi de memoria, 50m de CPU
-Limits: 128Mi de memoria, 100m de CPU

Probes:
-Readiness: HTTP GET / en el puerto 80, inicia tras 5s, cada 3s
-Liveness: HTTP GET / en el puerto 80, inicia tras 15s, cada 10s

Lifecycle hook:
preStop: ejecuta sleep 15 antes de detener el contenedor (para permitir que el tráfico se drene)




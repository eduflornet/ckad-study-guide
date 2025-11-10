🛠️ Tipo de recurso
Deployment: Define un despliegue de una aplicación gestionada por Kubernetes.

📛 Metadatos
Nombre: rolling-app

Etiqueta principal: app: rolling-test

📦 Especificaciones del despliegue
-Réplicas: 5 instancias del contenedor.
-Estrategia de actualización: RollingUpdate
-maxSurge: 1: Se permite 1 pod adicional durante la actualización.
-maxUnavailable: 1: Se permite que 1 pod esté fuera de servicio durante la actualización.

🔍 Selector
Coincide con etiquetas app: rolling-test para identificar los pods gestionados.

🧬 Plantilla de pod
Etiquetas: app: rolling-test, version: v1.20

Contenedor:
-Nombre: nginx
-Imagen: nginx:1.20
-Puerto expuesto: 80

📊 Recursos
Solicitudes:
    -Memoria: 64Mi
    -CPU: 50m

Límites:
    -Memoria: 128Mi
    -CPU: 100m

✅ Probes
Readiness Probe:
-Verifica disponibilidad en / puerto 80
-Comienza tras 5 segundos, cada 5 segundos

Liveness Probe:
-Verifica que el contenedor esté vivo en / puerto 80
-Comienza tras 15 segundos, cada 10 segundos

Este despliegue está diseñado para garantizar alta disponibilidad y actualizaciones seguras mediante la estrategia de rolling update

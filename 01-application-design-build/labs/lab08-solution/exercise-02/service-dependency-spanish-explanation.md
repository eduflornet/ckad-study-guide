Este manifiesto de Kubernetes define una arquitectura en la que una aplicación espera a que sus dependencias estén disponibles antes de iniciar. Utiliza init containers para garantizar que los servicios externos (como una base de datos y una API) estén listos, y que la configuración esté descargada antes de que el contenedor principal comience a ejecutarse.

🧩 Componentes principales
1. 🛎️ Service: database-service

```yaml
kind: Service
metadata:
  name: database-service
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
```

Expone el deployment de PostgreSQL en el puerto 5432.

Permite que otros pods accedan a la base de datos usando el nombre DNS database-service.

2. 🗄️ Deployment: database

```yaml
kind: Deployment
metadata:
  name: database
spec:
  replicas: 1
  ...
```

Despliega una instancia de PostgreSQL 15 con credenciales y base de datos predefinidas.

Usa una readiness probe con pg_isready para indicar cuándo está lista para recibir conexiones.

3. 🚦 Pod: service-dependent-app
Este pod tiene tres init containers y un contenedor principal:

🔧 Init Containers
wait-for-database

Usa nc (netcat) para verificar si el servicio database-service está escuchando en el puerto 5432.

Espera en bucle hasta que la base de datos esté disponible.

wait-for-api

Usa curl para verificar si una API externa (https://httpbin.org/status/200) responde correctamente.

Espera en bucle hasta que el endpoint devuelva HTTP 200.

🧠 Contenedor principal: app
Imagen: python:3.11-alpine

Lee los archivos de configuración generados por los init containers.

Imprime la configuración y simula actividad con un contador que se incrementa cada 10 segundos.

📁 Volumen compartido
```yaml
volumes:
- name: config-volume
  emptyDir: {}
emptyDir: volumen temporal compartido entre los init containers y el contenedor principal.
```

Permite que la configuración descargada esté disponible para la aplicación.

🧠 ¿Qué logra esta arquitectura?
Sincronización de dependencias: garantiza que la base de datos y la API estén listas antes de iniciar la app.

Configuración dinámica: descarga y genera archivos de configuración en tiempo de arranque.

Robustez: evita errores por dependencias no disponibles.



Este manifiesto de Kubernetes define una aplicación que realiza migraciones de base de datos, inserta datos iniciales y valida la configuración antes de arrancar. Utiliza init containers para preparar el entorno antes de que el contenedor principal se ejecute.

🧩 1. ConfigMap: migration-scripts
Contiene dos archivos embebidos:

migrate.sql: script SQL que:

Crea las tablas users y posts si no existen.

Inserta datos de ejemplo (alice, bob, y sus posts).

Usa ON CONFLICT DO NOTHING para evitar duplicados.

seed-data.json: archivo JSON con:

Usuarios adicionales (charlie, diana)

Configuración de la app (theme, notifications, max_posts_per_page)

Este ConfigMap se monta como volumen en los init containers y el contenedor principal.

🧪 2. Pod: app-with-migration
Este pod tiene tres init containers y un contenedor principal:

🔧 Init Containers
🛠️ db-migration
Imagen: postgres:15-alpine

Espera a que la base de datos esté lista usando pg_isready.

Ejecuta el script migrate.sql usando psql.

Monta el ConfigMap en /migrations.

🔁 Este paso garantiza que la estructura de la base de datos esté creada antes de continuar.

🌱 data-seeder
Imagen: python:3.11-alpine

Lee seed-data.json y conecta a PostgreSQL usando psycopg2.

Inserta usuarios adicionales (charlie, diana) si no existen.

Monta el ConfigMap en /seed-data.

🔁 Este paso agrega datos iniciales personalizados a la base de datos.

✅ config-validator
Imagen: python:3.11-alpine

Valida que seed-data.json tenga las claves esperadas (users, settings).

Verifica conectividad con la base de datos.

Cuenta registros en users y posts, y lanza advertencias si hay pocos datos.

🔁 Este paso asegura que la configuración y los datos estén completos antes de iniciar la app.

🧠 Contenedor principal: web-app
Imagen: python:3.11-alpine

Inicia un servidor HTTP en el puerto 8080.

Expone:

/users: devuelve los usuarios en formato JSON.

/: muestra una página HTML básica con enlace a /users.

Se conecta a PostgreSQL para consultar datos.

🔁 Este es el servicio final que depende de que los pasos anteriores se hayan completado correctamente.

📁 Volumen compartido
```yaml
volumes:
- name: migration-scripts
  configMap:
    name: migration-scripts
```

Monta el ConfigMap como volumen para que los scripts estén disponibles en los contenedores.

Como una mejora se podria convertir todo esto en un Helm chart para que puedas instalar, versionar y reutilizar fácilmente esta arquitectura con migraciones, seeding y validación.

Un **Helm chart** es un paquete que contiene:

Plantillas de recursos de Kubernetes (Deployment, Service, ConfigMap, etc.)

Valores configurables (values.yaml)

Archivos de metadatos (Chart.yaml)

🧰 Estructura del chart

```sh
app-with-init/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── configmap.yaml
│   ├── service.yaml
│   ├── deployment.yaml
│   ├── pod.yaml
```

🧾 1. Chart.yaml

```yaml
apiVersion: v2
name: app-with-init
description: Web app with init containers for DB migration and seeding
version: 0.1.0
```

⚙️ 2. values.yaml
```yaml
database:
  host: database-service
  port: 5432
  name: testdb
  user: testuser
  password: testpass

app:
  image: python:3.11-alpine
  port: 8080

migration:
  image: postgres:15-alpine

seeder:
  image: python:3.11-alpine

config:
  users:
    - username: charlie
      email: charlie@example.com
    - username: diana
      email: diana@example.com
  settings:
    theme: dark
    notifications: true
    max_posts_per_page: 10

```

📄 3. templates/configmap.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: migration-scripts
data:
  migrate.sql: |
    {{ .Files.Get "scripts/migrate.sql" | indent 4 }}
  seed-data.json: |
    {{ .Values.config | toJson | indent 4 }}

```

Puedes colocar migrate.sql en una carpeta scripts/ dentro del chart.

🚀 4. templates/pod.yaml
Aquí defines el Pod con los init containers (db-migration, data-seeder, config-validator) y el contenedor principal (web-app). Usa {{ .Values.* }} para parametrizar imágenes, credenciales, puertos, etc.


🧪 5. templates/service.yaml y deployment.yaml
Incluye el servicio para la base de datos y el Deployment si decides separar la base de datos como un componente independiente.

🧠 ¿Qué ventajas obtienes?
Reusabilidad: puedes instalar con helm install y cambiar valores fácilmente.

Versionado: puedes mantener múltiples versiones del chart.

Configurabilidad: puedes usar --set o values.yaml para personalizar sin tocar las plantillas.





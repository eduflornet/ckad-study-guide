Guardar el manifiesto en el archivo ``` init-containers-pod.yaml ```.

Aplicar el manifiesto:

```bash
kubectl apply -f /tmp/init-containers-pod.yaml
```
Verificar el orden de ejecución:

```bash
kubectl describe pod database-pod
```
Busca la sección Init Containers para confirmar que se ejecutaron en orden y terminaron correctamente.

Verificar los archivos generados: Una vez que el contenedor principal esté en estado Running, puedes acceder a él:

```bash
kubectl exec -it database-pod -- sh
```
Luego verifica:

```bash
ls /docker-entrypoint-initdb.d/
cat /docker-entrypoint-initdb.d/schema.sql

ls /etc/postgresql/
cat /etc/postgresql/postgresql.conf
```

## Imperative commands

¡Claro! Para crear este Pod con init containers de forma imperativa usando kubectl, necesitas ejecutar una serie de comandos que configuren cada parte del Pod. Aunque kubectl run no permite directamente definir múltiples init containers, puedes lograrlo usando kubectl create con objetos YAML generados desde línea de comandos o editando el recurso después de crearlo.

Aquí tienes una forma práctica de hacerlo:

🛠 Paso 1: Crear el Pod base sin init containers
```bash
kubectl run database-pod \
  --image=postgres:15-alpine \
  --env="POSTGRES_DB=testdb" \
  --env="POSTGRES_USER=admin" \
  --env="POSTGRES_PASSWORD=secret" \
  --restart=Never \
  --dry-run=client -o yaml > /tmp/init-containers-pod.yaml
```

🛠 Paso 2: Editar el YAML para agregar init containers y volúmenes
Abre el archivo generado:

```bash
nano /tmp/init-containers-pod.yaml
```
Agrega las siguientes secciones dentro de spec:

Volumes
```yaml
  volumes:
    - name: data-volume
      emptyDir: {}
    - name: config-volume
      emptyDir: {}
```

Init Containers
```yaml
  initContainers:
    - name: init-schema
      image: busybox:1.35
      command: ["sh", "-c", "echo 'CREATE TABLE users (id INT, name VARCHAR(50));' > /shared-data/schema.sql; echo 'Schema file created'"]
      volumeMounts:
        - name: data-volume
          mountPath: /shared-data
    - name: init-config
      image: busybox:1.35
      command: ["sh", "-c", "echo 'port=5432\nmax_connections=100\nshared_buffers=256MB' > /shared-config/postgresql.conf; echo 'Config file created'"]
      volumeMounts:
        - name: config-volume
          mountPath: /shared-config
    - name: network-check
      image: busybox:1.35
      command: ["sh", "-c", "nslookup kubernetes.default.svc.cluster.local; echo 'Network connectivity verified'"]

```

Volume Mounts en el contenedor principal
Dentro de containers[0], agrega:

```yaml
      volumeMounts:
        - name: data-volume
          mountPath: /docker-entrypoint-initdb.d
        - name: config-volume
          mountPath: /etc/postgresql
```

🛠 Paso 3: Aplicar el Pod
```yaml
kubectl apply -f /tmp/init-containers-pod.yaml
```

✅ Verificación
Verifica el estado de los init containers:

```yaml
kubectl get pod database-pod
kubectl describe pod database-pod
```

Accede al contenedor principal para verificar los archivos:

```yaml
kubectl exec -it database-pod -- sh

ls /docker-entrypoint-initdb.d/

cat /docker-entrypoint-initdb.d/schema.sql

ls /etc/postgresql/

cat /etc/postgresql/postgresql.conf
```


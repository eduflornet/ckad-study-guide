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
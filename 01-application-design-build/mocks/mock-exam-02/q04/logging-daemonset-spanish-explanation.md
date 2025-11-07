🔹 Paso 1: Etiquetar los nodos
Primero, etiqueta los nodos donde quieres que corra el agente de logging:

```bash
kubectl label nodes <nombre-del-nodo> logging=enabled
```
Haz esto en todos los nodos, incluyendo el master/control plane.

🔹 Paso 2: Manifiesto del DaemonSet
Aquí tienes el YAML completo que puedes guardar en /tmp/logging-daemonset.yaml:

```bash
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      nodeSelector:
        logging: enabled
      tolerations:
        - operator: "Exists"   # Permite correr en nodos con taints (incluyendo master/control plane)
      containers:
        - name: fluent-bit
          image: fluent/fluent-bit:2.1
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
          securityContext:
            privileged: true
          volumeMounts:
            - name: varlog
              mountPath: /host/var/log
              readOnly: true
            - name: dockercontainers
              mountPath: /host/var/lib/docker/containers
              readOnly: true
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: dockercontainers
          hostPath:
            path: /var/lib/docker/containers
```

🔍 Selector
```yaml
spec:
  selector:
    matchLabels:
      app: log-collector
```
Define cómo Kubernetes identifica los pods que pertenecen a este DaemonSet.

Aquí usamos la etiqueta app: log-collector.

📦 Template de Pod
```yaml
template:
  metadata:
    labels:
      app: log-collector
```
Cada pod creado tendrá la etiqueta app: log-collector.
Esto debe coincidir con el selector.

🖥️ NodeSelector y Tolerations
```yaml
spec:
  nodeSelector:
    logging: enabled
  tolerations:
    - operator: "Exists"
nodeSelector: asegura que los pods solo se ejecuten en nodos con la etiqueta logging=enabled.
```

tolerations: permite que los pods se ejecuten incluso en nodos con taints (como los master/control plane). El operator: Exists significa que tolera cualquier taint.


🐳 Contenedor
```yaml
containers:
  - name: fluent-bit
    image: fluent/fluent-bit:2.1
name: nombre del contenedor (fluent-bit).
```

image: la imagen del agente de logging (fluent/fluent-bit:2.1).

⚖️ Recursos
```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```
requests: recursos mínimos garantizados (50 milicores de CPU y 64 MiB de memoria).

limits: máximo permitido (100 milicores de CPU y 128 MiB de memoria). Esto evita que el contenedor consuma demasiado.

🔒 Seguridad
```yaml
securityContext:
  privileged: true
```
Ejecuta el contenedor en modo privilegiado, necesario para acceder a directorios del host como /var/log.

📂 Volúmenes y Montajes
```yaml
volumeMounts:
  - name: varlog
    mountPath: /host/var/log
    readOnly: true
  - name: dockercontainers
    mountPath: /host/var/lib/docker/containers
    readOnly: true
volumes:
  - name: varlog
    hostPath:
      path: /var/log
  - name: dockercontainers
    hostPath:
      path: /var/lib/docker/containers
```

volumes: definen qué directorios del host se exponen al pod.
volumeMounts: indican dónde se montan dentro del contenedor.

Ambos son read-only para evitar que el contenedor modifique los logs del host.

✅ Resumen
Este DaemonSet:

-Se despliega en todos los nodos con logging=enabled.

-Tolera taints para correr también en el master.

-Usa Fluent Bit como agente de logging.

-Monta los directorios de logs del host en modo lectura.

-Limita recursos para no sobrecargar el cluster.

-Corre en modo privilegiado para poder acceder a los archivos del host.


🔹 Paso 3: Aplicar el DaemonSet
```bash
kubectl apply -f /tmp/logging-daemonset.yaml
```
🔹 Paso 4: Verificar que los pods corren en los nodos esperados
```bash
kubectl get pods -n kube-system -o wide | grep log-collector
```
Deberías ver un pod por cada nodo etiquetado con logging=enabled.

🔹 Paso 5: Comprobar acceso a logs del host
Dentro de un pod del DaemonSet:

```bash
kubectl exec -n kube-system -it <nombre-del-pod> -- ls /host/var/log
```
Si ves los archivos de logs del host, la configuración está correcta ✅.

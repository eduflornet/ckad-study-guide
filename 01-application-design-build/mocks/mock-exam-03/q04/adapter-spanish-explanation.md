📄 1. Crear el manifiesto del Pod: adapter-pod.yaml

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: adapter-pod
spec:
  volumes:
    - name: nginx-logs
      emptyDir: {}
    - name: apache-logs
      emptyDir: {}
  containers:
    - name: app-nginx
      image: nginx:1.24-alpine
      volumeMounts:
        - name: nginx-logs
          mountPath: /var/log/nginx
    - name: app-apache
      image: httpd:2.4-alpine
      volumeMounts:
        - name: apache-logs
          mountPath: /usr/local/apache2/logs
    - name: log-adapter
      image: busybox:1.35
      command: ["/bin/sh", "-c"]
      args:
        - |
          while true; do
            if [ -f /nginx-logs/access.log ]; then
              tail -n 0 -f /nginx-logs/access.log | while read line; do
                echo "{\"source\":\"nginx\",\"timestamp\":\"$(date -Iseconds)\",\"message\":\"$line\"}"
              done &
            fi
            if [ -f /apache-logs/access_log ]; then
              tail -n 0 -f /apache-logs/access_log | while read line; do
                echo "{\"source\":\"apache\",\"timestamp\":\"$(date -Iseconds)\",\"message\":\"$line\"}"
              done &
            fi
            sleep 60
          done
      volumeMounts:
        - name: nginx-logs
          mountPath: /nginx-logs
        - name: apache-logs
          mountPath: /apache-logs
```

🚀 2. Aplicar el Pod y esperar que esté listo
```bash
kubectl apply -f /tmp/adapter-pod.yaml
kubectl wait --for=condition=Ready pod/adapter-pod --timeout=60s
```
🌐 3. Generar tráfico a los servidores web
```bash
kubectl exec -it adapter-pod -c app-nginx -- curl localhost
kubectl exec -it adapter-pod -c app-apache -- curl localhost
```

📋 4. Verificar logs del adaptador
```bash
kubectl logs adapter-pod -c log-adapter
```
Copia una muestra de la salida JSON:

```bash
kubectl logs adapter-pod -c log-adapter | head -n 10 > /tmp/adapter-output.json
```

📑 5. Crear comparación de logs
```bash
echo "Original nginx log:" > /tmp/log-comparison.txt
kubectl exec adapter-pod -c app-nginx -- tail -n 1 /var/log/nginx/access.log >> /tmp/log-comparison.txt

echo "\nAdapted nginx log:" >> /tmp/log-comparison.txt
kubectl logs adapter-pod -c log-adapter | grep '"source":"nginx"' | head -n 1 >> /tmp/log-comparison.txt

echo "\nOriginal apache log:" >> /tmp/log-comparison.txt
kubectl exec adapter-pod -c app-apache -- tail -n 1 /usr/local/apache2/logs/access_log >> /tmp/log-comparison.txt

echo "\nAdapted apache log:" >> /tmp/log-comparison.txt
kubectl logs adapter-pod -c log-adapter | grep '"source":"apache"' | head -n 1 >> /tmp/log-comparison.txt
```



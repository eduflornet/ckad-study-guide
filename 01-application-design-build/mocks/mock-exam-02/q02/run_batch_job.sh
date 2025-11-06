#!/bin/bash

set -e

echo "📁 Creando namespace..."
kubectl create namespace batch-processing --dry-run=client -o yaml | kubectl apply -f -

echo "📝 Generando manifiesto YAML en /tmp/batch-job.yaml..."
cat <<EOF > /tmp/batch-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-processor
  namespace: batch-processing
spec:
  completions: 5
  parallelism: 3
  backoffLimit: 2
  activeDeadlineSeconds: 600
  ttlSecondsAfterFinished: 300
  template:
    metadata:
      labels:
        job: data-processor
    spec:
      containers:
      - name: processor
        image: busybox:1.35
        command: ["sh", "-c", "for i in \$(seq 1 100); do echo Processing item \$i; sleep 0.1; done; echo Batch complete"]
        resources:
          limits:
            cpu: "100m"
            memory: "128Mi"
      restartPolicy: Never
EOF

echo "🚀 Aplicando el Job..."
kubectl apply -f /tmp/batch-job.yaml

echo "⏳ Esperando a que el Job finalice..."
kubectl wait --for=condition=complete job/data-processor -n batch-processing --timeout=10m || {
  echo "❌ El Job no se completó exitosamente dentro del tiempo límite."
  exit 1
}

echo "✅ Verificando completions..."
COMPLETIONS=$(kubectl get job data-processor -n batch-processing -o jsonpath='{.status.succeeded}')
if [ "$COMPLETIONS" -eq 5 ]; then
  echo "🎉 Job completado exitosamente con $COMPLETIONS ejecuciones."
else
  echo "⚠️ Job finalizado pero con $COMPLETIONS completions. Revisa los logs."
  kubectl logs -n batch-processing -l job=data-processor --tail=20
  exit 1
fi

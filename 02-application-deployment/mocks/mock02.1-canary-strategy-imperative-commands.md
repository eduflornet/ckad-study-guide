# Canary release strategy with imperative kubectl commands

Este escenario pide precisión técnica y buen pulso. Te propongo un flujo 100% imperativo con kubectl, usando dos Deployments (stable y canary), un Service único, validación automatizada con Jobs, monitoreo con HPA/metrics, y un script de “progressive shift” que revierte si algo va mal. Es realista para CKAD, sin depender de service meshes.

### Assumptions and quick setup
Namespace: finance

Service name: payment-api

Stable image: registry.example.com/payment-api:v1

Canary image: registry.example.com/payment-api:v2

Fraud service image: registry.example.com/fraud-svc:v2

Monitoring via metrics-server: kubectl top is available

Ingress optional: NGINX Ingress canary available if needed (included below as optional)

```bash
# Create namespace and labels
kubectl create namespace finance
kubectl label namespace/finance compliance=audit

# Baseline service (stable)
kubectl -n finance create deployment payment-api-stable \
  --image=registry.example.com/payment-api:v1 \
  --replicas=8 \
  --port=8080

kubectl -n finance set probe deployment/payment-api-stable \
  --readiness-http-get=/healthz --readiness-timeout=2 --readiness-period=5 \
  --liveness-http-get=/livez --liveness-timeout=2 --liveness-period=10

kubectl -n finance expose deployment payment-api-stable \
  --name=payment-api --port=80 --target-port=8080
  
  ```

### Fraud detection service (stable → will be canaried too)

```bash
kubectl -n finance create deployment fraud-svc-stable \
  --image=registry.example.com/fraud-svc:v1 \
  --replicas=4 --port=9000

kubectl -n finance set probe deployment/fraud-svc-stable \
  --readiness-http-get=/healthz --readiness-timeout=2 --readiness-period=5 \
  --liveness-http-get=/livez --liveness-timeout=2 --liveness-period=10

kubectl -n finance expose deployment fraud-svc-stable \
  --name=fraud-svc --port=9000 --target-port=9000
```

### Canary deployments and traffic split

Usaremos el mismo Service “payment-api” apuntando por labels a ambas versiones. El split se controla con replicas.

Deploy canary with isolation and audit annotations

```bash
kubectl -n finance create deployment payment-api-canary \
  --image=registry.example.com/payment-api:v2 \
  --replicas=1 --port=8080

kubectl -n finance annotate deployment/payment-api-canary \
  release.strategy=canary \
  release.ticket=FIN-2317 \
  release.owner=platform-team \
  compliance.audit="fraud-alg v2 rollout with progressive shift"

kubectl -n finance label deployment/payment-api-stable app=payment-api tier=api track=stable
kubectl -n finance label deployment/payment-api-canary app=payment-api tier=api track=canary
```
Ajustar selector del Service para incluir ambas pistas
```bash
kubectl -n finance patch service payment-api \
  -p '{"spec":{"selector":{"app":"payment-api","tier":"api"}}}'
```

**Split por réplicas**: el Service enviará tráfico a pods listos de ambos Deployments; el porcentaje se aproxima al reparto de réplicas.

Validación automatizada y shifting progresivo
Job de integridad de transacciones
```bash
kubectl -n finance create job tx-integrity-check \
  --image=registry.example.com/test-tools:latest \
  -- bash -lc 'python run_checks.py \
    --api http://payment-api.finance.svc.cluster.local \
    --fraud http://fraud-svc.finance.svc.cluster.local \
    --mode=canary --assert-idempotency --assert-p95<=300 --assert-error-rate<=0.5'
```
Script de shifting con rollback
```bash
cat <<'EOF' > shift-canary.sh
#!/usr/bin/env bash
set -euo pipefail
NS=finance
STABLE=payment-api-stable
CANARY=payment-api-canary

log(){ echo "[$(date +%H:%M:%S)] $*"; }

validate(){
  kubectl -n "$NS" rollout status deploy/$CANARY --timeout=90s || return 1
  kubectl -n "$NS" delete job tx-integrity-check --ignore-not-found
  kubectl -n "$NS" create job tx-integrity-check \
    --image=registry.example.com/test-tools:latest \
    -- bash -lc 'python run_checks.py \
      --api http://payment-api.finance.svc.cluster.local \
      --fraud http://fraud-svc.finance.svc.cluster.local \
      --mode=canary --assert-idempotency --assert-p95<=300 --assert-error-rate<=0.5'
  kubectl -n "$NS" wait --for=condition=complete job/tx-integrity-check --timeout=120s || return 1
  # Comprobación simple: sin reinicios en contenedores
  kubectl -n "$NS" get pods -l app=payment-api -o jsonpath='{range .items[*]}{.status.containerStatuses[0].restartCount}{"\n"}{end}' \
    | awk '{s+=$1} END{if(s>0) exit 1}'
}

rollback(){
  log "ROLLBACK: bajando canary y restaurando estable"
  kubectl -n "$NS" scale deploy/$CANARY --replicas=0
  kubectl -n "$NS" annotate deploy/$STABLE rollback.reason="canary failed" rollback.at="$(date -Iseconds)" --overwrite
}

# Pasos de tráfico progresivo por réplicas (aprox. 10%, 20%, 40%, 60%, 80%)
STEPS=(1 2 4 6 8)
for r in "${STEPS[@]}"; do
  log "SHIFT: escalando canary a $r réplicas"
  kubectl -n "$NS" scale deploy/$CANARY --replicas="$r"
  sleep 10
  if ! validate; then rollback; exit 1; fi
done

log "PROMOTE: actualizando estable a v2 y retirando canary"
kubectl -n "$NS" set image deploy/$STABLE payment-api=registry.example.com/payment-api:v2
kubectl -n "$NS" rollout status deploy/$STABLE --timeout=180s
kubectl -n "$NS" scale deploy/$CANARY --replicas=0
kubectl -n "$NS" annotate deploy/$STABLE release.promoted.at="$(date -Iseconds)" --overwrite
EOF
chmod +x shift-canary.sh

```

Ejecutar shifting

```bash
./shift-canary.sh
```

Monitoreo rápido y autoscaling
Visibilidad inmediata
```bash
kubectl -n finance top pods -l app=payment-api
kubectl -n finance describe deploy payment-api-canary | sed -n '/Conditions/,$p'
kubectl -n finance get events --sort-by=.metadata.creationTimestamp
```
Recursos y HPA

```bash
kubectl -n finance set resources deploy/payment-api-stable \
  --requests=cpu=250m,memory=256Mi --limits=cpu=500m,memory=512Mi
kubectl -n finance set resources deploy/payment-api-canary \
  --requests=cpu=250m,memory=256Mi --limits=cpu=500m,memory=512Mi

kubectl -n finance autoscale deploy/payment-api-stable --cpu=70% --min=6 --max=20
kubectl -n finance autoscale deploy/payment-api-canary --cpu=70% --min=1 --max=8
```

Cumplimiento y trazabilidad
Anotar y etiquetar cambios clave
```bash
kubectl -n finance annotate deploy/payment-api-stable \
  change.reason="promote v2 after canary pass" --overwrite
kubectl -n finance label deploy/payment-api-stable version=v2 --overwrite
```
Guardar historial y snapshot
```bash
kubectl -n finance rollout history deploy/payment-api-stable > rollout_history.txt

kubectl -n finance get events --sort-by=.metadata.creationTimestamp > events_log.txt

kubectl -n finance get deploy,pod,svc -l app=payment-api -o wide > snapshot_post_release.txt
```

Metadata en ConfigMap
```bash
kubectl -n finance create configmap release-audit \
  --from-literal=ticket=FIN-2317 \
  --from-literal=owner=platform-team \
  --from-literal=approved_by=security \
  --from-literal=timestamp="$(date -Iseconds)"
```

Plan de 55 minutos (orientativo)

00–10 min: Namespace, Deploy estable, Service, probes, labels.

10–20 min: Deploy canary, probes, selector del Service, anotaciones.

20–35 min: Job de integridad y script de shifting + pruebas locales.

35–45 min: Ejecutar shifting, verificar rollout status, monitoreo rápido.

45–55 min: Promoción, HPA, auditoría, snapshot y verificación final.
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

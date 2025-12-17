kubectl create deployment holy-api -n pluto \
--image=$(kubectl -n default get pods pod6 -o jsonpath='{.spec.containers[0].image}') \
--dry-run=client -o yaml > holy-api-deployment.yaml

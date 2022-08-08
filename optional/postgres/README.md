## Deploy PostgreSQL Separately
Do this step only if you need to have postgres as a standalone helm chart.

This only needs to be done once locally
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install postgres bitnami/postgres --values helm/values.yml
```

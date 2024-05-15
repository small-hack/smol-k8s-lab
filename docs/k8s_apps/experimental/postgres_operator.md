We are experimenting with the Zalando PostgeSQL Operator to create postgresql clusters and manage backups to S3. Our main interest here is that they support major version backups. Our main concern is the mutual TLS support.

In the PostgeSQL Operator, backups for S3 are done to local s3 endpoints consistently and to a configurable remote endpoint. You can see more in our [Zalando Postgres Operator Argo CD Application](https://github.com/small-hack/argocd-apps/tree/main/postgres/operators/zalando).

## Example yaml config

```yaml
apps:
  postgres_operator:
    description: |
      ⚠️ [magenta][i]demo[/i] status[/magenta]

      postgres-operator is a Kubernetes operator for postgresql by Zalando.

      smol-k8s-lab supports initialization by setting up your ingress hostnames, and then also creating a local s3 endpoint exclusively for backups with and additional configurable endpoint for backups to an external s3
    enabled: true
    init:
      enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # FQDN to use for postgres operator web interface
        hostname: "postgres-ui.boopthesnoot.cute"
        s3_endpoint: "postgres-s3.boopthesnoot.cute"
        s3_bucket: zalando-postgres-operator
        s3_region: eu-west-1
        backup_schedule: 30 18 * * *
        backup_retention_time: 8 weeks
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important! This
      # is an app of apps. Change to "monitoring/kube-prometheus-stack/" to
      # only install kube-prometheus-stack (foregoing loki and push gateway)
      path: postgres/operators/zalando/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: postgres-operator
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: postgres-operator
        source_repos:
        - https://opensource.zalando.com/postgres-operator/charts/postgres-operator
        - https://opensource.zalando.com/postgres-operator/charts/postgres-operator-ui
        - https://seaweedfs.github.io/seaweedfs/helm
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
          - postgres-operator
```

We use the Cloud Native PostgeSQL Operator to create postgresql clusters and manage backups to S3. 

<a href="../../assets/images/cnpg_operator_screenshot.png">
<img src="../../assets/images/cnpg_operator_screenshot.png" alt="Screenshot of Argo CD's web interface showing the CNPG Operator Application in tree view mode. This includes configmap s for monitoring and manager config, webhook-service, cnpg-validating-webhook-config, backups CRD, clusters CRD, poolers CRD, scheduledBackups CRD, operator deployment, and 3 cluster roles. the cnpg-webhook-service is branching to the cnpg-webhook-service endpoint. The cnpg-validating-webhook-config is branching to an endpoint slice of the same name. the deployment has two children: cnpg-webhook-cert and cnpg-operator replicaset. the replicaset feeds into a single pod called cnpg-operator">
</a>

In the CloudNative PostgeSQL Operator Backups for S3 are done to local s3 endpoints consistently and to a configurable remote endpoint.

## Example yaml config

```yaml
apps:
  cnpg_operator:
    description: |
      CloudNative PostgeSQL Operator for Kubernetes. This lets you create and
      manage many clusters of postgresql, including backups to s3.
    enabled: true
    argo:
      # secret keys to provide for the argocd secret plugin app, none by default
      secret_keys: {}
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: postgres/operators/cloud-native-postgres/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: cnpg-system
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: cnpg-operator
        source_repos:
        - https://github.com/small-hack/argocd-apps
        - https://cloudnative-pg.github.io/charts
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

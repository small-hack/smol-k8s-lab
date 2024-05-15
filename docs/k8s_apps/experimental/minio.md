[MinIO](https://min.io/) is a high-performance, S3 compatible object store. It is built for large scale AI/ML, data lake and database workloads. It is software-defined and runs on any cloud or on-premises infrastructure. MinIO is dual-licensed under open source GNU AGPL v3 and a commercial enterprise license. We at `smol-k8s-lab` use only the AGPLv3 stuff :)

We currently consider MinIO to be in a demo state, but to launch it, you'll need to decide between the operator/tenant helm charts, or the vanilla helm chart.

Check out our [MinIO Argo CD Applications](https://github.com/small-hack/argocd-apps/tree/main/minio).

## Example config for vanilla helm chart

```yaml
apps:
  minio:
    enabled: true
    description: |
      MinIO®️ is a high-performance, S3 compatible object store.

      MinIO is dual-licensed under open source GNU AGPL v3 and a commercial enterprise license.

      learn more: [link=https://min.io/]https://min.io/[/link]
    argo:
      # secrets keys to make available to ArgoCD ApplicationSets
      secret_keys:
        admin_console_hostname: "objectstore.dogpics.biz"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "minio/vanilla/"
      # either the branch or tag to point at in the argo repo above
      revision: "main"
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: "minio"
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: minio
        source_repos:
          - https://github.com/small-hack/argocd-apps
        destination:
          namespaces:
            - argocd
```

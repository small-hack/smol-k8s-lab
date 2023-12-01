[MinIO](https://min.io/) is a high-performance, S3 compatible object store. It is built for large scale AI/ML, data lake and database workloads. It is software-defined and runs on any cloud or on-premises infrastructure. MinIO is dual-licensed under open source GNU AGPL v3 and a commercial enterprise license. We at `smol-k8s-lab` use only the AGPLv3 stuff :)

We currently consider MinIO to be in an alpha state, but to launch it, you just need to provide a `hostname`.

Check out our [MinIO Argo CD Application](https://github.com/small-hack/argocd-apps/tree/main/alpha/minio).

## Example config

```yaml
apps:
  minio:
    enabled: false
    description: |
      MinIO®️ is a high-performance, S3 compatible object store.

      MinIO is dual-licensed under open source GNU AGPL v3 and a commercial enterprise license.

      learn more: [link=https://min.io/]https://min.io/[/link]
    argo:
      # secrets keys to make available to ArgoCD ApplicationSets
      secret_keys:
        hostname: "objectstore.dogpics.biz"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "alpha/minio/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "minio"
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - https://github.com/small-hack/argocd-apps
        destination:
          namespaces:
            - argocd
```

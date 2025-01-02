# Example:

```yaml
apps:
  valkey_cluster:
    description: |
      [link=https://valkey.io]Valkey Cluster[/link] is a fork of redis cluster, which is a key/value store

    enabled: false
    # Initialization of the app through smol-k8s-lab using bitwarden and/or k8s secrets
    init:
      enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys: {}
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: valkey_cluster/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: valkey
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: valkey
        source_repos:
          - "registry-1.docker.io"
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

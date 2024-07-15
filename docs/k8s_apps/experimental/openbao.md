[Openbao](https://openbao.org/) is a self-hosted FOSS alternative to Hashicorp's Vault. We're still experimenting with it, but we're really hopeful!

## Example config

Here's an example config:

```yaml
apps:
  openbao:
    description: |
      ⚠️ [magenta]ALPHA STATUS[/magenta]

      [Openbao](https://openbao.org/) is FOSS Linux Foundation maintained alternative to HashiCorp Vault.
    enabled: false
    # Initialization of the app through smol-k8s-lab using bitwarden and/or k8s secrets
    init:
      enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # name of the cluster that vault is associated with, can be any unique name
        cluster_name: my-cool-cluster
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: demo/openbao/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: openbao
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: vault
        source_repos:
          - https://openbao.github.io/openbao-helm
          - https://github.com/openbao/openbao-helm
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

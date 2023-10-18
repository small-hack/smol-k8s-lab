[Infisical](https://infisical.com/) is a SOC2 Type 2 Certified company that makes Infisical, an end-to-end platform to securely manage secrets and configs across your team and infrastructure, which is our most likely candidate for recommendation for a self-hosted FOSS alternative to Hashicorp's Vault.

`smol-k8s-lab` will support Infisical as a default application in the future after [Infisical/infisical#873](https://github.com/Infisical/infisical/issues/873) or a similar initial user feature is available. 

In the meantime, feel free to checkout out our first shot at an [Infisical Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/infisical), but note that you need to manually set up a first user.

## Example config

Here's an example config for Infisical:

```yaml
  infisical:
    enabled: false
    description: |
      ⚠️ [magenta]Alpha Status[/magenta]

      Infisical is an open-source, end-to-end encrypted secret management platform that enables teams to easily manage and sync their env vars.

      Learn more: [link=https://infisical.com/]https://infisical.com/[/link]
    # Initialization of the app through smol-k8s-lab
    init:
      enabled: true
    argo:
      secret_keys:
        hostname: "k8svault.cooldogs.net"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "infisical/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "infisical"
      # source repos for Argo CD App Project (in addition to app.argo.repo)
      project:
        source_repos:
          - "registry-1.docker.io"
          - "https://dl.cloudsmith.io/public/infisical/helm-charts/helm/charts/"
        destination:
          namespaces:
            - argocd
```

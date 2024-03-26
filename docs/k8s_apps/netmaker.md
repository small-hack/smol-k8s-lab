## Netmaker Argo CD Application
[Netmaker](https://www.netmaker.io/) is a vpn management tool wrapping WireGuard ®️.



## Example Config

```yaml
apps:
  netmaker:
    enabled: false
    description: |
      [link=https://www.netmaker.io/]Netmaker[/link]®️  makes networks with WireGuard. Netmaker automates fast, secure, and distributed virtual networks.
    init:
      enabled: true
      values:
        user: admin
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        hostname: netmaker.example.com
        admin_hostname: admin.netmaker.example.com
        api_hostname: api.netmaker.example.com
        broker_hostname: broker.netmaker.example.com
        auth_provider: oidc
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: demo/netmaker/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: netmaker
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
        - https://github.com/small-hack/netmaker-helm
        - https://small-hack.github.io/netmaker-helm
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

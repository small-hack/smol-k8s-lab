[Collabora Online](https://www.collaboraonline.com/) is a powerful online document editing suite which you can integrate into your own infrastructure or access via one of our trusted hosting partners.

You can use this app to deploy collabora online separately from nextcloud, or you can deploy it as part of the nextcloud app of apps. If deploying as part of nextcloud, leave this app disabled.

## Example config

```yaml
apps:
  collabora_online:
    enabled: false
    description: |
      [link=https://www.collaboraonline.com/]Collabora Online[/link] is a powerful online document editing suite which you can integrate into your own infrastructure or access via one of our trusted hosting partners.

      You can use this app to deploy collabora online separately from nextcloud,
      or you can deploy it as part of the nextcloud app of apps. If deploying as part
      of nextcloud, leave this app disabled.

      you can set an optional admin password with this variable:
        - COLLABORA_ONLINE_PASSWORD
    # Initialization of the app through smol-k8s-lab
    init:
      enabled: false
      values:
        admin_user: admin
        password:
          value_from:
            # you can change this to any env var
            env: COLLABORA_ONLINE_PASSWORD
    argo:
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: collabora_online/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: collabora-online
      # recurse directories in the provided git repo
      directory_recursion: false
      # secret keys to provide for the Argo CD Appset secret plugin, none by default
      secret_keys: {}
      # source repos for Argo CD App Project (in addition to app.argo.repo)
      project:
        name: collabora-online
        source_repos:
          - https://collaboraonline.github.io/online
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

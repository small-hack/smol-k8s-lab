LibreTranslate is a self-hosted language translation tool.

## Example config

```yaml
apps:
  libre_translate:
    description: |
      📖 [link=https://libretranslate.com/]libretranslate[/link] is a self-hosted translation tool.
    enabled: false
    init:
      enabled: true
    argo:
      # secret keys to provide for the argocd secret plugin app, none by default
      secret_keys:
        hostname: ""
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: libretranslate/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: libretranslate
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: libretranslate
        source_repos:
          - https://small-hack.github.io/libretranslate-helm-chart
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
            - libretranslate
```

[Longhorn](https://longhorn.io) is a Cloud native distributed block storage for Kubernetes.

## Example Config

```yaml
apps:
  longhorn:
    description: |
      🐮 [link=https://longhorn.io/]Longhorn[/link] is a Cloud native distributed block storage for Kubernetes.
    enabled: false
    argo:
      # secret keys to provide for the argocd secret plugin app, none by default
      secret_keys: {}
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: demo/longhorn/helm/
      # either the branch or tag to point at in the argo repo above
      revision: "main"
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: longhorn-system
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: longhorn
        source_repos:
          - https://charts.longhorn.io
          - https://github.com/longhorn/longhorn
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```


## Troubleshooting

### Uninstalling

Uninstalling through the Argo CD web interface often doesn't cut it. Try going through the [docs to uninstall longhorn](https://longhorn.io/docs/1.6.0/deploy/uninstall/).

If you have issues deleting a namespace with longhorn, try these steps [here](https://github.com/small-hack/argocd-apps/tree/main?tab=readme-ov-file#troubleshooting-tips).

We also found this issue useful: [longhorn/longhorn#5319](https://github.com/longhorn/longhorn/issues/5319)

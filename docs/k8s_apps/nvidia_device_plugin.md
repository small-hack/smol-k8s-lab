This allows you to install the NVIDIA Device Plugin for using your GPU in Kubernetes.

# Example Config

```yaml
apps:
  nvidia_device_plugin:
    description: |
      ⚠️ [magenta]ALPHA STATUS[/magenta]

      [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) is a helm chart to make the NVIDIA device plugin work on k8s so you can use your GPU on k8s.
    enabled: false
    # Initialization of the app through smol-k8s-lab using bitwarden and/or k8s secrets
    init:
      enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys: {}
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: nvidia_device_plugin/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: nvidia-device-plugin
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: nvidia-device-plugin
        source_repos:
          - https://nvidia.github.io/k8s-device-plugin
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

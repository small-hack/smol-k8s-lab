[Kepler](https://github.com/sustainable-computing-io/kepler) (Kubernetes-based Efficient Power Level Exporter) is a newly added and supported k8s app that uses eBPF to probe energy-related system stats and exports them as Prometheus metrics.

This app is still in alpha state as we learn more about how best to configure it. In the meantime, to our knowledge you can start playing with it after installing it alongside [cilium](/k8s_apps/cilium.md).

You can also check out our [Kepler Argo CD Application](https://github.com/small-hack/argocd-apps/tree/main/demo/kepler).

## Example Configuration

```yaml
apps:
  kepler:
    description: |
      [link=https://github.com/sustainable-computing-io/kepler]Kepler[/link] (Kubernetes Efficient Power Level Exporter) uses eBPF to probe energy-related system stats and exports them as Prometheus metrics.
    enabled: false
    # Initialization of the app through smol-k8s-lab
    init:
      enabled: false
    argo:
      # secret keys to provide for the argocd secret plugin app, none by default
      secret_keys: {}
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: demo/kepler/
      # either the branch or tag to point at in the argo repo above
      revision: "main"
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: kepler
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
        - https://sustainable-computing-io.github.io/kepler-helm-chart
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

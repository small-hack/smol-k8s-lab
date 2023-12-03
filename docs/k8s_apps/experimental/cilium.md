[cilium](https://cilium.io/) is an open source, cloud native solution for providing, securing, and observing network connectivity between workloads, fueled by the revolutionary Kernel technology eBPF.

Learn more about our [cilium Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/alpha/cilium).

This application is still in an alpha state with `smol-k8s-lab`, but you can get started using it by just providing a hostname in the config file like this:

```yaml
apps:
  # This app is installed with helm or manifests depending on what is recommended
  # for your k8s distro. Becomes managed by ArgoCD if you enable it below
  cilium:
    enabled: false
    description: |
      Cilium is an open source, cloud native solution for providing, securing, and observing network connectivity between workloads, fueled by the revolutionary Kernel technology eBPF.

      Learn more: [link=https://cilium.io/]https://cilium.io/[/link]
    # Initialize of the app through smol-k8s-lab
    init:
      enabled: true
    argo:
      secret_keys:
        hostname: "cilium.cooldogsontheinternet.com"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "alpha/cilium/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "cilium"
      # source repos for Argo CD cilium Project
      project:
        source_repos:
          - "https://helm.cilium.io/"
        destination:
          namespaces:
            - argocd
            - cilium
```

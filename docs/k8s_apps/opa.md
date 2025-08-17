# Open Policy Agent Gatekeeper

An experimental app for writing security policies for Kubernetes.

```yaml
apps:
  opa:
    enabled: true
    description: |
      [magenta]⚠️ Experimental[/magenta]
      [link=https://open-policy-agent.github.io/gatekeeper/website/]OPA (Open Policy Agent) Gatekeeper[/link] is a customizable cloud native policy controller that helps enforce policies and strengthen governance. Put simply, it lets you set up policies for security requirements in Kubernetes.

    init:
      enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys: []
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to
      path: opa/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: gatekeeper-system
      # recurse directories in the provided git repo
      # if set to false, we will not deploy the CSI driver
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: opa
        source_repos:
          - https://open-policy-agent.github.io/gatekeeper/charts
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

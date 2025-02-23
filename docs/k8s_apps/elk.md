[Elk](https://github.com/elk-zone/elk) is a Mastodon and GoToSocial web client AKA a frontend for GoToSocial. We're using the [0hlov3/charts:elk-frontend](https://github.com/0hlov3/charts/tree/main/charts/elk-frontend) helm chart.

## Example configs

```yaml
apps:
  elk:
    description: |
       [link=https://github.com/elk-zone/elk]elk[/link] is an open source self hosted frontend for Mastodon and GoToSocial.
    enabled: false
    init:
      enabled: false
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # hostname that users go to in the browser
        hostname: ""
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: elk/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: elk
      # recurse directories in the git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: elk
        # depending on if you use seaweedfs or minio, you can remove the other source repo
        source_repos:
          - https://charts.fsociety.social
          - https://charts.schoenwald.aero
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

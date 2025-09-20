[Elk](https://github.com/elk-zone/elk) is a Mastodon and GoToSocial web client AKA a frontend for GoToSocial. We're using the [0hlov3/charts:elk-frontend](https://github.com/0hlov3/charts/tree/main/charts/elk-frontend) helm chart.

<img width="1238" alt="Screenshot of all deployed Elk resources in the Argo CD web interface using tree mode. It features the main app, elk-frontend, which branches into a pvc, elk-frontend-data, a secret elk-env, a service elk-frontend, a service account, elk-frontend, a deployment, elk-frontend, and an ingress, elk-frontend. The service branches into an endpoint, elk-frontend, and an endpoint slice, elk-frontend-randomcharacters. The deployment branches into 3 replica history versions with one of them branching into an elk-frontend pod. The ingress branches into a certificate, elk-tls, which branches into a certificate request, elk-tls-1, which branches into an order, elk-tls-randomcharacters" src="https://github.com/user-attachments/assets/a1bacf8c-03a0-4039-9873-359cefe70b23" />

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

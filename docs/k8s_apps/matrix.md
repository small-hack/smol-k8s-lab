[Matrix](https://matrix.org/) is an open protocol for decentralised, secure communications. 

`smol-k8s-lab` deploys a matrix synapse server, element (a web frontend), and a turn server (voice server).

The main variable you need to worry about when setting up matrix is your `hostname`.

## Example config

```yaml
apps:
  matrix:
    description: |
      Matrix is an open protocol for decentralised, secure communications.
      This deploys a matrix synapse server, element (web frontend), and turn server (voice)

      Learn more: [link=https://matrix.org/]https://matrix.org/[/link]

      smol-k8s-lab supports initialization by setting up your create initial secrets for your hostnames, and credentials for: postgresql, admin user, SMTP
    enabled: false
    init:
      enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        hostname: "chat.beepboopfordogsnoots.city"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "matrix/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "matrix"
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - "registry-1.docker.io"
          - "https://jessebot.github.io/matrix-chart"
        destination:
          namespaces:
            - argocd
```

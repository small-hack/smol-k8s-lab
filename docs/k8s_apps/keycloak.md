We've disabled keycloak at this time because we don't have the time to maintain it and it's harder to use than zitadel.

```yaml
apps:
  keycloak:
    enabled: false
    description: |
      keycloak is an IAM provider that you can use with ArgoCD for user/group management and oauth2
      smol-k8s-lab initializes keycloak by creating an initial user & clients for ArgoCD and vouch this will also prompt you for input for creating an admin user. Switch to initialization to false if you want to use your own argo repo that does not not use the appset_secret_plugin or setup an initial user/clients
    init:
      enabled: true
      values:
        # first human user to setup
        username: ""
        first_name: ""
        last_name: ""
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        hostname: ""
        mail_hostname: ""
        default_realm: "default"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "keycloak/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "keycloak"
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - "registry-1.docker.io"
        destination:
          namespaces:
            - argocd
```

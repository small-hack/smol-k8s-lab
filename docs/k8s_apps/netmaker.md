## Netmaker Argo CD Application
[Netmaker](https://www.netmaker.io/) is a vpn management tool wrapping WireGuard ®️.

![Screenshot of the Argo CD web interface showing the netmaker app of apps. The netmaker app shows three children: netmaker-persistence application in healthy state, netmaker-appset with a child of netmaker-helm app both in healthy state, and the netmaker external secrets appset with a child app of netmaker-externalsecrets also both in a healthy state](./netmaker.png)

![Screenshot of the Argo CD web interface showing the netmaker-helm app's networking view. From the left it shows connection from the internet to the ip 192.168.42.42 which then connects to three ingresses, which connect to three services, which connect to three pods. The ingresses are netmaker-api, netmaker-mqtt, and netmaker-ui, which similarly named services and pods. Outside of that part of the chart are two services netmaker-postgresql and netmaker-postgresql-hl. Both connect to a pod called netmaker-postgresql-0](./netmaker-network.png)

We're currently using our [own home grown helm chart](https://github.com/small-hack/netmaker-helm) as it supports existing secrets and initial super admin user creation. You can learn more about the Argo CD ApplicationSet [here](https://github.com/small-hack/argocd-apps/tree/main/netmaker).

### Initialization Features

If you set `apps.netmaker.init.enabled` to `true`, we will create a Zitadel app for use with oidc, and also create an initial admin user, plus disable the GUI registration for security sake.


## Example Config

```yaml
apps:
  netmaker:
    enabled: false
    description: |
      [link=https://www.netmaker.io/]Netmaker[/link]®️  makes networks with WireGuard. Netmaker automates fast, secure, and distributed virtual networks.
    init:
      enabled: true
      values:
        # this creates a super admin user and disables the GUI registration form
        # if using the default config, we select a password for you and update your bitwarden
        admin_user: admin
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        hostname: netmaker.example.com
        admin_hostname: admin.netmaker.example.com
        api_hostname: api.netmaker.example.com
        broker_hostname: broker.netmaker.example.com
        auth_provider: oidc
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: netmaker/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: netmaker
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
        - https://github.com/small-hack/netmaker-helm
        - https://small-hack.github.io/netmaker-helm
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

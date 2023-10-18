[Mastodon](https://joinmastodon.org/) is a FOSS social media networking platform based on [ActivityPub](https://www.w3.org/TR/activitypub/).

This app is a work in progress as we find the best way to sustainably run Mastodon on Kubernetes which is another app that didn't really have the cloud in mind when it came to be, but as it's the best we got, we still love it dearly.

If you're using the default `smol-k8s-lab` Mastodon app, you'll need to provide both `hostname` and `mail_hostname` for the ApplicationSet.

Check out our [Mastodon Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/mastodon)!

## Example Config

```yaml
apps:
  mastodon:
    description: |
       mastodon is an open source self hosted social media network.

       learn more: [link=https://joinmastodon.org/]https://joinmastodon.org/[/link]

       smol-k8s-lab supports initializing mastodon, by setting up your hostname and SMTP credentials as well as your credentials for redis, postgresql, and an admin user
    enabled: false
    init:
      enabled: true
    argo:
      # secrets keys to make available to ArgoCD ApplicationSets
      secret_keys:
        hostname: "social.cooldogsontheinternet.net"
        mail_hostname: "mail.beepboop.com"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "mastodon/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "social"
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - "registry-1.docker.io"
          - "https://jessebot.github.io/mastodon-helm-chart"
        destination:
          namespaces:
            - argocd
```

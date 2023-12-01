[Mastodon](https://joinmastodon.org/) is a FOSS social media networking platform based on [ActivityPub](https://www.w3.org/TR/activitypub/).

This app is a work in progress as we find the best way to sustainably run Mastodon on Kubernetes, which is another app that didn't really have the cloud in mind when it came to be, but as it's the best we got, we still love it dearly.

We currently maintain [our own Mastodon helm chart](https://github.com/jessebot/mastodon-helm-chart) as the [official Mastodon helm chart](https://github.com/mastodon/chart) is missing some features from [PR](https://github.com/mastodon/chart/pulls)s that have yet to be merged. The goal is to at least move to the [Bitnami hosted Mastodon helm chart](https://github.com/bitnami/charts/tree/main/bitnami/mastodon) after [bitnami/charts#19179](https://github.com/bitnami/charts/pull/19179) is merged, as then there's one less helm chart for small-hack to manage on its own.

Check out our [Mastodon Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/mastodon)!

## Required Init Values

To use the default `smol-k8s-lab` Argo CD Application, you'll need to provide one time init values for:

- `admin_user`
- `admin_email`
- `smtp_user`
- `smtp_host`

## Required ApplicationSet Values

And you'll also need to provide the following values to be templated for your personal installation:

- `hostname` - the hostname for your web interface

## Required Sensitive Values

If you'd like to setup SMTP, we need a bit more sensitive data. This includes your:

- SMTP password

You have two options. You can:

- respond to a one-time prompt for these credentials (one-time _per cluster_)
- export an environment variable

### Environment Variables

You can export the following env vars and we'll use them for your sensitive data:

- `MASTODON_SMTP_PASSWORD`
- `MASTODON_S3_BACKUP_ACCESS_ID`
- `MASTODON_S3_BACKUP_SECRET_KEY`
- `MASTODON_RESTIC_REPO_PASSWORD`

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
      values:
        admin_user: "tootadmin"
        admin_email: ""
        smtp_user: "change me to enable mail"
        smtp_host: "change@me-to-enable.mail"
    argo:
      # secrets keys to make available to ArgoCD ApplicationSets
      secret_keys:
        hostname: "social.cooldogsontheinternet.net"
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

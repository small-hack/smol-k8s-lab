[Mastodon](https://joinmastodon.org/) is a FOSS social media networking platform based on [ActivityPub](https://www.w3.org/TR/activitypub/).

This app is a work in progress as we find the best way to sustainably run Mastodon on Kubernetes, which is another app that didn't really have the cloud in mind when it came to be, but as it's the best we got, we still love it dearly.

We currently maintain [our own Mastodon helm chart](https://github.com/jessebot/mastodon-helm-chart) as the [official Mastodon helm chart](https://github.com/mastodon/chart) is missing some features from [PR](https://github.com/mastodon/chart/pulls)s that have yet to be merged. The goal is to at least move to the [Bitnami hosted Mastodon helm chart](https://github.com/bitnami/charts/tree/main/bitnami/mastodon) after [bitnami/charts#19179](https://github.com/bitnami/charts/pull/19179) is merged, as then there's one less helm chart for small-hack to manage on its own.

Check out our [Mastodon Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/mastodon)!

<img src="/images/screenshots/mastodon_screenshot.png" alt="screenshot of the mastodon applicationset in Argo CD's web interface using the tree mode view.">

<img src="/images/screenshots/mastodon_networking_screenshot.png" alt="screenshot of the mastodon applicationset in Argo CD's web interface using the tree mode view.">

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

If you'd like to setup SMTP, we need a bit more sensitive data. This includes your SMTP password, S3 backup credentials, and restic repo password.

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
       [link=https://joinmastodon.org/]Mastodon[/link] is an open source self hosted social media network.

       smol-k8s-lab supports initializing mastodon, by setting up your hostname, SMTP credentials, redis credentials, postgresql credentials, and an admin user credentials. We pass all credentials as secrets in the namespace and optionally save them to Bitwarden.

       smol-k8s-lab also creates a local s3 endpoint and as well as S3 bucket and credentials if you enable set mastodon.argo.secret_keys.s3_provider to "minio" or "seaweedfs". Both seaweedfs and minio require you to specify a remote s3 endpoint, bucket, region, and accessID/secretKey so that we can make sure you have remote backups.

       To provide sensitive values via environment variables to smol-k8s-lab use:
         - MASTODON_SMTP_PASSWORD
         - MASTODON_S3_BACKUP_ACCESS_ID
         - MASTODON_S3_BACKUP_SECRET_KEY
         - MASTODON_RESTIC_REPO_PASSWORD
    enabled: false
    init:
      enabled: true
      values:
        # admin user
        admin_user: "tootadmin"
        # admin user's email
        admin_email: ""
        # mail server to send verification and notification emails
        smtp_host: "change@me-to-enable.mail"
        # mail user for smtp host
        smtp_user: "change me to enable mail"
      sensitive_values:
        # these can be passed in as env vars if you pre-pend MASTODON_ to each one
        - SMTP_PASSWORD
        - S3_BACKUP_ACCESS_ID
        - S3_BACKUP_SECRET_KEY
        - RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        admin_user: tootadmin
        # hostname that users go to in the browser
        hostname: ""
        # set the local s3 provider for mastodon's public data in one bucket 
        # and private database backups in another. can be minio or seaweedfs
        s3_provider: seaweedfs
        # how large the backing pvc's capacity should be for minio or seaweedfs
        s3_pvc_capacity: 120Gi
        # local s3 endpoint for postgresql backups, backed up constantly
        s3_endpoint: ""
        s3_region: eu-west-1
        # Remote S3 configuration, for pushing remote backups of your local postgresql backups
        # these are done only nightly right now, for speed and cost optimization
        s3_backup_endpoint: ""
        s3_backup_region: ""
        s3_backup_bucket: ""
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: mastodon/small-hack/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # namespace to install the k8s app in
      namespace: mastodon
      # recurse directories in the git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        # depending on if you use seaweedfs or minio, you can remove the other source repo
        source_repos:
          - registry-1.docker.io
          - https://small-hack.github.io/cloudnative-pg-cluster-chart
          - https://operator.min.io/
          - https://seaweedfs.github.io/seaweedfs/helm
          - https://small-hack.github.io/mastodon-helm-chart
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

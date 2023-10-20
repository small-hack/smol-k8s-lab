[Nextcloud](https://nextcloud.com/) is an Open Source and self hosted personal cloud. We optionally deploy it for you to save you some time in testing.

Part of the `smol-k8s-lab` init process is that we will put the following into your Bitwarden vault:
- administration credentials
- SMTP credentials
- PostgreSQL credentials


## Required Init Values

To use the default `smol-k8s-lab` Argo CD Application, you'll need to provide one time init values for:

- `admin_user`
- `smtp_user`
- `smtp_host`

## Required ApplicationSet Values

And you'll also need to provide the following values to be templated for your personal installation:

- `hostname`
- `backup_method`

After you select which backup method you want to use, you need to provide either:

- `backup_s3_endpoint`
- `backup_s3_bucket`

Or:

- `backup_mount_path`

## Required Sensitive Values

If you'd like to setup SMTP and backups, we need a bit more sensitive data. This includes your:

- SMTP password
- restic repo password
- S3 access key (only if backup method is set to s3)
- S3 access id (only if backup method is set to s3)

You have two options. You can:

- respond to a one-time prompt for these credentials (one-time _per cluster_)
- export environment variables

### Environment Variables

You can export the following env vars and we'll use them for your sensitive data:

- `NEXTCLOUD_SMTP_PASSWORD`
- `NEXTCLOUD_RESTIC_REPO_PASSWORD`

Only required if backup_method is set to s3:
- `NEXTCLOUD_S3_ACCESS_KEY`
- `NEXTCLOUD_S3_ACCESS_ID`

## Official Repo

You can learn more about how the Nextcloud Argo CD ApplicationSet is installed at [small-hack/argocd-apps/nextcloud](https://github.com/small-hack/argocd-apps/tree/main/nextcloud).


## Complete Example Config

```yaml
apps:
  nextcloud:
    enabled: false
    description: |
      Nextcloud Hub is the industry-leading, fully open-source, on-premises content collaboration platform. Teams access, share and edit their documents, chat and participate in video calls and manage their mail and calendar and projects across mobile, desktop and web interfaces

      Learn more: [link=https://nextcloud.com/]https://nextcloud.com/[/link]

      smol-k8s-lab supports initialization by setting up your admin username, password, and SMTP username and password, as well as your redis and postgresql credentials

      Note: smol-k8s-lab is not officially affiliated with nextcloud or vis versa
    # initialize the app by setting up new k8s secrets and/or Bitwarden items
    init:
      enabled: true
      values:
        admin_user: 'mycooladminuser'
        smtp_user: 'mycoolsmtpusername'
        smtp_host: 'mail.cooldogs.net'
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        hostname: "cloud.cooldogs.net"
        backup_method: "s3"
        backup_s3_endpoint: "s3.us-east.cooldogs.net"
        backup_s3_bucket: "my-cool-backup-bucket"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "nextcloud/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "nextcloud"
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - "registry-1.docker.io"
          - "https://nextcloud.github.io/helm"
        destination:
          namespaces:
            - argocd
            - nextcloud
```

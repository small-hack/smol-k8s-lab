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


## Required Sensitive Values

If you'd like to setup SMTP and backups, we need a bit more sensitive data. This includes your:

- SMTP password
- restic repo password
- s3 backup credentials

You have two options. You can:

- respond to a one-time prompt for these credentials (one-time _per cluster_)
- export environment variables

### Environment Variables

You can export the following env vars and we'll use them for your sensitive data:

- `NEXTCLOUD_SMTP_PASSWORD`
- `NEXTCLOUD_S3_BACKUP_ACCESS_KEY`
- `NEXTCLOUD_S3_BACKUP_ACCESS_ID`
- `NEXTCLOUD_RESTIC_REPO_PASSWORD`

## Official Repo

You can learn more about how the Nextcloud Argo CD ApplicationSet is installed at [small-hack/argocd-apps/nextcloud](https://github.com/small-hack/argocd-apps/tree/main/nextcloud).


## Complete Example Config

```yaml
apps:
  nextcloud:
    enabled: false
    description: |
      [link=https://nextcloud.com/]Nextcloud Hub[/link] is the industry-leading, fully open-source, on-premises content collaboration platform. Teams access, share and edit their documents, chat and participate in video calls and manage their mail and calendar and projects across mobile, desktop and web interfaces

      smol-k8s-lab supports initialization by setting up your admin username, password, and SMTP username and password, as well as your redis and postgresql credentials.

      To avoid providing sensitive values everytime you run smol-k8s-lab, consider exporting the following environment variables before running smol-k8s-lab:
        - NEXTCLOUD_SMTP_PASSWORD
        - NEXTCLOUD_S3_BACKUP_ACCESS_KEY
        - NEXTCLOUD_S3_BACKUP_ACCESS_ID
        - NEXTCLOUD_RESTIC_REPO_PASSWORD

      Note: smol-k8s-lab is not affiliated with Nextcloud GmbH. This is a community-supported-only install method.
    # initialize the app by setting up new k8s secrets and/or Bitwarden items
    init:
      enabled: true
      values:
        admin_user: 'mycooladminuser'
        smtp_user: 'mycoolsmtpusername'
        smtp_host: 'mail.cooldogs.net'
      sensitive_values:
        - SMTP_PASSWORD
        - S3_BACKUP_ACCESS_KEY
        - S3_BACKUP_ACCESS_ID
        - RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        hostname: "cloud.cooldogs.net"
        # choose S3 as the local primary object store from either: seaweedfs, or minio
        # SeaweedFS - deploy SeaweedFS filer/s3 gateway
        # MinIO     - deploy MinIO vanilla helm chart
        s3_provider: seaweedfs
        # the endpoint you'd like to use for your minio or SeaweedFS instance
        s3_endpoint: 'nextcloud-s3.cooldogs.net'
        # how large the backing pvc's capacity should be for minio or seaweedfs
        s3_pvc_capacity: 100Gi
        s3_region: eu-west-1
        s3_backup_endpoint: "s3.us-east-1.cooldogs.net"
        s3_backup_bucket: "my-cool-backup-bucket"
        s3_backup_region: "us-east-1"
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "nextcloud/app_of_apps/"
      # either the branch or tag to point at in the argo repo above
      ref: "main"
      # namespace to install the k8s app in
      namespace: "nextcloud"
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - registry-1.docker.io
          - https://nextcloud.github.io/helm
          - https://small-hack.github.io/cloudnative-pg-cluster-chart
          - https://seaweedfs.github.io/seaweedfs/helm
          - https://github.com/seaweedfs/seaweedfs
        destination:
          namespaces: []
```

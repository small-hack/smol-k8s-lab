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
- `default_phone_region`

*These determine how you'd like to set up persistence for nextcloud. We recommend just files enabled for now*
- `files_pvc_enabled`
- `files_storage`
- `files_access_mode`
- `config_pvc_enabled`
- `config_storage`
- `config_access_mode`

*These are used for local backups in the same cluster to a nextcloud namespaced seaweedfs instance*
- `s3_provider`
- `s3_endpoint`
- `s3_pvc_capacity`
- `s3_region`

*For backups, you must put nextcloud into maintenance_mode. This sets a time to do that*
- `maintenance_mode_on_schedule`
- `maintenance_mode_off_schedule`


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
      restore:
        enabled: true
        cnpg_restore: true
        restic_snapshot_ids:
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          seaweedfs_master: latest
          nextcloud_files: latest
      values:
        admin_user: 'mycooladminuser'
        smtp_user: 'mycoolsmtpusername'
        smtp_host: 'mail.cooldogs.net'
        smtp_password:
          value_from:
            env: NEXTCLOUD_SMTP_PASSWORD
    backups:
      # cronjob syntax schedule to run nextcloud pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for nextcloud postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the cnpg backup shows as completed
      # before it actually is, due to the wal archive it lists as it's end not
      # being in the backup yet
      postgres_schedule: 0 0 0 * * *
      s3:
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: s3.eu-central-003.backblazeb2.com
        bucket: my-nextcloud-bucket
        region: eu-central-003
        secret_access_key:
          value_from:
            env: NEXTCLOUD_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: NEXTCLOUD_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: NEXTCLOUD_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        hostname: "cloud.cooldogs.net"
        default_phone_region: NL
        # enable persistent volume claim for nextcloud files storage
        files_pvc_enabled: 'true'
        # size of files pvc storage
        files_storage: 100Gi
        files_access_mode: ReadWriteOnce
        # enable persistent volume claim for nextcloud config storage
        config_pvc_enabled: 'false'
        # size of config pvc storage
        config_storage: 20Gi
        config_access_mode: ReadWriteOnce
        # choose S3 as the local primary object store from either: seaweedfs, or minio
        # SeaweedFS - deploy SeaweedFS filer/s3 gateway
        # MinIO     - deploy MinIO vanilla helm chart
        s3_provider: seaweedfs
        # the endpoint you'd like to use for your minio or SeaweedFS instance
        s3_endpoint: cloud-s3.cooldogs.net
        # how large the backing pvc's capacity should be for minio or seaweedfs
        s3_pvc_capacity: 10Gi
        s3_region: eu-west-1
        # cronjob schedule to turn on nextcloud maintenance mode for backups
        maintenance_mode_on_schedule: 30 23 * * *
        # cronjob schedule to turn off nextcloud maintenance mode after backups
        maintenance_mode_off_schedule: 30 1 * * *
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "nextcloud/app_of_apps/"
      # either the branch or tag to point at in the argo repo above
      revision: "main"
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: "nextcloud"
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: nextcloud
        source_repos:
          - registry-1.docker.io
          - https://nextcloud.github.io/helm
          - https://small-hack.github.io/cloudnative-pg-cluster-chart
          - https://seaweedfs.github.io/seaweedfs/helm
          - https://github.com/seaweedfs/seaweedfs
        destination:
          namespaces: []
```

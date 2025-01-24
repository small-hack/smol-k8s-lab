[GoToSocial](https://gotosocial.org/) is a Free and Open Source social media networking platform based on [ActivityPub](https://www.w3.org/TR/activitypub/).

We are mostly stable for running GoToSocial on Kubernetes. Check out our [GoToSocial Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/gotosocial/small-hack):

<a href="../../assets/images/screenshots/gotosocial_screenshot.png">
<img src="../../assets/images/screenshots/gotosocial_screenshot.png" alt="screenshot of the gotosocial applicationset in Argo CD's web interface using the tree mode view. the main gotosocial app has 6 child apps: gotosocial-app-set with child gotosocial-web-app, gotosocial-external-secrets-appset with child gotosocial-external-secrets, gotosocial-postgres-app-set with child gotosocial-postgres-cluster, gotosocial-s3-provider-app-set with child gotosocial-seaweedfs, and gotosocial-s3-pvc-appset with child gotosocial-s3-pvc.">
</a>

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

- `GOTOSOCIAL_SMTP_PASSWORD`
- `GOTOSOCIAL_S3_BACKUP_ACCESS_ID`
- `GOTOSOCIAL_S3_BACKUP_SECRET_KEY`
- `GOTOSOCIAL_RESTIC_REPO_PASSWORD`

## Example Config

```yaml
apps:
  gotosocial:
    description: |
       [link=https://gotosocial.org]gotosocial[/link] is an open source self hosted social media network.

       smol-k8s-lab supports initializing gotosocial, by setting up your hostname, SMTP credentials, postgresql credentials, OIDC Credentials, and an admin user credentials. We pass all credentials as Secrets in the namespace and optionally save them to Bitwarden.

       smol-k8s-lab also creates a local s3 endpoint and as well as S3 bucket and credentials if you enable set gotosocial.argo.secret_keys.s3_provider to "minio" or "seaweedfs". Both seaweedfs and minio require you to specify a remote s3 endpoint, bucket, region, and accessID/secretKey so that we can make sure you have remote backups.

       To provide sensitive values via environment variables to smol-k8s-lab use:
         - GOTOSOCIAL_SMTP_PASSWORD
         - GOTOSOCIAL_S3_BACKUP_ACCESS_ID
         - GOTOSOCIAL_S3_BACKUP_SECRET_KEY
         - GOTOSOCIAL_RESTIC_REPO_PASSWORD
    enabled: false
    init:
      enabled: true
      restore:
        enabled: false
        cnpg_restore: true
        restic_snapshot_ids:
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          # restic snapshot id for the gotosocial pvc to restore
          gotosocial: latest
      values:
        # admin user
        admin_user: "gotosocialadmin"
        # admin user's email
        admin_email: ""
        # mail server to send verification and notification emails
        smtp_host: "change@me-to-enable.mail"
        # mail server port to send verification and notification emails
        smtp_port: "25"
        # mail user for smtp host
        smtp_user: "change me to enable mail"
        smtp_password:
          value_from:
            env: GOTOSOCIAL_SMTP_PASSWORD
    backups:
      # cronjob syntax schedule to run gotosocial pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for gotosocial postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the backup shows as completed before
      # it actually is
      postgres_schedule: 0 0 0 * * *
      s3:
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: s3.eu-central-003.backblazeb2.com
        bucket: my-gotosocial-backups
        region: eu-central-003
        secret_access_key:
          value_from:
            env: GOTOSOCIAL_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: GOTOSOCIAL_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: GOTOSOCIAL_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # admin user for your gotosocial instance
        admin_user: gotosocialadmin
        # hostname that users go to in the browser
        hostname: ""
        # set the local s3 provider for gotosocial's public data in one bucket
        # and private database backups in another. can be minio or seaweedfs
        s3_provider: seaweedfs
        # how large the backing pvc's capacity should be for minio or seaweedfs
        s3_pvc_capacity: 120Gi
        # local s3 endpoint for postgresql backups, backed up constantly
        s3_endpoint: ""
        # optional region where your s3 bucket lives
        s3_region: eu-west-1
        # access mode the gotosocial pvc
        access_mode: ReadWriteOnce
        # amount of storage for the gotosocial pvc
        storage: 10Gi
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: gotosocial/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: gotosocial
      # recurse directories in the git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: gotosocial
        # depending on if you use seaweedfs or minio, you can remove the other source repo
        source_repos:
          - registry-1.docker.io
          - https://small-hack.github.io/cloudnative-pg-cluster-chart
          - https://operator.min.io/
          - https://seaweedfs.github.io/seaweedfs/helm
          - https://charts.schoenwald.aero
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

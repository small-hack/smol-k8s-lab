[Zitadel](https://zitadel.com/) is an Identity Management solution that includes acting as an OIDC provider.

<a href="../../assets/images/screenshots/zitadel_screenshot.png">
<img src="../../assets/images/screenshots/zitadel_screenshot.png" alt="screenshot of the Argo CD web interface showing the Zitadel app of apps in tree view mode. The zitadel app of apps has 5 children: zitadel-bitwarden-eso, zitadel-postgres-app-set, zitadel-s3-provider-app-set, zitadel-s3-pvc-app-set, and zitadel-web-app-set">
</a>

Zitadel is one of the more complex apps that `smol-k8s-lab` supports out of the box. For initialization, you need to pass in the following info:

- `username` - name of the first admin user to create
- `email` - email of the first admin user
- `first name` - first name of the first admin user
- `last name` - last name of the first admin user
- `gender` - optional - the gender of the first admin user

The above values are used to create an initial user. We also create Argo CD admin and users groups to be used with an Argo CD OIDC app that we prepare. If Vouch is enabled, we also create an OIDC app for that as well as a user group. You initial user is automatically added to all the groups we create.

Finally, we create a groupsClaim so that all queries for auth also process the user's groups.

In addition to those one time init values, we also require a hostname to use for the Zitadel API and web frontend.

## Sensitive values

Sensitive values can be provided via environment variables using a `value_from` map on any value under `init.values` or `backups`. Example of providing s3 credentials and restic repo password via sensitive values:

```yaml
apps:
  zitadel:
    backups:
      s3:
        secret_access_key:
          value_from:
            # can be any env var
            env: ZITADEL_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            # can be any env var
            env: ZITADEL_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          # can be any env var
          env: ZITADEL_RESTIC_REPO_PASSWORD
```

## Backups

Backups are a new feature in `v5.0.0` that enable backing up your postgres cluster and PVCs via restic to a configurable remote S3 bucket. If you have `init.enabled` set to `true` and you're using our pre-configured `argo.repo`, we support both instant backups, and scheduled backups.

When running a zitadel backup, we will initiate a [Cloud Native Postgresql backup](https://cloudnative-pg.io/documentation/1.23/backup/#on-demand-backups) to your local seaweedfs cluster that we setup for you, and then wait until the last wal archive associated with that backup is complete. After that, we start a k8up backup job to backup all of your important PVCs to your configured s3 bucket.

To use the backups feature, you'll need to configure the values below.

```yaml
apps:
  zitadel:
    backups:
      # cronjob syntax schedule to run zitadel seaweedfs pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for zitadel postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the cnpg backup shows as completed
      # before it actually is, due to the wal archive it lists as it's end not
      # being in the backup yet
      postgres_schedule: 0 0 0 * * *
      s3:
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: s3.eu-central-003.backblazeb2.com
        bucket: my-zitadel-backup-bucket
        region: eu-central-003
        secret_access_key:
          value_from:
            env: ZITADEL_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: ZITADEL_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: ZITADEL_RESTIC_REPO_PASSWORD
```

## Restores

Restores are a new feature in `v5.0.0` that enable restoring your cluster via restic from a configurable remote S3 bucket. If you have `init.enabled` set to `true` and you're using our pre-configured `argo.repo`, we support restoring both your postgres cluster and PVCs. A restore is a kind of initialization process, so it lives under the `init` section of the config for your application, in this case, zitadel. Here's an example:

```yaml
apps:
  zitadel:
    init:
      enabled: true
      restore:
        enabled: false
        cnpg_restore: true
        restic_snapshot_ids:
          # these can all be any restic snapshot ID, but default to latest
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          seaweedfs_master: latest
```

The restore process will put your secrets into place, then restore your seaweedfs cluster first, followed by your postgresql cluster, and then it will install your zitadel argocd app as normal.

#### Sensitive values before `v5.0.0`

`smol-k8s-lab` did not originally support the `value_from` map. If you're using a version *before `v5.0.0`*, to avoid having to provide sensitive values every time you run `smol-k8s-lab` with zitadel enabled, set up the following environment variables:

- `ZITADEL_S3_BACKUP_ACCESS_ID`
- `ZITADEL_S3_BACKUP_SECRET_KEY`
- `ZITADEL_RESTIC_REPO_PASSWORD`

## Example config

```yaml
apps:
  zitadel:
    enabled: false
    description: |
      [link=https://zitadel.com/opensource]ZITADEL[/link] is an open source self hosted IAM platform for the cloud era

      smol-k8s-lab supports initialization of:
        - an admin service account
        - a human admin user (including an autogenerated password)
        - a project with a name of your chosing
        - 2 OIDC applications for Argo CD and Vouch
        - 2 Argo CD groups (admins and users), 1 vouch groups
        - groupsClaim action to enforce group roles on authentication
        - updates your appset_secret_plugin secret and refreshes the pod

      The default app will also deploy SeaweedFS to backup your database which in turn is backed up to a remote s3 provider of your choice.

      To provide sensitive values via environment variables to smol-k8s-lab use:
        - ZITADEL_S3_BACKUP_ACCESS_ID
        - ZITADEL_S3_BACKUP_SECRET_KEY
        - ZITADEL_RESTIC_REPO_PASSWORD
    init:
      # Switch to false if you don't want to create initial secrets or use the
      # API via a service account to create the above described resources
      enabled: true
      values:
        username: 'certainlynotadog'
        email: 'notadog@humans.com'
        first_name: 'Dogsy'
        last_name: 'Dogerton'
        # options: GENDER_UNSPECIFIED, GENDER_MALE, GENDER_FEMALE, GENDER_DIVERSE
        # more coming soon, see: https://github.com/zitadel/zitadel/issues/6355
        gender: GENDER_UNSPECIFIED
        # name of the default project to create OIDC applications in
        project: core
        # coming soon after we refactor a bit
        # smtp_password:
        #   value_from:
        #     env: ZITADEL_SMTP_PASSWORD
      restore:
        enabled: false
        cnpg_restore: true
        restic_snapshot_ids:
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          seaweedfs_master: latest
    backups:
      # cronjob syntax schedule to run zitadel seaweedfs pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for zitadel postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the cnpg backup shows as completed
      # before it actually is, due to the wal archive it lists as it's end not
      # being in the backup yet
      postgres_schedule: 0 0 0 * * *
      s3:
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: s3.eu-central-003.backblazeb2.com
        bucket: my-zitadel-backup-bucket
        region: eu-central-003
        secret_access_key:
          value_from:
            env: ZITADEL_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: ZITADEL_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: ZITADEL_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to ArgoCD ApplicationSets
      secret_keys:
        # FQDN to use for zitadel
        hostname: 'zitadel.gooddogs.com'
        # type of database to use: postgresql or cockroachdb
        database_type: postgresql
        # set the local s3 provider for zitadel's database backups. can be minio or seaweedfs
        s3_provider: seaweedfs
        # local s3 endpoint for postgresql backups, backed up constantly
        s3_endpoint: 'zitadel-s3.gooddogs.com'
        # capacity for the PVC backing your local s3 instance
        s3_pvc_capacity: 2Gi
      # repo to install the Argo CD app from
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      # if you want to use cockroachdb, change to zitadel/zitadel_and_cockroachdb
      path: zitadel/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: zitadel
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: zitadel
        source_repos:
          - https://charts.zitadel.com
          - https://zitadel.github.io/zitadel-charts
          - https://small-hack.github.io/cloudnative-pg-cluster-chart
          - https://operator.min.io/
          - https://seaweedfs.github.io/seaweedfs/helm
        destination:
          namespaces: []
```

You can learn more about our Zitadel Argo CD Application at [small-hack/argocd-apps/zitadel](https://github.com/small-hack/argocd-apps/tree/main/zitadel).

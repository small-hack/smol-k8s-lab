[Matrix](https://matrix.org/) is an open protocol for decentralised, secure communications.

`smol-k8s-lab` deploys a matrix synapse server, element (a web frontend), and a turn server (voice server).

<a href="../../assets/images/screenshots/matrix.png">
<img src="../../assets/images/screenshots/matrix.png" alt="screenshot of the Argo CD web interface showing the matrix app of apps in tree view mode, which shows the following children: external secrets appset, postgres appset, matrix PVC appset, s3 provider appset, s3 pvc app set, and matrix web app set.">
</a>

<details>
  <summary>Matrix helm chart app in Argo CD</summary>

  <a href="../../assets/images/screenshots/matrix-web-app.png">
    <img src="../../assets/images/screenshots/matrix-web-app.png" alt="screenshot of the Argo CD web interface showing the matrix web app helm chart app in tree view mode.">
  </a>

</details>

<details>
  <summary>Matrix networking view in Argo CD</summary>

  <a href="../../assets/images/screenshots/matrix-networking.png">
    <img src="../../assets/images/screenshots/matrix-networking.png" alt="screenshot of the Argo CD web interface showing the matrix web app in networking view mode. It shows a cloud on the left flowing into a box that says 192.168.168.168 which branches off into three ingress resources: matrix stack element, matrix stack synapse, and matrix stack synapse federation. The ingress resource for element, branches off into a service of the same name and then a pod of the same name. The synapse and synapse federation ingress resources branch off into two respective services that branch off into one shared pod called matrix stack synapse.">
  </a>

</details>


!!! Note
    We recently added support for [sliding sync](https://github.com/) and [matrix authentication service](https://github.com/). To use these, please use `matrix/app_of_apps_beta/` for `apps.matrix.argo.path`.

## Required Values

### Appset secret values

The main variables you need to worry about when setting up matrix are your `hostname` variables:

- hostname
- element_hostname
- federation_hostname

**If using Matrix authentication Service and Sliding Sync**:

- auth_hostname
- sliding_sync_hostname

These are all storage related and you can leave them at the defaults for small servers:

**Signing key storage**:
- signing_key_pvc_enabled
- signing_key_storage
- signing_key_access_mode

**Media storage**:
- media_pvc_enabled
- media_storage
- media_access_mode

**Synapse config storage**:
- synapse_config_pvc_enabled
- synapse_config_storage
- synapse_config_access_mode

**S3 storage**:
- s3_provider
- s3_bucket
- s3_endpoint
- s3_pvc_capacity
- s3_region

You'll also need to provide an admin_email for users to contact someone if something goes wrong.

### Init Values

These are all one time values that you need to provide, related entirely to mail setup:

- smtp_user
- smtp_host
See below for providing smtp_password without putting it in plain text.

If you want to federate, you also need to provide:
- [trusted_key_servers](https://element-hq.github.io/synapse/latest/usage/configuration/config_documentation.html?highlight=trusted#trusted_key_servers)

You can provide a list of maps like this for trusted_key_servers:

```yaml
apps:
  matrix:
    init:
      values:
        - server_name: matrix.friend.com
          verify_keys:
            ed25519:auto: abcdefghijklmnopqrstuvwxyzabcdefghijklmopqr
```

The trusted_key_servers option currently displays in the TUI, but is not editable via the TUI yet. See: [#269](https://github.com/small-hack/smol-k8s-lab/issues/269)


#### Sensitive values

Sensitive values can be provided via environment variables using a `value_from` map on any value under `init.values` or `backups`. Example of providing the SMTP password:

```yaml
apps:
  matrix:
    init:
      values:
        smtp_password:
          value_from:
            env: MATRIX_SMTP_PASSWORD
```


#### Sensitive values before `v5.0.0`

`smol-k8s-lab` did not originally support the `value_from` map. If you're using a version *before `v5.0.0`*, to avoid having to provide sensitive values every time you run `smol-k8s-lab` with matrix enabled, set up the following environment variables:

- `MATRIX_SMTP_PASSWORD`
- `MATRIX_S3_BACKUP_ACCESS_ID`
- `MATRIX_S3_BACKUP_SECRET_KEY`
- `MATRIX_RESTIC_REPO_PASSWORD`

## Backups

Backups are a new feature in `v5.0.0` that enable backing up your cluster via restic to a configurable remote S3 bucket. If you have `init.enabled` set to `true` and you're using our pre-configured `argo.repo`, we support both instant backups, and scheduled backups.

When running a backup of any kind, we will first initiate a [Cloud Native Postgresql backup](https://cloudnative-pg.io/documentation/1.23/backup/#on-demand-backups) to your local seaweedfs cluster that we setup for you, and then wait until the last wal archive associated with that backup is complete. After that, we start a k8up backup job to backup all of your important PVCs to your configured s3 bucket.

To use the backups feature, you'll need to configure the values below.

```yaml
apps:
  matrix:
    backups:
      # cronjob syntax schedule to run matrix pvc backups. This example shows PVC Backups
      # happening at 12:10 AM.
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for matrix postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the backup shows as completed before
      # it actually is. This example shows postgres backups happening at exactly midnight
      postgres_schedule: 0 0 0 * * *
      s3:
        endpoint: s3.eu-central-003.backblazeb2.com
        bucket: my-matrix-backup-bucket
        region: eu-central-003
        secret_access_key:
          value_from:
            env: MATRIX_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: MATRIX_S3_BACKUP_ACCESS_ID
      # restic requires this for encrypting your backups in the remote bucket
      restic_repo_password:
        value_from:
          env: MATRIX_RESTIC_REPO_PASSWORD
```

## Restores

Restores are a new feature in `v5.0.0` that enable restoring your postgres cluster and PVCs via restic from a configurable remote S3 bucket. If you have `init.enabled` set to `true` and you're using our pre-configured `argo.repo`, we support restoring both your postgres cluster and PVCs. A restore is a kind of initialization process, so it lives under the `init` section of the config for your application, in this case, matrix. Here's an example:

```yaml
apps:
  matrix:
    enabled: false
    init:
      enabled: true
      restore:
        enabled: true
        # this must be set to true to restore your postgres cluster
        cnpg_restore: true
        # all of these default to latest, but you can set them to any restic snapshot ID
        restic_snapshot_ids:
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          matrix_media: latest
          matrix_synapse_config: latest
          matrix_signing_key: latest
```

The restore process will put your secrets into place, then restore your seaweedfs cluster first, followed by your postgresql cluster, followed by your matrix your PVCs, and then it will install your matrix argocd app as normal.


## Full Example config

```yaml
apps:
  matrix:
    description: |
      [link=https://matrix.org/]Matrix[/link] is an open protocol for decentralised, secure communications.
      This deploys a matrix synapse server, element (web frontend), and turn server (voice)

      smol-k8s-lab supports initialization by creating initial secrets for your:
        - matrix, element, and federation hostnames,
        - credentials for: postgresql, admin user, S3 storage, and SMTP

      smol-k8s-lab also sets up an OIDC application via Zitadel.

      To provide sensitive values via environment variables to smol-k8s-lab use a value_from map in the config.yaml
    enabled: false
    init:
      enabled: true
      restore:
        enabled: false
        cnpg_restore: true
        restic_snapshot_ids:
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          matrix_media: latest
          matrix_synapse_config: latest
          matrix_signing_key: latest
      values:
        smtp_user: change me to enable mail
        smtp_host: enable.mail
        smtp_password:
          value_from:
            env: MATRIX_SMTP_PASSWORD
    backups:
      # cronjob syntax schedule to run matrix pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for matrix postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the backup shows as completed before
      # it actually is
      postgres_schedule: 0 0 0 * * *
      s3:
        endpoint: s3.eu-central-003.backblazeb2.com
        bucket: my-matrix-backup-bucket
        region: eu-central-003
        secret_access_key:
          value_from:
            env: MATRIX_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: MATRIX_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: MATRIX_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # hostname of the synapse matrix server
        hostname: "chat.beepboopfordogsnoots.city"
        # the hostname of the element web interface
        element_hostname: 'element.beepboopfordogsnoots.city'
        # hostname for federation, that others can see you on the fediverse
        federation_hostname: 'chat-federation.beepboopfordogsnoots.city'
        # email for of the admin user
        admin_email: 'notadog@coolcats.com'
        # list of admin users for bridges, the hostnames will be appended automatically
        admin_users:
          - notadog
          - realcat
        # enable signing key backups
        signing_key_pvc_enabled: 'true'
        # size of signing key pvc storage
        signing_key_storage: 1Mi
        signing_key_access_mode: ReadWriteOnce
        # enable persistent volume claim for matrix media storage
        media_pvc_enabled: 'true'
        # size of media pvc storage
        media_storage: 20Gi
        media_access_mode: ReadWriteOnce
        # enable persistent volume claim for matrix synapse config storage
        synapse_config_pvc_enabled: 'true'
        # size of synapse config pvc storage
        synapse_config_storage: 2Mi
        synapse_config_access_mode: ReadWriteOnce
        # choose S3 as the local primary object store from either: seaweedfs, or minio
        # SeaweedFS - deploy SeaweedFS filer/s3 gateway
        # MinIO     - deploy MinIO vanilla helm chart
        s3_provider: seaweedfs
        # local s3 provider bucket name
        s3_bucket: matrix
        # the endpoint you'd like to use for your minio or SeaweedFS instance
        s3_endpoint: matrix-s3.social-media-for-dogs.com
        # how large the backing pvc's capacity should be for minio or seaweedfs
        s3_pvc_capacity: 100Gi
        s3_region: eu-west-1
      # git repo to install the Argo CD app from
      repo: "https://github.com/small-hack/argocd-apps"
      # path in the argo repo to point to. Trailing slash very important!
      path: "matrix/app_of_apps/"
      # either the branch or tag to point at in the argo repo above
      revision: "main"
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: "matrix"
      # recurse directories in the git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: matrix
        source_repos:
          - https://small-hack.github.io/cloudnative-pg-cluster-chart
          - https://small-hack.github.io/matrix-chart
          - https://operator.min.io/
          - https://seaweedfs.github.io/seaweedfs/helm
        destination:
          namespaces:
            - argocd
```

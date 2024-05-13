[Matrix](https://matrix.org/) is an open protocol for decentralised, secure communications.

`smol-k8s-lab` deploys a matrix synapse server, element (a web frontend), and a turn server (voice server).

<a href="../../assets/images/screenshots/matrix_screenshot.png">
<img src="../../assets/images/screenshots/matrix_screenshot.png" alt="screenshot of the Argo CD web interface showing the matrix app of apps in tree view mode, which shows the following children: persistence app, external secrets appset, postgres appset, s3 provider appset, s3 pvc app set, and matrix web app set.">
</a>

The main variable you need to worry about when setting up matrix is your `hostname`.

## Sensitive values

To avoid having to provide sensitive values every time you run smol-k8s-lab with matrix enabled, provide the following via environment variables:

- `MATRIX_SMTP_PASSWORD`
- `MATRIX_S3_BACKUP_ACCESS_ID`
- `MATRIX_S3_BACKUP_SECRET_KEY`
- `MATRIX_RESTIC_REPO_PASSWORD`

## Example config

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

      To provide sensitive values via environment variables to smol-k8s-lab use:
        - MATRIX_SMTP_PASSWORD
        - MATRIX_S3_BACKUP_ACCESS_ID
        - MATRIX_S3_BACKUP_SECRET_KEY
        - MATRIX_RESTIC_REPO_PASSWORD
    enabled: false
    init:
      enabled: true
      restore:
        enabled: false
        cnpg_restore: true
        restic_snapshot_ids:
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          seaweedfs_master: latest
          matrix_media: latest
          matrix_synapse_config: latest
          matrix_signing_key: latest
      values:
        smtp_user: change me to enable mail
        smtp_host: enable.mail
        smtp_password:
          valueFrom:
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
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: s3.eu-central-003.backblazeb2.com
        bucket: my-matrix-backup-bucket
        region: eu-central-003
        secret_access_key:
          valueFrom:
            env: MATRIX_S3_BACKUP_SECRET_KEY
        access_key_id:
          valueFrom:
            env: MATRIX_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        valueFrom:
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
        s3_endpoint: matrix-s3.vleermuis.tech
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

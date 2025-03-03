[Harbor](https://goharbor.io/) is a self hosted OCI registry and includes plugins for security scanning. You can use it for anything that can be built as an OCI e.g. docker, helm, and python. From their website:

> Harbor is an open source trusted cloud native registry project that stores, signs, and scans content. Harbor extends the open source Docker Distribution by adding the functionalities usually required by users such as security, identity and management. Having a registry closer to the build and run environment can improve the image transfer efficiency. Harbor supports replication of images between registries, and also offers advanced security features such as user management, access control and activity auditing.

We install the helm chart from [goharbor/harbor-helm](https://github.com/goharbor/harbor-helm) as part of an Argo CD ApplicationSet.

⚠️ *Harbor is an _experimental_ smol-k8s-lab app, so it may be unstable*

## Example configuration

```yaml
apps:
  harbor:
    description: |
      [magenta]⚠️ Experimental[/magenta]
      󰨀 [link=https://goharbor.io/]Harbor[/link] is an open source trusted cloud native registry project that stores, signs, and scans content. Harbor extends the open source Docker Distribution by adding the functionalities usually required by users such as security, identity and management. Having a registry closer to the build and run environment can improve the image transfer efficiency. Harbor supports replication of images between registries, and also offers advanced security features such as user management, access control and activity auditing.

       We install the helm chart from [link=https://github.com/goharbor/harbor-helm]github.com/goharbor/harbor-helm[/link].

       smol-k8s-lab supports initializing harbor, by setting up your hostname, valkey credentials, postgresql credentials, and an admin user credentials. We pass all credentials as Secrets in the namespace and optionally save them to Bitwarden.

       smol-k8s-lab also creates a local s3 endpoint and as well as S3 bucket and credentials if you enable set harbor.argo.secret_keys.s3_provider to "minio" or "seaweedfs". Both seaweedfs and minio require you to specify a remote s3 endpoint, bucket, region, and accessID/secretKey so that we can make sure you have remote backups.

       To provide sensitive values via environment variables to smol-k8s-lab use:
         - HARBOR_S3_BACKUP_ACCESS_ID
         - HARBOR_S3_BACKUP_SECRET_KEY
         - HARBOR_RESTIC_REPO_PASSWORD
    enabled: false
    init:
      enabled: true
      restore:
        enabled: false
        cnpg_restore: true
        restic_snapshot_ids:
          # seaweedfs_master: latest
          seaweedfs_volume: latest
          seaweedfs_filer: latest
          harbor_valkey_primary: latest
          harbor_valkey_replica: latest
      values:
        # admin user
        admin_user: "admin"
        # admin user's email
        admin_email: ""
    backups:
      # cronjob syntax schedule to run harbor pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for harbor postgres backups
      # must happen at least 10 minutes before pvc backups, to avoid corruption
      # due to missing files. This is because the backup shows as completed before
      # it actually is
      postgres_schedule: 0 0 0 * * *
      s3:
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: ""
        bucket: ""
        region: ""
        secret_access_key:
          value_from:
            env: HARBOR_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: HARBOR_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: HARBOR_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # you can delete these if you're not using tolerations/affinity
        toleration_key: ""
        toleration_operator: ""
        toleration_value: ""
        toleration_effect: ""
        # these are for node affinity, delete if not in use
        affinity_key: ""
        affinity_value: ""
        # admin user for your harbor instance
        admin_user: admin
        # hostname that users go to in the browser
        hostname: ""
        # set the local s3 provider for harbor's public data in one bucket
        # and private database backups in another. can be minio or seaweedfs
        s3_provider: seaweedfs
        # how large the backing pvc's capacity should be for minio or seaweedfs
        s3_pvc_capacity: 120Gi
        # local s3 endpoint for postgresql backups, backed up constantly
        s3_endpoint: ""
        s3_region: eu-west-1
        # enable persistence for valkey - recommended
        valkey_pvc_enabled: 'true'
        # size of valkey pvc storage
        valkey_storage: 3Gi
        valkey_storage_class: local-path
        valkey_access_mode: ReadWriteOnce
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: demo/harbor/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: harbor
      # recurse directories in the git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: harbor
        # depending on if you use seaweedfs or minio, you can remove the other source repo
        source_repos:
          - registry-1.docker.io
          - https://small-hack.github.io/cloudnative-pg-cluster-chart
          - https://operator.min.io/
          - https://seaweedfs.github.io/seaweedfs/helm
          - https://helm.goharbor.io
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

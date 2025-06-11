[writefreely](https://writefreely.org/) is a slim blogging platform.

This is an *Experimental* app.

# Example config

```yaml
apps:
  writefreely:
    description: |
       [magenta]⚠️ Experimental[/magenta]
       [link=https://writefreely.org/]writefreely[/link] is a slim open source blogging platform.

       To provide sensitive values via environment variables to smol-k8s-lab use:
         - WRITEFREELY_SMTP_PASSWORD
         - WRITEFREELY_S3_BACKUP_SECRET_KEY
         - WRITEFREELY_S3_BACKUP_ACCESS_ID
         - WRITEFREELY_RESTIC_REPO_PASSWORD
    enabled: false
    init:
      enabled: false
      values:
        smtp_password:
          value_from:
            env: WRITEFREELY_SMTP_PASSWORD
    backups:
      # cronjob syntax schedule to run writefreely pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for writefreely postgres backups
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
            env: WRITEFREELY_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: WRITEFREELY_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: WRITEFREELY_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        ## you can delete these if you're not using tolerations/affinity
        # toleration_key: ""
        # toleration_operator: ""
        # toleration_value: ""
        # toleration_effect: ""
        ## these are for node affinity, delete if not in use
        # affinity_key: ""
        # affinity_value: ""
        # hostname that users go to in the browser
        hostname: ""
        # admin username
        admin_user: "writefreely"
        # admin email
        admin_email: ""
        # title of your title
        blog_title: ""
        # smtp server
        smtp_host: ""
        # smtp port
        smtp_port: ""
        # smtp username
        smtp_user: ""
        # writefreely mysql pvc capacity
        mysql_pvc_capacity: 5Gi
        # writefreely pvc capacity
        pvc_capacity: 10Gi
        # set the local s3 provider for writefreely's public data in one bucket
        # and private database backups in another. can be seaweedfs for now
        s3_provider: seaweedfs
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: writefreely/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: writefreely
      # recurse directories in the git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: writefreely
        # depending on if you use seaweedfs or minio, you can remove the other source repo
        source_repos:
          - registry-1.docker.io
          - seaweedfs.github.io/seaweedfs/helm
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

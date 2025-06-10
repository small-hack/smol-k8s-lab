[Forgejo](https://forgejo.org/) is an open source self hosted git server and frontend.

⚠️ *forgejo is an _experimental_ smol-k8s-lab app, so it may be unstable*

## Example configuration

```yaml
apps:
  forgejo:
    description: |
       [magenta]⚠️ Experimental[/magenta]
       [link=https://forgejo.org/]forgejo[/link] is an open source self hosted git server and frontend.

       To provide sensitive values via environment variables to smol-k8s-lab use:
          - FORGEJO_S3_BACKUP_SECRET_KEY
          - FORGEJO_S3_BACKUP_ACCESS_ID
          - FORGEJO_RESTIC_REPO_PASSWORD
    enabled: false
    init:
      enabled: false
    backups:
      # cronjob syntax schedule to run forgejo pvc backups
      pvc_schedule: 10 0 * * *
      # cronjob syntax (with SECONDS field) for forgejo postgres backups
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
            env: FORGEJO_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: FORGEJO_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: FORGEJO_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # hostname that users go to in the browser
        hostname: ""
        ## you can delete these if you're not using tolerations/affinity
        # toleration_key: ""
        # toleration_operator: ""
        # toleration_value: ""
        # toleration_effect: ""
        ## these are for node affinity, delete if not in use
        # affinity_key: ""
        # affinity_value: ""
        pvc_capacity: 10Gi
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: forgejo/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: forgejo
      # recurse directories in the git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: forgejo
        # depending on if you use seaweedfs or minio, you can remove the other source repo
        source_repos:
          - code.forgejo.org
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

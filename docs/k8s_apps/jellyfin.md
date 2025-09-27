[Jellyfin](https://jellyfin.com/opensource) is a home media server. We're using the [jellyfin/jellyfin-helm](https://github.com/jellyfin/jellyfin-helm) helm chart.

**Tip**: Once you've got everything up and running, consider downloading some of Blender Studio's fantastic [Creative Commons licensed open source films](https://download.blender.org/demo/movies/).

## Example configs

```yaml
apps:
  jellyfin:
    enabled: true
    description: |
      [link=https://jellyfin.com/opensource]jellyfin[/link] is an open source self media hosting platform that replaces something like emby or plex.

      Once you've got everything up and running, consider downloading some of Blender Studio's fantastic Creative Commons licensed open source films:
      [link=https://download.blender.org/demo/movies/]download.blender.org/demo/movies/[/link]
    init:
      # Switch to false if you don't want to create intial secrets or use the
      # API via a service acocunt to create the above described resources
      enabled: true
      restore:
        enabled: false
        restic_snapshot_ids:
          media: latest
          config: latest
    backups:
      # cronjob syntax schedule to run jellyfin seaweedfs pvc backups
      pvc_schedule: 10 0 * * *
      s3:
        # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
        endpoint: example
        bucket: example
        region: auto
        # secret_access_key:
        #   value_from:
        #     env: JELLYFIN_S3_BACKUP_SECRET_KEY
        # access_key_id:
        #   value_from:
        #     env: JELLYFIN_S3_BACKUP_ACCESS_ID
      # restic_repo_password:
      #   value_from:
      #     env: JELLYFIN_RESTIC_REPO_PASSWORD
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # FQDN to use for jellyfin
        hostname: jelly.example.com
        # tolerations and affinity (important if you're not using networked storage)
        toleration_key: dedicated
        toleration_operator: Equal
        toleration_value: example
        toleration_effect: NoSchedule
        affinity_key: dedicated
        affinity_value: example
        # enable persistent volume claim for jellyfin media storage
        media_pvc_enabled: 'true'
        # size of media pvc storage
        media_storage: 250Gi
        media_storage_class: local-path
        media_access_mode: ReadWriteOnce
        # enable persistent volume claim for jellyfin config storage
        config_pvc_enabled: 'true'
        # size of config pvc storage
        config_storage: 2Gi
        config_access_mode: ReadWriteOnce
        config_storage_class: local-path
      # repo to install the Argo CD app from
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: jellyfin/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: jellyfin
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        source_repos:
          - https://jellyfin.github.io/jellyfin-helm
          - https://small-hack.github.io/cloudnative-pg-cluster-chart
          - https://operator.min.io/
          - https://seaweedfs.github.io/seaweedfs/helm
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
        name: jellyfin
```

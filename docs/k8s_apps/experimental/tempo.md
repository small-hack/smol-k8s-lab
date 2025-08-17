[Tempo](https://grafana.com/docs/tempo/latest/) is an open-source, easy-to-use, and high-scale distributed tracing backend. Tempo lets you search for traces, generate metrics from spans, and link your tracing data with logs and metrics. We're still experimenting with it here at small-hack, so feel free to grab anything you like, but understand that it is still in development.

## Experimental

```yaml
apps:
  tempo:
    description: |
      [magenta]⚠️ Experimental[/magenta]
      [link=https://grafana.com.com/oss/tempo]Tempo[/link]
    enabled: true
    init:
      # if init is enabled, we'll set up an app in Zitadel for using Oauth2 with Grafana
      enabled: true
      # restore:
      #   enabled: false
      #   restic_snapshot_ids:
      #     seaweedfs_volume: latest
      #     seaweedfs_filer: latest
    # backups:
    #   # cronjob syntax schedule to run forgejo pvc backups
    #   pvc_schedule: 10 0 * * *
    #   s3:
    #     # these are for pushing remote backups of your local s3 storage, for speed and cost optimization
    #     endpoint: ''
    #     bucket: ''
    #     region: ''
    #     secret_access_key:
    #       value_from:
    #         env: TEMPO_S3_BACKUP_SECRET_KEY
    #     access_key_id:
    #       value_from:
    #         env: TEMPO_S3_BACKUP_ACCESS_ID
    #   restic_repo_password:
    #     value_from:
    #       env: TEMPO_RESTIC_REPO_PASSWORD

    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      # toleration affinity
      # toleration_key: dedicated
      # toleration_operator: Equal
      # toleration_value: nextcloud
      # toleration_effect: NoSchedule
      # affinity_key: dedicated
      # affinity_value: nextcloud
      secret_keys: []
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to
      path: tempo/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: monitoring
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: monitoring
        source_repos:
        - registry-1.docker.io
        - ghcr.io/grafana/helm-charts
        - https://seaweedfs.github.io/seaweedfs/helm
        - https://tempo.github.io/helm-charts
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces: []
```

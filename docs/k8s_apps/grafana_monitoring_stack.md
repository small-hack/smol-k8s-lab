Together with [alloy](https://grafana.com/oss/alloy/), [mimir](https://grafana.com/oss/mimir/), and [loki](https://grafana.com/oss/loki/), we cover gathering metrics and logs as well as creating dashboards with [Grafana](https://grafana.com/). We even deploy [alert-manager](https://prometheus.io/docs/alerting/latest/alertmanager/) for you to create your own alerts.

You can see an overview of the whole Prometheus Stack Argo CD Application at [small-hack/argocd-apps:grafana_stack](https://github.com/small-hack/argocd-apps/tree/main/grafana_stack).

<a href="../../assets/images/screenshots/grafana_stack.png">
<img src="../../assets/images/screenshots/grafana_stack.png" alt="screenshot of the Argo CD web interface showing the grafana monitoring stack app of apps which includes the following children: loki, prometheus-crd, prometheus-appset">
</a>

| Application                                                               | Description                                         |
|---------------------------------------------------------------------------|-----------------------------------------------------|
| [Alloy](https://grafana.com.com/oss/mimir)                                | for collecting metrics and logs                     |
| [Mimir](https://grafana.com.com/oss/mimir/)                               | for aggregating metrics and storign them in S3      |
| [Loki](https://grafana.com/oss/loki/)                                     | for aggregating logs and storing them in S3         |
| [Alert Manager](https://prometheus.io/docs/alerting/latest/alertmanager/) | for sending alerts to matrix                        |
| [Grafana](https://grafana.com/oss/grafana/)                               | for querying metrics/logs and displaying dashboards |

## Important note

We haven't generated new screenshots, but we've updated how we now deploy the Prometheus CRDs. They are now deployed separately, so that anything that relies on them that gets deployed earlier on, such as your identity provider, which you may want to secure the prometheus related frontends.

## Example configs

### Custom Resource Definitions (CRDs)

```yaml
apps:
  prometheus_crds:
    description: |
      [link=https://prometheus.io/docs/introduction/overview/]Prometheus[/link] CRDs to start with.
      You can optionally disable this if you don't want to deploy apps with metrics.

    enabled: true
    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys: {}
      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important!
      path: prometheus/crds/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: prometheus
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: prometheus
        source_repos:
        - https://github.com/prometheus-community/helm-charts.git
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
          - kube-system
          - prometheus
```

### kube-prometheus-stack

**NOTE**: You need to *also* enable the CRD app above for this to work!

```yaml
apps:
  grafana_stack:
    description: |
      Full monitoring stack with:
       - [link=https://grafana.com.com/oss/mimir]Alloy[/link] - for collecting metrics and logs
       - [link=https://grafana.com.com/oss/mimir/]Mimir[/link] - for aggregating metrics and storign them in S3
       - [link=https://grafana.com/oss/loki/]Loki[/link] - for aggregating logs and storing them in S3
       - [link=https://prometheus.io/docs/alerting/latest/alertmanager/]Alert Manager[/link] - for sending alerts to matrix
       - [link=https://grafana.com/oss/grafana/]Grafana[/link] - for querying metrics/logs and displaying dashboards

      smol-k8s-lab supports initialization by setting up your ingress hostnames. It will also setup Oauth2 for Grafana directly by creating an app in Zitadel for you.

      For Alert Manager, we use vouch-proxy via Ingress resource annotations to forward users to Zitadel for auth, so the frontend is not insecure.
    enabled: false

    init:
      # if init is enabled, we'll set up an app in Zitadel for using Oauth2 with Grafana
      enabled: true

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
            env: GRAFANA_STACK_S3_BACKUP_SECRET_KEY
        access_key_id:
          value_from:
            env: GRAFANA_STACK_S3_BACKUP_ACCESS_ID
      restic_repo_password:
        value_from:
          env: GRAFANA_STACK_RESTIC_REPO_PASSWORD

    argo:
      # secrets keys to make available to Argo CD ApplicationSets
      secret_keys:
        # FQDN to use for Thanos web interface
        thanos_hostname: ""
        # FQDN to use for Grafana
        grafana_hostname: ""
        # FQDN to use for the Loki UI
        loki_hostname: ""
        # FQDN to use for Alert Manager web interface
        alert_manager_hostname: ""
        # set the local s3 provider for the loki/mimir S3 backups. can be minio or seaweedfs
        s3_provider: seaweedfs
        # local s3 endpoint for loki/mimir S3 backups, backed up constantly
        s3_endpoint: ""
        # capacity for the PVC backing your local s3 instance
        s3_pvc_capacity: 100Gi

      # git repo to install the Argo CD app from
      repo: https://github.com/small-hack/argocd-apps
      # path in the argo repo to point to. Trailing slash very important! This
      # is an app of apps. Change to "monitoring/kube-prometheus-stack/" to
      # only install kube-prometheus-stack (foregoing loki and push gateway)
      path: grafana_stack/app_of_apps/
      # either the branch or tag to point at in the argo repo above
      revision: main
      # kubernetes cluster to install the k8s app into, defaults to Argo CD default
      cluster: https://kubernetes.default.svc
      # namespace to install the k8s app in
      namespace: "monitoring"
      # recurse directories in the provided git repo
      directory_recursion: false
      # source repos for Argo CD App Project (in addition to argo.repo)
      project:
        name: monitoring
        source_repos:
          - "registry-1.docker.io"
          - "https://grafana.github.io/helm-charts"
          - "https://github.com/grafana/helm-charts.git"
          - "https://github.com/prometheus-community/helm-charts.git"
          - "https://prometheus-community.github.io/helm-charts"
        destination:
          # automatically includes the app's namespace and argocd's namespace
          namespaces:
            - kube-system
```

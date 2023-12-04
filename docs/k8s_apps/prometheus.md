[Prometheus](https://prometheus.io/docs/introduction/overview/) is the core of our optionally installed monitoring stack. Together with [Grafana](https://grafana.com/) and [loki](https://grafana.com/oss/loki/), we cover gathering metrics and logs as well as creating dashboards. We even deploy [alert-manager](https://prometheus.io/docs/alerting/latest/alertmanager/) for you to create your own alerts.

You can see an overview of the whole Prometheus Stack Argo CD Application at [small-hack/argocd-apps/prometheus](https://github.com/small-hack/argocd-apps/tree/main/prometheus).

<img src="/assets/images/screenshots/prometheus_screenshot.png" alt="screenshot of the Argo CD web interface showing the prometheus app of apps which includes the following children: loki, prometheus-crd, prometheus-appset, prometheus-pushgateway-appset">

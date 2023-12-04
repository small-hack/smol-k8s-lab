We use [cert-manager](https://cert-manager.io) to generate TLS certs for the web frontends of any apps we install. 

<img src="/assets/images/screenshots/certmanager_screenshot.png" alt="Argo CD web interface screenshot of cert manager in tree view mode showing cert-manager-helm-chart with three of its children. The screenshot does not show the entire Argo CD application because it contains well over 10 different roles and cluster roles and does not fit on one page, so instead we've chosen to show only the deployment children which are cert-manager, cert-manager-caininjector, and cert-manager-webhook each with their own replicasets and pods.">

By default, we install two cluster issuers:

- `letsencrypt-staging`
- `letsencrypt-prod`

All applications will use `letsencrypt-staging` by default, until you change this setting via the [TUI](/tui/apps_screen/#modifying-globally-available-templating-parameters-for-argo-cd-applicationsets) or [config file](/config_file/#globally-available-argo-cd-applicationset). We default to the staging server, because `letsencrypt-prod` has very tight rate limiting and when testing, as one does in a lab, you can easily exceed this, which can issue you a ban for at least a week.

## Troubleshooting

Follow the steps in the [cert-manager common error troubleshooting guide](https://cert-manager.io/docs/faq/acme/#common-errors)), you can also change the `letsencrypt-staging` value to `letsencrypt-prod` for any domains you own and can configure to point to your cluster via DNS.

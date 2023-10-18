We use the Bitwarden ESO Provider along side the [external-secrets-operator](/k8s_apps/external-secrets-operator.md) to pull secret data from your Bitwarden vault, into the cluster as [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/).

`smol-k8s-lab` stores any sensitive user specific data about applications in your Bitwarden vault. Some examples include admin credentials, database credentials, and OIDC credentials.

Head over to the [Bitarden ESO Provider helm chart](https://github.com/jessebot/bitwarden-eso-provider/) to learn more, and then see how it is configured at [small-hack/argocd-apps](https://github.com/small-hack/argocd-apps/blob/main/external-secrets-operator/bitwarden/bitwarden_argocd_app.yaml).

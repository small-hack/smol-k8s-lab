The [External Secrets Operator](https://external-secrets.io/latest/) (abbreviated as ESO) is a Kubernetes operator that integrates external secret management systems like AWS Secrets Manager, HashiCorp Vault, Google Secrets Manager, Azure Key Vault, IBM Cloud Secrets Manager, CyberArk Conjur and many more. The operator reads information from external APIs and automatically injects the values into a Kubernetes Secret.

The goal of External Secrets Operator is to synchronize secrets from external APIs into Kubernetes. ESO is a collection of custom API resources - ExternalSecret, SecretStore and ClusterSecretStore that provide a user-friendly abstraction for the external API that stores and manages the lifecycle of the secrets for you.

`smol-k8s-lab` default makes heavy use of ESO in conjunction with the [Bitwarden ESO Provider](/k8s_apps/bitwarden_eso_provider.md) to ensure no credentials or sensitive data is stored as plain text in our git repos or in any helm values we provide. We accomplish this goal by always biasing towards using Kubernetes Secrets as sources of truth for helm charts, and those secrets come from Bitwarden by default.

Check out our [ESO Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/external-secrets-operator).

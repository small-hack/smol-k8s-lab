[Kyverno](https://kyverno.io/) is a policy engine designed for Kubernetes. Policies are managed as Kubernetes resources and no new language is required to write policies. This allows using familiar tools such as kubectl, git, and kustomize to manage policies. Kyverno policies can validate, mutate, generate, and cleanup Kubernetes resources, and verify image signatures and artifacts to help secure the software supply chain. The Kyverno CLI can be used to test policies and validate resources as part of a CI/CD pipeline.

Kyverno is still in alpha status at `smol-k8s-lab`, but here's what we've got so far:

- [Kyverno Argo CD Application](https://github.com/small-hack/argocd-apps/tree/main/kyverno)

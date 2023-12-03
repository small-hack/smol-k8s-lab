Argo CD exclusively powers _most_ of the applications that `smol-k8s-lab` supports. It should be installed by default if you use the default configuration.

## Default Argo CD configuration

Argo CD is one of the most complex applications we deploy for you. We follow this procedure:

1. Install Argo CD first with helm using some bare minimum options that include setting up your initial admin password.
   The reason we set up a password for you instead of letting Argo CD generate it for you, is so that we can store it in your password manager for later use. 
2. Deploy the [appset-secret-plugin](https://github.com/small-hack/appset-secret-plugin).
3. Optionally deploy an OIDC provider ([Zitadel](/k8s_apps/zitadel.md))
4. Create an Argo CD Application for Argo to manage itself

The final Application will be sourced from [small-hack/argocd-apps/argocd](https://github.com/small-hack/argocd-apps/tree/main/argocd), which you can learn more about its readme.

<img src="/images/screenshots/argocd_screenshot.png" alt="screenshot of the Argo CD Application viewed through the Argo CD web interface in tree mode. It shows Argo CD as the parent application and then 3 child applications: appset-secret-plugin (an app), argocd-bitwarden-eso (an appset), and argocd-web-app-set (an appset).">


## ApplicationSets

We make heavy use of [Argo CD ApplicationSets](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/) in order to utilize [generators](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators/), specifically we use a [Plugin Generator](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators-Plugin/) called [appset-secret-plugin](https://github.com/small-hack/appset-secret-plugin) to store variables in Kubernetes Secrets that can be passed to Argo CD ApplicationSets. This is particularly useful for data such as a specific hostname or timezone for an application.

[K8up](https://k8up.io/) is a kubernetes app that utilizes [Restic](https://restic.net/) to create backups of persistent volume claims to object stores like S3, MinIO, and Backblaze B2.

`smol-k8s-lab` optionally installs k8up as one of it's supported kubernetes applications [argocd repo with k8up template](https://gitlab.com/small-hack/argocd-apps/blob/main/k8up)

My work with k8up spans across a couple of repos. On github, I setup [k8s-backups-tutorial](https://github.com/jessebot/k8s-backups-tutorial), and I've also contributed a tiny bit to k8up directly in the form of [minor commits](https://github.com/jessebot/argo-example#argocd) to help with Backblaze B2 support.


- [Nextcloud backup example](https://gitlab.com/vleermuis_tech/goobernetes/nextcloud/-/tree/main/deps/k8up_backups)

### API Docs

The full API docs are [here](https://doc.crds.dev/github.com/k8up-io/k8up@v2.3.0).

- [One time Backups](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Backup/v1@v2.3.0)
- [Scheduled Backups](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Schedule/v1@v2.3.0)
- [Restores](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Backup/v1@v2.3.0)

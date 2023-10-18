[K8up](https://k8up.io/) is a Kubernetes app that utilizes [Restic](https://restic.net/) to create backups of persistent volume claims to object stores like S3, MinIO, and Backblaze B2.

`smol-k8s-lab` optionally installs K8up as one of it's supported Kubernetes applications using [Argo CD repo with K8up template](https://gitlab.com/small-hack/argocd-apps/blob/main/k8up).

One of the most important template values we require for our default Argo CD ApplicationSet is `timezone`, which should be a timezone from the [TZ database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) (in the wikipedia list, you want the second column, TZ Identifier).


### API Docs

The full API docs are [here](https://doc.crds.dev/github.com/k8up-io/k8up@v2.3.0).

- [One time Backups](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Backup/v1@v2.3.0)
- [Scheduled Backups](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Schedule/v1@v2.3.0)
- [Restores](https://doc.crds.dev/github.com/k8up-io/k8up/k8up.io/Backup/v1@v2.3.0)

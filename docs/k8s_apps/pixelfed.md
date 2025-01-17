[pixelfed](https://joinpixelfed.org/) is a Free and Open Source social media networking platform based on [ActivityPub](https://www.w3.org/TR/activitypub/).

We are mostly stable for running pixelfed on Kubernetes. Check out our [pixelfed Argo CD ApplicationSet](https://github.com/small-hack/argocd-apps/tree/main/pixelfed/small-hack):

<a href="../../assets/images/screenshots/pixelfed_screenshot.png">
<img src="../../assets/images/screenshots/pixelfed_screenshot.png" alt="screenshot of the pixelfed applicationset in Argo CD's web interface using the tree mode view. the main pixelfed app has 6 child apps: pixelfed-valkey, pixelfed-app-set with child pixelfed-web-app, pixelfed-external-secrets-appset with child pixelfed-external-secrets, pixelfed-postgres-app-set with child pixelfed-postgres-cluster, pixelfed-s3-provider-app-set with child pixelfed-seaweedfs, and pixelfed-s3-pvc-appset with child pixelfed-s3-pvc.">
</a>

This is the networking view in Argo CD:

<a href="../../assets/images/screenshots/pixelfed_networking_screenshot.png">
<img src="../../assets/images/screenshots/pixelfed_networking_screenshot.png" alt="screenshot of the pixelfed applicationset in Argo CD's web interface using the networking tree mode view. it shows the flow of cloud to ip address to pixelfed-web-app ingress to two services pixelfed-web-app-streaming and pixelfed-web-app-web which each go to their respective pods. There's also additional services and pods outside of that flow. pods masotdon-web-app-media and masotdon-web-app-sidekiq have no children. 2 elastic search services have the same elastic search pod child. and then there's an additional 3 matching elastic search service and pod pairs">
</a>

## Required Init Values

To use the default `smol-k8s-lab` Argo CD Application, you'll need to provide one time init values for:

- `admin_user`
- `admin_email`
- `smtp_user`
- `smtp_host`
- `smtp_port`

## Required ApplicationSet Values

And you'll also need to provide the following values to be templated for your personal installation:

- `hostname` - the hostname for your web interface

## Required Sensitive Values

If you'd like to setup SMTP, we need a bit more sensitive data. This includes your SMTP password, S3 backup credentials, and restic repo password.

You have two options. You can:

- respond to a one-time prompt for these credentials (one-time _per cluster_)
- export an environment variable

### Environment Variables

You can export the following env vars and we'll use them for your sensitive data:

- `PIXELFED_SMTP_PASSWORD`
- `PIXELFED_S3_BACKUP_ACCESS_ID`
- `PIXELFED_S3_BACKUP_SECRET_KEY`
- `PIXELFED_RESTIC_REPO_PASSWORD`


# Example Config

```yaml
apps:
```

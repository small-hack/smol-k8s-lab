## Default Installed Applications
Version is the helm chart version, or manifest version. See the [Default Applications](/k8s_apps/argocd) tab for more info on each application.

|           Application           |                      Description                      | Initialization Supported |
|:-------------------------------:|:------------------------------------------------------|:------------------------:|
| [<img src="../assets/images/icons/metallb_icon.png" width="32px" alt="metallb logo, blue arrow pointing up, with small line on one leg of arrow to show balance">][metallb] <br /> [metallb] | Loadbalancer and IP Address pool manager for metal | ✅ |
| [<img src="../assets/images/icons/nginx.ico" width="32px" alt="nginx logo, white letter N with green background">][ingress-nginx] <br /> [ingress-nginx] | The ingress-nginx controller allows access to the cluster remotely, needed for web traffic | ❌ |
| [<img src="../assets/images/icons/cert-manager_icon.png" width="32px" alt="cert manager logo">][cert-manager] <br /> [cert-manager] | For SSL/TLS certificates | ✅ |
| [<img src="../assets/images/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD] <br /> [Argo CD] | Gitops - Continuous Deployment | ✅ |
| [<img src="../assets/images/icons/argo_icon.png" width="32" alt="argo CD logo, an organer squid wearing a fishbowl helmet">][Argo CD Appset Secret Plugin] <br /> [Argo CD Appset Secret Plugin] | Gitops - Continuous Deployment | ✅ |
| [<img src="../assets/images/icons/eso_icon.png" width="32" alt="ESO logo, outline of robot with astricks in a screen in it's belly">][ESO] <br /> [ESO] | external-secrets-operator integrates external secret management systems like Bitwarden or GitLab | ❌ |
| [<img src="../assets/images/icons/eso_icon.png" width="32" alt="ESO logo, again">][Bitwarden ESO Provider] <br /> [Bitwarden ESO Provider] | Bitwarden external-secrets-operator provider  | ✅ |
| [<img src="../assets/images/icons/zitadel.png" width="32" alt="Zitadel logo, an orange arrow pointing left">][ZITADEL] <br /> [ZITADEL] | An identity provider and OIDC provider to provide SSO | ✅ |
| [<img src="../assets/images/icons/vouch.png" width="32" alt="Vouch logo, the letter V in rainbow ">][Vouch] <br /> [Vouch] | Vouch proxy allows you to secure web pages that lack authentication e.g. prometheus | ✅ |
| [<img src="../assets/images/icons/prometheus.png" width="32" alt="Prometheus logo, a torch">][Prometheus Stack] <br /> [Prometheus Stack] | Prometheus monitoring and logging stack using [loki]/[promtail], [alert manager], and [grafana]  | ✅ |


Minor Notes:

>All Default Applications can be disabled through your `~/.config/smol-k8s-lab/config.yaml` file, **except** Argo CD. You can still choose not to install it, but if not installed, smol-k8s-lab will <i>only</i> install: metallb, nginx-ingress, and cert-manager</sub>


## Optionally Installed Applications

| Application/Tool | Description | Initialization Supported |
|:----------------:|:------------|:------------------------:|
| [<img src="../assets/images/icons/cilium.png"  width="32" alt="cilium logo">][Cilium] <br /> [Cilium]<sup>demo</sup> | Kubernetes netflow visualizer and policy editor | ✅ |
| [<img src="../assets/images/icons/gotosocial.png" width="32" alt="GoToSocial logo, a cute little sloth smiling">][GoToSocial] <br /> [GoToSocial] | GoToSocial is a self hosted federated social media site, that is slimmer than Mastodon.  | ✅ |
| [<img src="../assets/images/icons/home_assistant_icon.png"  width="32" alt="home assistant logo, which is a small blue house with three white tracers inside of it, making it appear as though the home is a circuit board">][Home Assistant] <br /> [Home Assistant] | Home Assistant, a self hosted, at home IoT management solution. | ✅ |
| [<img src="../assets/images/icons/kyverno_icon.png"  width="32" alt="kyvero logo">][Kyverno] <br /> [Kyverno]<sup>alpha</sup> | Kubernetes native policy management to enforce policies on k8s resources | ❌ |
| [<img src="../assets/images/icons/kepler.png" width="32" alt="kepler logo">][kepler] <br /> [kepler] | Kepler (Kubernetes Efficient Power Level Exporter) uses eBPF to probe energy-related system stats and exports them as Prometheus metrics. | ✅ |
| [<img src="../assets/images/icons/k8up.png" width="32" alt="k8up logo, a minimalist logo of a small blue hill with line starting the right going into the hill">][k8up] <br /> [k8up] | Backups operator using [restic] to backup to s3 endpoints | ✅ |
| [<img src="../assets/images/icons/k8tz.png" width="32" alt="k8tz logo, the k8s logo but with a watch in the center instead of the ship wheel">][k8tz] <br /> [k8tz] | Timezone environment variable injector for pods and cronjobs | ✅ |
| [<img src="../assets/images/icons/netmaker-icon.png" width="32" alt="netmaker logo, a purple letter N">][Netmaker] <br /> [Netmaker] | Netmaker is a self hosted vpn management tool | ✅ |
| [<img src="../assets/images/icons/nextcloud.png" width="32" alt="nextcloud logo, 3 white circles touching eachother on a blue background">][Nextcloud] <br /> [Nextcloud] | Nextcloud is a self hosted file server | ✅ |
| [<img src="../assets/images/icons/mastodon.png" width="32" alt="Mastodon logo, a white M in a purple chat bubble">][Mastodon] <br /> [Mastodon] | Mastodon is a self hosted federated social media site  | ✅ |
| [<img src="../assets/images/icons/matrix.png" width="32" alt="Matrix logo">][matrix] <br /> [matrix] | Matrix is a self hosted chat platform  | ✅ |
| [<img src="../assets/images/icons/minio.png" width="32" alt="minio logo, a minimalist drawing in red of a crane">][minio] <br /> [minio] | Self hosted S3 Object Store operator | ✅ |
| [<img src="../assets/images/icons/peertube.png" width="32" alt="peertube logo, 3 triangles stacked togehter like the triforce, the top is black, the bottom left is gray, and the bottom right is orange. It's tilted on it's side and the space in the center is white">][PeerTube] <br /> [PeerTube] | Self hosted video hosting site, much like YouTube, but federated and FOSS | ✅ |
| [<img src="../assets/images/icons/seaweedfs.png" width="32" alt="seaweedfs logo, ">][seaweedfs] <br /> [seaweedfs] | Self hosted S3 Object Store | ✅ |

There are plenty more on the side bar, and you can even add your own :)

<!-- k8s apps link references -->
[Local Path Provisioner]: https://github.com/rancher/local-path-provisioner
[nginx-ingress]: https://github.io/kubernetes/ingress-nginx

<!-- k8s distro link references -->
[k3s]: https://k3s.io/
[k3d]: https://k3d.io/
[KinD]: https://kind.sigs.k8s.io/

<!-- k8s optional apps link references -->
[ESO]: https://external-secrets.io
[alert manager]: https://prometheus.io/docs/alerting/latest/alertmanager/
[Argo CD]:https://argo-cd.readthedocs.io/en/latest/
[Argo CD Appset Secret Plugin]: https://github.com/small-hack/argocd-appset-secret-plugin/

[cert-manager]: https://cert-manager.io/docs/
[cilium]: https://github.com/cilium/cilium/tree/main/install/kubernetes/cilium
[Bitwarden ESO Provider]: https://github.com/small-hack/bitwarden-eso-provider
[grafana]: https://grafana.com/
[GoToSocial]: https://gotosocial.org/
[ingress-nginx]: https://github.io/kubernetes/ingress-nginx
[Home Assistant]: https://www.home-assistant.io/
[k8tz]: https://github.com/small-hack/argocd-apps/tree/main/alpha/k8tz
[k8up]: https://k8up.io
[Kyverno]: https://github.com/kyverno/kyverno/
[kepler]: https://github.com/sustainable-computing-io/kepler-helm-chart/tree/main/chart/kepler
[Local Path Provisioner]: https://github.com/rancher/local-path-provisioner
[loki]: https://grafana.com/oss/loki/
[Mastodon]: https://joinmastodon.org/
[matrix]: https://matrix.org/
[metallb]: https://github.io/metallb/metallb "metallb"
[minio]: https://min.io/
[PeerTube]: https://joinpeertube.org/
[Nextcloud]: https://github.com/nextcloud/helm
[Netmaker]: https://netmaker.io
[Prometheus Stack]: https://github.com/small-hack/argocd-apps/tree/main/prometheus
[promtail]: https://grafana.com/docs/loki/latest/send-data/promtail/
[seaweedfs]: https://github.com/seaweedfs/seaweedfs
[Vouch]: https://github.com/small-hack/vouch-helm-chart
[ZITADEL]: https://github.com/zitadel/zitadel-charts/tree/main

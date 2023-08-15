from ..pretty_printing.console_logging import header, sub_header
from ..k8s_tools.homelabHelm import prepare_helm
from ..k8s_tools.k8s_lib import K8s


def install_base_apps(k8s_obj: K8s, k8s_distro: str = "",
                      metallb_enabled: bool = True, argo_enabled: bool = False,
                      argo_secrets_enabled: bool = False, email: str = "",
                      cidr: str = "") -> bool:
    """ 
    Helm installs all base apps:
        metallb, ingess-nginx, and cert-manager.
    All Needed for getting Argo CD up and running.
    """
    # make sure helm is installed and the repos are up to date
    prepare_helm(k8s_distro, metallb_enabled, argo_enabled, 
                 argo_secrets_enabled)

    # needed for metal (non-cloud provider) installs
    if metallb_enabled:
        header("Installing [b]metallb[/b] so we have an IP address pool.")
        from ..k8s_apps.metallb import configure_metallb
        configure_metallb(cidr)

    # ingress controller: so we can accept traffic from outside the cluster
    header("Installing [b]ingress-nginx-controller[/b]...")
    from ..k8s_apps.nginx_ingress_controller import configure_ingress_nginx
    configure_ingress_nginx(k8s_distro)

    # manager SSL/TLS certificates via lets-encrypt
    header("Installing [b]cert-manager[/b] for TLS certificates...")
    from ..k8s_apps.cert_manager import configure_cert_manager
    configure_cert_manager(k8s_obj, email)

    # success!
    return True

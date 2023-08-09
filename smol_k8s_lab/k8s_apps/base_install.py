from .console_logging import header, sub_header

def install_k8s_distro(k8s_distro="", extra_args=[]):
    """
    Install a specific distro of k8s
    Takes one variable:
        k8s_distro - string. options: 'k0s', 'k3s', or 'kind'
    Returns True
    """
    header(f'Installing [green]{k8s_distro}[/] cluster.')
    sub_header('This could take a min ʕ•́ _ ̫•̀ʔっ♡ ', False)

    if k8s_distro == "kind":
        from .k8s_distros.kind import install_kind_cluster
        install_kind_cluster()
    elif k8s_distro == "k3s":
        from .k8s_distros.k3s import install_k3s_cluster
        install_k3s_cluster(extra_args)
    elif k8s_distro == "k0s":
        from .k8s_distros.k0s import install_k0s_cluster
        install_k0s_cluster()
    return True


def install_base_apps(k8s_distro="", metallb_enabled=True, argo_enabled=False,
                      argo_secrets_enabled=False, email="", cidr=""):
    """ 
    Helm installs all base apps:
        metallb, ingess-nginx, and cert-manager.
    All Needed for getting Argo CD up and running.
    """
    # make sure helm is installed and the repos are up to date
    from .k8s_tools.homelabHelm import prepare_helm
    prepare_helm(k8s_distro, metallb_enabled, argo_enabled, 
                 argo_secrets_enabled)

    # needed for metal (non-cloud provider) installs
    if metallb_enabled:
        header("Installing [b]metallb[/b] so we have an IP address pool.")
        from .k8s_apps.metallb import configure_metallb
        configure_metallb(cidr)

    # ingress controller: so we can accept traffic from outside the cluster
    header("Installing [b]ingress-nginx-controller[/b]...")
    from .k8s_apps.nginx_ingress_controller import configure_ingress_nginx
    configure_ingress_nginx(k8s_distro)

    # manager SSL/TLS certificates via lets-encrypt
    header("Installing [b]cert-manager[/b] for TLS certificates...")
    from .k8s_apps.cert_manager import configure_cert_manager
    configure_cert_manager(email)

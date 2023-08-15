from ..pretty_printing.console_logging import sub_header, header
from ..subproc import subproc


def create_k8s_distro(k8s_distro: str = "", metallb_enabled: bool = True,
                       extra_args: list = []):
    """
    Install a specific distro of k8s
    Takes one variable:
        k8s_distro - string. options: 'k0s', 'k3s', 'k3d', or 'kind'
    Returns True
    """
    cmd = "kubectl config get-clusters"
    clusters = subproc([cmd], error_ok=True, quiet=True)
    if f'smol-k8s-lab-{k8s_distro}' in clusters:
        sub_header(f'We already have a {k8s_distro} cluster ♡')
        return True

    header(f'Creating a [green]{k8s_distro}[/] cluster.')
    sub_header('This could take a min ʕ•́ _ ̫•̀ʔっ♡ ', False)

    if k8s_distro == "kind":
        from .kind import install_kind_cluster
        install_kind_cluster()
    elif k8s_distro == "k3s":
        from .k3s import install_k3s_cluster
        install_k3s_cluster(metallb_enabled, extra_args)
    # curently unsupported - in alpha state
    elif k8s_distro == "k3d":
        from .k3d import install_k3d_cluster
        install_k3d_cluster()
    elif k8s_distro == "k0s":
        from .k0s import install_k0s_cluster
        install_k0s_cluster()
    return True


def delete_cluster(k8s_distros=["kind"]):
    """
    Delete a k0s, k3s, or KinD cluster entirely.
    It is suggested to perform a reboot after deleting a k0s cluster.
    """
    for k8s_distro in k8s_distros:
        if k8s_distro == 'k3s':
            from .k8s_distros.k3s import uninstall_k3s
            uninstall_k3s()

        elif k8s_distro == 'kind':
            from .k8s_distros.kind import delete_kind_cluster
            delete_kind_cluster()

        elif k8s_distro == 'k0s':
            from .k8s_distros.k0s import uninstall_k0s
            uninstall_k0s()

        else:
            header(f"┌（・o・）┘≡З  Whoops. {k8s_distro} not YET supported.")

    sub_header("[grn]◝(ᵔᵕᵔ)◜ Success![/grn]")

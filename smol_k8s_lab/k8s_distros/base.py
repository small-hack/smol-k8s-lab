import logging as log
from ..pretty_printing.console_logging import sub_header, header
from ..subproc import subproc


def check_contexts(k8s_distro: str = ""):
    """
    gets current context and if any have have smol-k8s-lab-{distro} returns and
    dict of {"context": context_name, "cluster": cluster_name, "user": auto_info}
    returns False if there's no clusters with smol-k8s-lab-{distro} as the context
    """
    cmd = "kubectl config get-contexts --no-headers"
    contexts = subproc([cmd], error_ok=True, quiet=True)
    log.debug(contexts)
    if contexts:
        for k8s_context in contexts.split('\n'):
            fields = k8s_context.split()
            if f'smol-k8s-lab-{k8s_distro}' in k8s_context:
                log.debug(f"fields is {fields}")
                if len(fields) == 5:
                    return_dict = {"context": fields[1], "cluster": fields[2],
                                   "user": fields[3]}
                    log.debug(f"return_dict is {return_dict}")
                    return return_dict
                elif len(fields) == 4:
                    return_dict = {"context": fields[0], "cluster": fields[1],
                                   "user": fields[2]}
                    log.debug(f"return_dict is {return_dict}")
                    return return_dict
    return False


def create_k8s_distro(k8s_distro: str = "", metallb_enabled: bool = True,
                       extra_args: list = []):
    """
    Install a specific distro of k8s
    Takes one variable:
        k8s_distro - string. options: 'k0s', 'k3s', 'k3d', or 'kind'
    Returns True
    """
    header(f"Initializing your [green]{k8s_distro}[/] cluster")
    contexts = check_contexts(k8s_distro)
    if contexts:
        sub_header(f'We already have a [green]{k8s_distro}[/] cluster ♡')

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


def delete_cluster(k8s_distro: str = "kind"):
    """
    Delete a k0s, k3s, or KinD cluster entirely.
    It is suggested to perform a reboot after deleting a k0s cluster.
    """
    contexts = check_contexts(k8s_distro)
    log.info(contexts)

    if not contexts:
        return True

    if k8s_distro == 'k3s':
        from .k3s import uninstall_k3s
        uninstall_k3s(contexts)

    elif k8s_distro == 'kind':
        from .kind import delete_kind_cluster
        delete_kind_cluster()

    elif k8s_distro == 'k0s':
        from .k0s import uninstall_k0s
        uninstall_k0s()

    else:
        header(f"┌（・o・）┘≡З  Whoops. {k8s_distro} not YET supported.")

    sub_header("[grn]◝(ᵔᵕᵔ)◜ Success![/grn]")

import logging as log
from .kind import install_kind_cluster, delete_kind_cluster
from .k3d import install_k3d_cluster, uninstall_k3d_cluster
from .k3s import install_k3s_cluster, uninstall_k3s
from ..utils.rich_cli.console_logging import sub_header, header
from ..utils.subproc import subproc


def check_contexts(k8s_distro: str):
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


def create_k8s_distro(k8s_distro: str,
                      distro_metadata: dict = {},
                      metallb_enabled: bool = True,
                      cilium_enabled: bool = False) -> True:
    """
    Install a specific distro of k8s
    Arguments:
        k8s_distro:       options: 'k3s', 'k3d', 'kind'
        distro_metadata:  any extra data objects to be passed to the install funcs
        metallb_enabled:  if we're enabling metallb it requires we disable
                          servicelb for k3s
        cilium_enabled:   if we're enabling cilium it requires we disable flannel
                          for k3s and disable network-policy for all distros
    Returns True
    """
    header(f"Initializing your [green]{k8s_distro}[/] cluster", "💙")
    contexts = check_contexts(k8s_distro)
    if contexts:
        sub_header(f'We already have a [green]{k8s_distro}[/] cluster ♡')

    sub_header('This could take a min ʕ•́ _ •̀ʔっ♡ ', False)
    kubelet_args = distro_metadata.get('kubelet_extra_args', None)

    if k8s_distro == "kind":
        networking_args = distro_metadata['networking_args']

        # if cilium is enabled, we need to disable the default CNI
        if cilium_enabled:
            networking_args["disableDefaultCNI"] = True

        install_kind_cluster(kubelet_args,
                             networking_args,
                             distro_metadata['nodes']['control_plane'],
                             distro_metadata['nodes']['workers'])

    elif k8s_distro == "k3s" or k8s_distro == "k3d":
        # get any extra args the user has passed in
        k3s_args = distro_metadata['extra_k3s_cli_args']

        # if metallb is enabled, we need to disable servicelb
        if metallb_enabled:
            k3s_args.append('--disable=servicelb')

        # if cilium is enabled, we need to disable flannel and network-policy
        if cilium_enabled:
            k3s_args.extend(['--flannel-backend=none',
                             '--disable-network-policy'])

        if k8s_distro == "k3s":
            install_k3s_cluster(set(k3s_args),
                                kubelet_args,
                                distro_metadata['external_nodes'])

        # curently unsupported - in alpha state
        if k8s_distro == "k3d":
            install_k3d_cluster(k3s_args,
                                kubelet_args,
                                distro_metadata['nodes']['control_plane'],
                                distro_metadata['nodes']['workers'])
    return True


def delete_cluster(k8s_distro: str) -> True:
    """
    Delete a k3s, or KinD cluster entirely.
    """
    contexts = check_contexts(k8s_distro)
    log.info(contexts)

    if not contexts:
        return True

    if k8s_distro == 'k3s':
        uninstall_k3s(contexts)

    if k8s_distro == 'k3d':
        uninstall_k3d_cluster()

    elif k8s_distro == 'kind':
        delete_kind_cluster()

    else:
        # how did you even make it this far?
        header(f"┌（・o・）┘≡З  Whoops. {k8s_distro} not YET supported.")

    sub_header("[grn]◝(ᵔᵕᵔ)◜ Success![/grn]")
    return True

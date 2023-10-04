from .kind import install_kind_cluster, delete_kind_cluster
from .k3d import install_k3d_cluster, delete_k3d_cluster
from .k3s import install_k3s_cluster, uninstall_k3s
from ..utils.rich_cli.console_logging import sub_header, header
from ..utils.subproc import subproc


def check_all_contexts() -> list:
    """
    gets current context and if any have smol-k8s-lab returns and dict of 
    {"context": context_name, "cluster": cluster_name, "user": auto_info}

    returns False if there's no clusters with smol-k8s-lab as the context
    """
    contexts = subproc(["kubectl config get-contexts --no-headers"],
                       error_ok=True, quiet=True)

    return_contexts = []

    if contexts:
        # split all contexts outputs into a list of context lines
        for k8s_context in contexts.split('\n'):

            # split each context into fields
            fields = k8s_context.split()

            # HACK: I honestly have no clue why fields is empty sometimes &
            # don't have time to troubleshoot it either 🤦
            if fields:
                # set the cluster name, making sure to not get the * context
                if fields[0] and fields[0] != "*":
                    cluster_name = fields[0]
                else:
                    cluster_name = fields[1]

                # determine the distro of k8s we're using
                for distro_name in "kind", "k3d", "k3s", "gke", "aks", "eks":
                    if distro_name in cluster_name:
                        distro = distro_name
                        break

                context_tuple = (cluster_name, distro)

                return_contexts.append(context_tuple)

    return return_contexts


def check_contexts_for_distro(k8s_distro: str) -> dict:
    """
    gets current context and if any have smol-k8s-lab-{distro} returns and
    dict of {"context": context_name, "cluster": cluster_name, "user": auto_info}
    returns False if there's no clusters with smol-k8s-lab-{distro} as the context
    """
    contexts = subproc(["kubectl config get-contexts --no-headers"],
                       error_ok=True, quiet=True)

    if contexts:
        # split all contexts outputs into a list of context lines
        for k8s_context in contexts.split('\n'):
            # split each context into fields
            fields = k8s_context.split()

            # if smol-k8s-lab in 
            if f'smol-k8s-lab-{k8s_distro}' in k8s_context:
                # 5 fields if there's a * denoting the current context
                if len(fields) == 5:
                    return_dict = {"context": fields[1], "cluster": fields[2],
                                   "user": fields[3]}

                # 4 fields if there's no current context ie no cluster is selected
                elif len(fields) == 4:
                    return_dict = {"context": fields[0], "cluster": fields[1],
                                   "user": fields[2]}

                return return_dict
    return {}


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
    contexts = check_contexts_for_distro(k8s_distro)
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
            install_k3d_cluster(set(k3s_args),
                                kubelet_args,
                                distro_metadata['nodes']['control_plane'],
                                distro_metadata['nodes']['workers'])
    return True


def delete_cluster(k8s_distro: str) -> True:
    """
    Delete a k3s, or KinD cluster entirely.
    """
    contexts = check_contexts_for_distro(k8s_distro)

    if not contexts:
        return True

    if k8s_distro == 'k3s':
        uninstall_k3s(contexts)

    if k8s_distro == 'k3d':
        delete_k3d_cluster()

    elif k8s_distro == 'kind':
        delete_kind_cluster()

    else:
        # how did you even make it this far?
        header(f"┌（・o・）┘≡З  Whoops. {k8s_distro} not YET supported.")

    sub_header("[grn]◝(ᵔᵕᵔ)◜ Success![/grn]")
    return True

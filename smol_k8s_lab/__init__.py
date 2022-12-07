#!/usr/bin/env python3.11
"""
           NAME: smol-k8s-lab
    DESCRIPTION: Works with k3s and KinD
         AUTHOR: jessebot(AT)linux(d0t)com
        LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE
"""

import bcrypt
from click import option, argument, command, Choice
from collections import OrderedDict
import logging
from os import chmod, getenv, path, remove
from pathlib import Path
import requests

from rich.theme import Theme
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
import shutil
import stat
from sys import exit
from yaml import dump, safe_load
from .console_logging import simple_loading_bar, header, sub_header, print_panel
from .env_config import check_os_support, USR_CONFIG_FILE, VERSION
from .bw_cli import BwCLI
from .help_text import RichCommand, options_help
from .homelabHelm import helm
from .subproc import subproc


from smol_k8s_lab.console_logging import log


# this is for rich text, to pretty print things
soft_theme = Theme({"info": "dim cornflower_blue",
                    "warn": "yellow on black",
                    "danger": "bold magenta"})
CONSOLE = Console(theme=soft_theme)

PWD = path.dirname(__file__)
HOME_DIR = getenv("HOME")
HELP = options_help()
HELP_SETTINGS = dict(help_option_names=['-h', '--help'])


def setup_logger(level="", log_file=""):
    """
    Sets up rich logger and stores the values for it in a db for future import
    in other files. Returns logging.getLogger("rich")
    """
    # determine logging level
    if not level:
        if USR_CONFIG_FILE and 'log' in USR_CONFIG_FILE:
            level = USR_CONFIG_FILE['log']['level']
        else:
            level = 'info'

    log_level = getattr(logging, level.upper(), None)

    # these are params to be passed into logging.basicConfig
    opts = {'level': log_level, 'format': "%(message)s", 'datefmt': "[%X]"}

    # we only log to a file if one was passed into config.yaml or the cli
    if not log_file:
        if USR_CONFIG_FILE:
            log_file = USR_CONFIG_FILE['log'].get('file', None)

    # rich typically handles much of this but we don't use rich with files
    if log_file:
        opts['filename'] = log_file
        opts['format'] = "%(asctime)s %(levelname)s %(funcName)s: %(message)s"
    else:
        rich_handler_opts = {'rich_tracebacks': True}
        # 10 is the DEBUG logging level int value
        if log_level == 10:
            # log the name of the function if we're in debug mode :)
            opts['format'] = "[bold]%(funcName)s()[/bold]: %(message)s"
            rich_handler_opts['markup'] = True
        else:
            rich_handler_opts['show_path'] = False
            rich_handler_opts['show_level'] = False

        opts['handlers'] = [RichHandler(**rich_handler_opts)]

    # this uses the opts dictionary as parameters to logging.basicConfig()
    logging.basicConfig(**opts)

    if log_file:
        return None
    else:
        return logging.getLogger("rich")


def install_k8s_distro(k8s_distro=""):
    """
    install a specific distro of k8s
    options: k3s, kind
    """
    if k8s_distro == "kind":
        install_kind_cluster()
    elif k8s_distro == "k3s":
        install_k3s_cluster()


def install_k3s_cluster():
    """
    python installation for k3s, emulates curl -sfL https://get.k3s.io | sh -
    Notes: --flannel-backend=none will break k3s on metal
    """

    # download the k3s installer if we don't have it here already
    url = requests.get("https://get.k3s.io")
    k3s_installer_file = open("./install.sh", "wb")
    k3s_installer_file.write(url.content)
    k3s_installer_file.close()

    # make sure we can actually execute the script
    chmod("./install.sh", stat.S_IRWXU)

    # create the k3s cluster (just one server node)
    cmd = ('./install.sh --disable=servicelb --disable=traefik '
           '--write-kubeconfig-mode=647')
    subproc([cmd], spinner=False)

    # create the ~/.kube directory if it doesn't exist
    Path(f'{HOME_DIR}/.kube').mkdir(exist_ok=True)

    # Grab the kubeconfig and copy it locally
    cp = f'sudo cp /etc/rancher/k3s/k3s.yaml {HOME_DIR}/.kube/kubeconfig'

    # change the permissions os that it doesn't complain
    chmod_cmd = f'sudo chmod 644 {HOME_DIR}/.kube/kubeconfig'

    # run both commands one after the other
    subproc([cp, chmod_cmd])

    # remove the script after we're done
    remove('./install.sh')

    return


def install_kind_cluster():
    """
    python installation process for kind
    """
    # make sure kind is installed first, and if not, install it
    if not shutil.which("kind"):
        msg = ("ʕ•́ᴥ•̀ʔ [b]kind[/b] is [warn]not installed[/warn]. "
               "[i]We'll install it for you.[/i] ʕᵔᴥᵔʔ")
        CONSOLE.print(msg, justify='center')
        subproc(['brew install kind'])

    # then use our pre-configured kind file to install a small cluster
    full_path = path.join(PWD, 'distros/kind/kind_cluster_config.yaml')
    subproc([f"kind create cluster --config={full_path}"])
    return


def delete_cluster(k8s_distro="k3s"):
    """
    Delete a KIND or K3s cluster entirely.
    """
    header(f"Bye bye, [b]{k8s_distro}[/b]!")

    if k8s_distro == 'k3s':
        subproc(['k3s-uninstall.sh'], error_ok=True, spinner=False)

    elif k8s_distro == 'kind':
        subproc(['kind delete cluster'])

    else:
        header("┌（・o・）┘≡З  Whoops. {k8s_distro} not YET supported.")
    exit()


def add_default_repos(k8s_distro, argo=False, external_secrets=False,
                      kyverno=False):
    """
    Add all the default helm chart repos:
    - metallb is for loadbalancing and assigning ips, on metal...
    - ingress-nginx allows us to do ingress, so access outside the cluster
    - jetstack is for cert-manager for TLS certs
    - argo is argoCD to manage k8s resources in the future through a gui
    - kyverno is a k8s native policy manager
    """
    repos = OrderedDict()

    repos['metallb'] = 'https://metallb.github.io/metallb'
    repos['ingress-nginx'] = 'https://kubernetes.github.io/ingress-nginx'
    repos['jetstack'] = 'https://charts.jetstack.io'

    if external_secrets:
        repos['external-secrets'] = 'https://charts.external-secrets.io'

    if argo:
        repos['argo-cd'] = 'https://argoproj.github.io/argo-helm'

    if kyverno:
        repos['kyverno'] = 'https://kyverno.github.io/kyverno/'

    # kind has a special install path
    if k8s_distro == 'kind':
        repos.pop('ingress-nginx')

    # install and update any repos needed
    helm.repo(repos).add()
    return


def prepare_helm(k8s_distro="", argo=False, external_secrets=False,
                 kyverno=False):
    """
    get helm installed if needed, and then install/update all the helm repos
    """
    header("Adding/Updating helm repos...")
    if not shutil.which("helm"):
        msg = ("ʕ•́ᴥ•̀ʔ [b]Helm[/b] is [warn]not installed[/warn]. "
               "[i]We'll install it for you.[/i] ʕᵔᴥᵔʔ")
        CONSOLE.print(msg, justify='center')
        subproc(['brew install helm'])

    # this is where we add all the helm repos we're going to use
    add_default_repos(k8s_distro, argo, external_secrets, kyverno)
    return


def apply_custom_resources(custom_resource_dict_list):
    """
    Does a kube apply on a custom resource dict, and retries if it fails
    using loading bar for progress
    """
    k_cmd = 'kubectl apply --wait -f '
    commands = {}

    # Write a YAML representation of data to '/tmp/{resource_name}.yaml'.
    for custom_resource_dict in custom_resource_dict_list:
        resource_name = "_".join([custom_resource_dict['kind'],
                                  custom_resource_dict['metadata']['name']])
        yaml_file_name = f'/tmp/smol-k8s-lab/{resource_name}.yaml'
        with open(yaml_file_name, 'w') as cr_file:
            dump(custom_resource_dict, cr_file)
        commands[f'Installing {resource_name}'] = k_cmd + yaml_file_name

    # loops with progress bar until this succeeds
    simple_loading_bar(commands)


def apply_manifests(manifest_file_name="", namespace="default", deployment="",
                    selector="component=controller"):
    """
    applies a manifest and waits with a nice loading bar
    """
    apply = f"kubectl apply --wait -f {manifest_file_name}"

    rollout = f"kubectl rollout status -n {namespace} deployment/{deployment}"

    wait = (f"kubectl wait --for=condition=ready pod --selector={selector} "
            f"--timeout=90s -n {namespace}")

    # loops with progress bar until this succeeds
    subproc([apply, rollout, wait])


def configure_metallb(address_pool=[]):
    """
    metallb is special because it has Custom Resources:
        IPaddressPool and L2Advertisement
    Requires and accepts one arg:
        address_pool - list of IP addresses - default: []
    """
    url = ("https://raw.githubusercontent.com/metallb/metallb/v0.13.7/config/"
           "manifests/metallb-native.yaml")

    # install manifest and wait
    apply_manifests(url, "metallb-system", "controller",
                    "component=controller")

    # metallb requires a address pool configured and a layer 2 advertisement CR
    print_panel(log.info("Installing IPAddressPool and L2Advertisement custom resources."))

    ip_pool_cr = {'apiVersion': 'metallb.io/v1beta1',
                  'kind': 'IPAddressPool',
                  'metadata': {'name': 'default',
                               'namespace': 'metallb-system'},
                  'spec': {'addresses': address_pool}}

    l2_advert_cr = {'apiVersion': 'metallb.io/v1beta1',
                    'kind': 'L2Advertisement',
                    'metadata': {'name': 'default',
                                 'namespace': 'metallb-system'}}

    apply_custom_resources([ip_pool_cr, l2_advert_cr])
    return


def configure_ingress_nginx(k8s_distro="k3s"):
    """
    install nginx ingress controller from manifests for kind and helm for k3s
    # OLD: you need these to access webpages from outside the cluster
    # nginx_chart_opts = {'hostNetwork': 'true','hostPort.enabled': 'true'}
    # set_options=nginx_chart_opts)
    """
    url = ('https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/'
           'deploy/static/provider/kind/deploy.yaml')

    if k8s_distro == 'kind':
        # this is to wait for the deployment to come up
        apply_manifests(url, "ingress-nginx", "ingress-nginx-controller",
                        "app.kubernetes.io/component=controller")
    else:
        release = helm.chart(release_name='ingress-nginx',
                             chart_name='ingress-nginx/ingress-nginx',
                             namespace='ingress-nginx')
        release.install()
    return


def configure_cert_manager(email_addr):
    """
    installs cert-manager helm chart and letsencrypt-staging clusterissuer
    """

    # install chart and wait
    release = helm.chart(release_name='cert-manager',
                         chart_name='jetstack/cert-manager',
                         namespace='kube-system',
                         set_options={'installCRDs': 'true'})
    release.install(True)

    acme_staging = 'https://acme-staging-v02.api.letsencrypt.org/directory'
    issuer = {'apiVersion': 'cert-manager.io/v1',
              'kind': 'ClusterIssuer',
              'metadata': {'name': 'letsencrypt-staging'},
              'spec': {
                  'acme': {'email': email_addr,
                           'server': acme_staging,
                           'privateKeySecretRef': {
                               'name': 'letsencrypt-staging'},
                           'solvers': [
                               {'http01': {'ingress': {'class': 'nginx'}}}]
                           }}}

    apply_custom_resources([issuer])


def configure_external_secrets(external_secrets_config):
    """
    configure external secrets and provider. currently only works with gitlab
    Accepts dict as arg:
    dict = {'namespace': 'somenamespace', 'access_token': 'tokenhere'}
    """

    header("Installing External Secrets Operator...")
    release = helm.chart(release_name='external-secrets-operator',
                         chart_name='external-secrets/external-secrets',
                         namespace='external-secrets')
    release.install(True)

    gitlab_access_token = external_secrets_config['access_token']
    gitlab_namespace = external_secrets_config['namespace']

    # create the namespace if does not exist
    subproc([f'kubectl create namespace {gitlab_namespace}'], error_ok=True)

    # this currently only works with gitlab
    gitlab_secret = {'apiVersion': 'v1',
                     'kind': 'Secret',
                     'metadata': {'name': 'gitlab-secret',
                                  'namespace': gitlab_namespace,
                                  'labels': {'type': 'gitlab'}},
                     'type': 'Opaque',
                     'stringData': {'token': gitlab_access_token}}

    apply_custom_resources([gitlab_secret])
    return


def configure_argocd(argo_cd_domain="", argo_cd_grpc_domain="",
                     password_manager=False):
    """
    Installs argocd with ingress enabled by default and puts admin pass in a
    password manager, currently only bitwarden is supported
    arg:
        argo_cd_domain:   str, defaults to "", required
        password_manager: bool, defaults to False, optional

    extra ingress annotations for argocd:
        'tls': [{'hosts': [argo_cd_domain]}],
               # ingress resource 4 the Argo CD srvr 4 dedicated [gRPC-ingress]
               'ingressGrpc': {
                   'enabled': True,
                   'ingressClassName': 'nginx',
                   'hosts': [argo_cd_grpc_domain],
                   'annotations': {
                       "nginx.ingress.kubernetes.io/backend-protocol": 'GRPC'},
                   'tls': [{'hosts': [{argo_cd_grpc_domain: {
                       'secretName': 'argocd-secret'}}]}],
                   'https': True}}}
    """
    header("Installing 🦑 Argo CD...")

    # this is the base python dict for the values.yaml that is created below
    val = {'dex': {'enabled': False},
           'configs': {'secret': {'argocdServerAdminPassword': ""}},
           'server': {
               'ingress': {
                   'enabled': True,
                   'hosts': [argo_cd_domain],
                   'annotations': {
                       "kubernetes.io/ingress.class": "nginx",
                       "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                       "cert-manager.io/cluster-issuer": "letsencrypt-staging",
                       "kubernetes.io/tls-acme": True,
                       "nginx.ingress.kubernetes.io/ssl-passthrough": True,
                   },
                   'https': True,
                   'tls':  [{'secretName': 'argocd-secret',
                             'hosts': [argo_cd_domain]}]}}}

    # if we're using a password manager, generate a password & save it
    if password_manager:
        sub_header(":lock: Creating a new password in BitWarden.")
        # if we're using bitwarden...
        bw = BwCLI()
        bw.unlock()
        argo_password = bw.generate()
        bw.create_login(name=argo_cd_domain,
                        item_url=argo_cd_domain,
                        user="admin",
                        password=argo_password)
        bw.lock()
        admin_pass = bcrypt.hashpw(argo_password.encode('utf-8'),
                                   bcrypt.gensalt()).decode()

        # this gets passed to the helm cli, but is bcrypted
        val['configs']['secret']['argocdServerAdminPassword'] = admin_pass

    # this creates a values.yaml from from the val dict above
    values_file_name = '/tmp/smol-k8s-lab/argocd_values.yaml'
    with open(values_file_name, 'w') as values_file:
        dump(val, values_file)

    release = helm.chart(release_name='argo-cd',
                         chart_name='argo-cd/argo-cd',
                         namespace='argocd',
                         values_file=values_file_name)
    release.install(True)
    return


def install_kyverno():
    """
    does a helm install of kyverno
    """
    release = helm.chart(release_name='kyverno',
                         chart_name='kyverno/kyverno',
                         namespace='kyverno')
    release.install()


# an ugly list of decorators, but these are the opts/args for the whole script
@command(cls=RichCommand, context_settings=HELP_SETTINGS)
@argument("k8s", metavar="<k3s OR kind>", default="")
@option('--argo', '-a', is_flag=True, help=HELP['argo'])
@option('--config', '-c', metavar="CONFIG_FILE", type=str,
        default=path.join(HOME_DIR, '.config/smol-k8s-lab/config.yaml'),
        help=HELP['config'])
@option('--delete', '-D', is_flag=True, help=HELP['delete'])
@option('--external_secret_operator', '-e', is_flag=True,
        help=HELP['external_secret_operator'])
@option('--kyverno', '-k', is_flag=True, help=HELP['kyverno'])
@option('--k9s', '-K', is_flag=True, help=HELP['k9s'])
@option('--log_level', '-l', metavar='LOGLEVEL', help=HELP['log_level'],
        type=Choice(['debug', 'info', 'warn', 'error']))
@option('--log_file', '-o', metavar='LOGFILE', help=HELP['log_file'])
@option('--password_manager', '-p', is_flag=True,
        help=HELP['password_manager'])
@option('--version', '-v', is_flag=True, help=HELP['version'])
def main(k8s: str = "",
         argo: bool = False,
         config: str = "",
         delete: bool = False,
         external_secret_operator: bool = False,
         kyverno: bool = False,
         k9s: bool = False,
         log_level: str = "",
         log_file: str = "",
         password_manager: bool = False,
         version: bool = False):
    """
    Quickly install a k8s distro for a homelab setup. Installs k3s
    with metallb, ingess-nginx, cert-manager, and argocd
    """
    # setup logging immediately
    log = setup_logger(log_level, log_file)

    # only return the version if --version was passed in
    if version:
        print(f'\n🎉 v{VERSION}\n')
        return True

    # make sure we got a valid k8s distro
    if k8s not in ['k3s', 'kind']:
        log.error(f'\n☹ Sorry, "[b]{k8s}[/]" is not a currently supported k8s'
                  ' distro. Please try again with k3s or kind.\n')
        exit()

    # before we do anything, we need to make sure this OS is supported
    check_os_support()

    if delete:
        # this exist the script after deleting the cluster
        delete_cluster(k8s)

    # load in config file
    try:
        with open(config, 'r') as yaml_file:
            input_variables = safe_load(yaml_file)
    except FileNotFoundError:
        log.error(f"Expected config file, {config}, but it was not found")

    # make sure the tmp directory exists, to store stuff
    Path("/tmp/smol-k8s-lab").mkdir(exist_ok=True)

    # install the actual KIND or k3s cluster
    header(f'Installing [green]{k8s}[/] cluster.')
    sub_header('This could take a min ʕ•́ᴥ•̀ʔっ♡ ', False)
    install_k8s_distro(k8s)

    # make sure helm is installed and the repos are up to date
    prepare_helm(k8s, argo, external_secret_operator, kyverno)

    # needed for metal (non-cloud provider) installs
    header("Installing [b]metallb[/b] so we have an ip address pool")
    configure_metallb(input_variables['metallb_address_pool'])

    # this is so we can accept traffic from outside the cluster
    header("Installing [b]ingress-nginx-controller[/b]...")
    configure_ingress_nginx(k8s)

    # this is for manager SSL/TLS certificates via lets-encrypt
    header("Installing [b]cert-manager[/b] for TLS certificates...")
    configure_cert_manager(input_variables['email'])

    # this is for external secrets, currently only supports gitlab
    if external_secret_operator:
        external_secrets = input_variables['external_secrets']['gitlab']
        configure_external_secrets(external_secrets)

    if kyverno:
        install_kyverno()

    # then install argo CD ꒰ᐢ.   ̫ .ᐢ꒱ <---- who is he? :3
    if argo:
        # todo: make less ugly
        base = input_variables['domains']['base']
        argo_cd_domain = input_variables['domains']['argo_cd']
        argo_cd_grpc_domain = input_variables['domains']['argo_cd_grpc']
        argocd_fqdn = ".".join([argo_cd_domain, base])
        argocd_grpc_fqdn = ".".join([argo_cd_grpc_domain, base])
        configure_argocd(argocd_fqdn, argocd_grpc_fqdn, password_manager)

    # we're done :D
    print("")
    CONSOLE.print(Panel("\nSmol K8s Lab completed!\n\nMake sure you run:\n"
                        f"[b]export KUBECONFIG={HOME_DIR}/.kube/kubeconfig\n",
                        title='[green]◝(ᵔᵕᵔ)◜ Success!',
                        subtitle='♥ [cyan]Have a nice day[/] ♥',
                        border_style="cornflower_blue"))
    print("")


if __name__ == '__main__':
    main()

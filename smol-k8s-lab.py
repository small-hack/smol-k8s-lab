#!/usr/bin/env python3.10
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
Works with k3s and KinD
"""
import bcrypt
from click import option, argument, command
from collections import OrderedDict
import logging
from os import chmod, getenv, path, remove
from pathlib import Path
import requests
# to pretty print things
from rich.theme import Theme
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
import shutil
import stat
from sys import exit
from time import sleep
from yaml import dump, safe_load
# custom local libraries
from util.homelabHelm import helm
from util.subproc import subproc
from util.logging import simple_loading_bar, header, sub_header
from util.rich_click import RichCommand
from util.bw_cli import BwCLI


# for console AND file logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")

PWD = path.dirname(__file__)
HOME_DIR = getenv("HOME")
# this is for rich text, to pretty print things
soft_theme = Theme({"info": "dim cornflower_blue",
                    "warn": "yellow on black",
                    "danger": "bold magenta"})
CONSOLE = Console(theme=soft_theme)


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
    # --flannel-backend=host-gw')
    subproc([cmd], False, True, False)

    # create the ~/.kube directory if it doesn't exist
    Path(f'{HOME_DIR}/.kube').mkdir(exist_ok=True)

    # Grab the kubeconfig and copy it locally
    cp = f'sudo cp /etc/rancher/k3s/k3s.yaml {HOME_DIR}/.kube/kubeconfig'
    # change the permissions os that it doesn't complain
    chmod_cmd = f'sudo chmod 644 {HOME_DIR}/.kube/kubeconfig'
    # run both commands one after the other
    subproc([cp, chmod_cmd], False, True, False)
    # remove the script after we're done
    remove('./install.sh')


def install_kind_cluster():
    """
    python installation process for kind
    """
    # make sure kind is installed first, and if not, install it
    if not shutil.which("kind"):
        msg = ("ʕ•́ᴥ•̀ʔ [b]Kind[/b] is [warn]not installed[/warn]. "
               "[i]We'll install it for you.[/i] ʕᵔᴥᵔʔ")
        CONSOLE.print(msg, justify='center')
        subproc(['brew install kind'])
    # then use our pre-configured kind file to install a small cluster

    full_path = path.join(PWD, '/distros/kind/kind_cluster_config.yaml')
    subproc([f"kind create cluster --config={full_path}"])
    return


def install_custom_resources(custom_resource_dict_list):
    """
    Does a kube apply on a custom resource dict, and retries if it fails
    using loading bar for progress
    """
    k_cmd = 'kubectl apply -f '
    commands = {}
    # Write a YAML representation of data to '/tmp/{resource_name}.yaml'.
    for custom_resource_dict in custom_resource_dict_list:
        resource_name = "_".join([custom_resource_dict['kind'],
                                  custom_resource_dict['metadata']['name']])
        yaml_file_name = f'/tmp/{resource_name}.yaml'
        with open(yaml_file_name, 'w') as cr_file:
            dump(custom_resource_dict, cr_file)
        commands[f'Installing {resource_name}'] = k_cmd + yaml_file_name

    # loops with progress bar until this succeeds
    simple_loading_bar(commands)


def configure_metallb(address_pool):
    """
    metallb is special because it has Custom Resources
    """
    logging.info("Making sure kube-system pod-security is setup...")
    cmds = []
    cmds.append("kubectl create namespace metallb-system")
    base_cmd = 'kubectl label namespace metallb-system'
    cmds.append(f"{base_cmd} pod-security.kubernetes.io/enforce=privileged")
    cmds.append(f"{base_cmd} pod-security.kubernetes.io/audit=privileged")
    cmds.append(f"{base_cmd} pod-security.kubernetes.io/warn=privileged")
    # install manifest and wait
    # cmds.append("kubectl apply --wait -f https://raw.githubusercontent.com/"
    #       "metallb/metallb/v0.13.6/config/manifests/metallb-native.yaml")
    subproc(cmds)
    sleep(15)

    # old helm install manifest and wait
    release = helm.chart(chart_name='metallb/metallb',
                         release_name='metallb',
                         namespace='metallb-system')
    release.install(True)

    log.info("Installing IPAddressPool and L2Advertisement custom resources.")

    ip_pool_cr = {'apiVersion': 'metallb.io/v1beta1',
                  'kind': 'IPAddressPool',
                  'metadata': {'name': 'base-pool',
                               'namespace': 'metallb-system'},
                  'spec': {'addresses': address_pool}}

    l2_advert_cr = {'apiVersion': 'metallb.io/v1beta1',
                    'kind': 'L2Advertisement',
                    'metadata': {'name': 'base-pool-advert',
                                 'namespace': 'metallb-system'}}

    install_custom_resources([ip_pool_cr, l2_advert_cr])


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

    install_custom_resources([issuer])


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
    subproc([f'kubectl create namespace {gitlab_namespace}'], True)

    # this currently only works with gitlab
    gitlab_secret = {'apiVersion': 'v1',
                     'kind': 'Secret',
                     'metadata': {'name': 'gitlab-secret',
                                  'namespace': gitlab_namespace,
                                  'labels': {'type': 'gitlab'}},
                     'type': 'Opaque',
                     'stringData': {'token': gitlab_access_token}}

    install_custom_resources([gitlab_secret])
    return


def delete_cluster(k8s_distro="k3s"):
    """
    Delete a KIND or K3s cluster entirely.
    """
    header(f"ヾ(^_^) byebye {k8s_distro}!!")

    if k8s_distro == 'k3s':
        subproc(['k3s-uninstall.sh'], True, True, False)
    elif k8s_distro == 'kind':
        subproc(['kind delete cluster'])
    else:
        header("┌（・Σ・）┘≡З  Whoops. {k8s_distro} not YET supported.")

    exit()


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


def install_argocd(argo_cd_domain="", password_manager=False):
    """
    Installs argocd with ingress enabled by default and puts admin pass in a
    password manager, currently only bitwarden is supported
    """
    opts = {'dex.enabled': 'false',
            'server.ingress.enabled': 'true',
            'server.ingress.ingressClassName': 'nginx',
            'server.ingress.hosts[0]': argo_cd_domain,
            'server.extra[0]': '--insecure'}

    # if we're using a password manager, generate a password & save it
    if password_manager:
        header(":lock: Creating a new password in BitWarden.")
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
        opts['configs.secret.argocdServerAdminPassword'] = admin_pass

    header("Installing Argo CD...")

    release = helm.chart(release_name='argo-cd',
                         chart_name='argo-cd/argo-cd',
                         namespace='argocd',
                         set_options=opts)
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
@command(cls=RichCommand)
@argument("k8s",
          metavar="<k3s OR kind>",
          default="")
@option('--argo', '-a',
        is_flag=True,
        help='Install Argo CD as part of this script. Defaults to False')
@option('--delete',
        is_flag=True,
        help='Delete the existing cluster.')
@option('--external_secret_operator', '-e',
        is_flag=True,
        help='Install the external secrets operator to pull secrets from '
             'somewhere else, so far only supporting gitlab.')
@option('--file', '-f',
        metavar="FILE",
        type=str,
        default='./config.yml',
        help='Full path and name of yml to parse.\n'
             'Example: -f [light_steel_blue]/tmp/config.yml[/]')
@option('--kyverno',
        is_flag=True,
        help='[i](Experimental)[/i] Install kyverno. Defaults to False.')
@option('--k9s',
        is_flag=True,
        help='Run k9s as soon as this script is complete. '
             'Defaults to False')
@option('--password_manager', '-p',
        is_flag=True,
        help='Store generated admin passwords directly into your password '
             'manager. Right now, this defaults to Bitwarden and requires you'
             ' to input your vault password to unlock the vault temporarily.')
def main(k8s: str,
         argo: bool = False,
         delete: bool = False,
         external_secret_operator: bool = False,
         file: str = "",
         kyverno: bool = False,
         k9s: bool = False,
         password_manager: bool = False):
    """
    Quickly install a k8s distro for a homelab setup. Installs k3s
    with metallb, nginx-ingess-controller, cert-manager, and argocd
    """

    # make sure we got a valid k8s distro
    if k8s not in ['k3s', 'kind']:
        CONSOLE.print(f'\n☹ Sorry, "[b]{k8s}[/]" is not a currently supported '
                      'k8s distro. Please try again with k3s or kind.\n')
        exit()

    if delete:
        # this exist the script after deleting the cluster
        delete_cluster(k8s)

    with open(file, 'r') as yaml_file:
        input_variables = safe_load(yaml_file)

    # install the actual KIND or k3s cluster
    header(f'Installing [green]{k8s}[/] cluster.')
    sub_header('This could take a min ʕ•́ᴥ•̀ʔっ♡ ', False)
    install_k8s_distro(k8s)

    # make sure helm is installed and the repos are up to date
    prepare_helm(k8s, argo, external_secret_operator, kyverno)

    # needed for metal (non-cloud provider) installs
    header("Configuring metallb so we have an ip address pool")
    configure_metallb(input_variables['metallb_address_pool'])

    header("Installing nginx-ingress-controller...")
    # KinD has special ingress-nginx install
    if k8s == 'kind':
        url = ('https://raw.githubusercontent.com/kubernetes/ingress-nginx'
               '/main/deploy/static/provider/kind/deploy.yaml')
        subproc([f'kubectl apply -f {url}'])

        # this is to wait for the deployment to come up
        rollout_cmd = ('kubectl rollout status -n ingress-nginx deployment'
                       '/ingress-nginx-controller')
        wait_cmd = ('kubectl wait --for=condition=ready pod '
                    '--selector=app.kubernetes.io/component=controller '
                    '--timeout=90s -n ingress-nginx')
        subproc([rollout_cmd, wait_cmd])
    else:
        # you need this to access webpages from outside the cluster
        # nginx_chart_opts = {'hostNetwork': 'true',
        #                     'hostPort.enabled': 'true'}
        release = helm.chart(release_name='nginx-ingress',
                             chart_name='ingress-nginx/ingress-nginx',
                             namespace='kube-system')
        #                     set_options=nginx_chart_opts)
        release.install()

    # this is for manager SSL/TLS certificates via lets-encrypt
    header("Installing cert-manager for TLS certificates...")
    configure_cert_manager(input_variables['email'])

    # this is for external secrets, currently only supports gitlab
    if external_secret_operator:
        external_secrets = input_variables['external_secrets']['gitlab']
        configure_external_secrets(external_secrets)

    if kyverno:
        install_kyverno()

    # then install argo CD :D
    if argo:
        argo_cd_domain = input_variables['domains']['argo_cd']
        install_argocd(argo_cd_domain, password_manager)

    CONSOLE.print(Panel("\nSmol K8s Lab completed!\n\nMake sure you run:\n"
                        f"[b]export KUBECONFIG={HOME_DIR}/.kube/kubeconfig",
                        title='[green]₍ᐢ•ﻌ•ᐢ₎っSuccess ♥',
                        subtitle='[cyan]Have a nice day ♥'))


if __name__ == '__main__':
    main()

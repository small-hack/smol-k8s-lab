#!/usr/bin/env python3.11
"""
       Name: external_secrets
DESCRIPTION: configures external secrets, currently only with gitlab
             hopefully with more supported providers in the future
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from ..k8s_tools.homelabHelm import helm
from ..k8s_tools.kubernetes_util import apply_custom_resources
from ..subproc import subproc
from ..console_logging import header
import platform
import lsb_release
import urllib.request
import gnupg
from pprint import pprint

def configure_gpu_operator():
    """
    configure the Nvidia GPU operator
    """
    # Get the nvidia gpg Key
    gpg = gnupg.GPG()
    target_file = "nvidia-container-toolkit-keyring.gpg"
    server = "https://nvidia.github.io/libnvidia-container/gpgkey"
    urllib.request.urlretrieve(server, target_file)
    key_data = open(target_file).read()
    subproc([f"cat {target_file} | sudo gpg --dearmor -o /usr/share/keyrings/{target_file}"], error_ok=False)
    # Install the container runtime prior to cluster creation
    # see docs.k3s.io/advanced
    # docs.nvidia.com/datacenter/cloud-native/gpu-operator/getting-started.html
    header("Installing the NVIDIA Container Toolkit...")

    # Get the Linux distribution. Debian12 is not supported so debain11 is entered 
    # to fool the installer into letting it work. We dont support debian10 
    # so it works out in the end.
    if "Ubuntu" in platform.version():
        release = lsb_release.get_distro_information()['RELEASE']
        distribution = f"ubuntu{release}"
        print(f"distribution is: {distribution}")

    if "Debian" in platform.version():
        distribution = "debian11"
        print(f"distribution is: {distribution}")

    # Download the container list
    target_file = "nvidia-container-toolkit.list"

    urllib.request.urlretrieve(f"https://nvidia.github.io/libnvidia-container/{distribution}/libnvidia-container.list", target_file) 
    with open(target_file, 'r') as file :
        filedata = file.read()
    
    # Regex it
    filedata = filedata.replace('deb https://', 'deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://')
    
    # Save it
    with open(target_file, 'w') as file:
        file.write(filedata)

    subproc([f"sudo mv {target_file} /etc/apt/sources.list.d/"], error_ok=False)

    # update apt package cache and install the toolkit
    subproc(['sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit'], error_ok=False)

    # Set NVIDIA as the default container runtime
    subproc(['sudo nvidia-ctk runtime configure --runtime=docker'], error_ok=False)

    # Restart docker daemon to finalize change
    subproc(['sudo systemctl restart docker'], error_ok=False)

    # Edit the config.toml to use root location
    subproc(['sudo sed -i "s/^#root/root/" /etc/nvidia-container-runtime/config.toml'], error_ok=False)

    #header("Installing GPU Operator...")
    #release = helm.chart(release_name='gpu-operator',
    #                     chart_name='nvidia/gpu-operator',
    #                     namespace='gpu-operator')
    #                     # chart_version='',
    #release.install(True)

    # create the namespace if does not exist
    #subproc(['kubectl create namespace gpu-operator'], error_ok=True)

    # this currently only works with gitlab
    # gitlab_secret = {'apiVersion': 'v1',
    #                  'kind': 'Secret',
    #                  'metadata': {'name': 'gitlab-secret',
    #                               'namespace': gitlab_namespace,
    #                               'labels': {'type': 'gitlab'}},
    #                  'type': 'Opaque',
    #                  'stringData': {'token': gitlab_access_token}}
    # apply_custom_resources([gitlab_secret])

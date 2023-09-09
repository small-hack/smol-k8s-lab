#!/usr/bin/env python3.11
"""
       Name: extras
DESCRIPTION: install extra tooling related to k8s
     AUTHOR: <https://github.com/jessebot>
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
from os import path
from..utils.subproc import subproc
from .constants import PWD


def do_setup():
    """
    - Install/Update brew dependencies from Brewfile:
      docker, kind, kubectl, helm, krew, k9s, argocd, bitwarden-cli
    - Install/Update kubectl plugins with krew:
      ctx, ns, example, deprecations

    returns True
    """
    brewfile = path.join(PWD, 'config/extras/Brewfile')
    cmds = [f"brew bundle --file={brewfile}",
            "kubectl krew install ctx",
            "kubectl krew install ns",
            "kubectl krew install example",
            "kubectl krew install deprecations",
            "kubectl krew update",
            "kubectl krew upgrade"]
    subproc(cmds, error_ok=True)

    return True

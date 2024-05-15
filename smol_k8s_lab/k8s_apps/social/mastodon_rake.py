#!/usr/bin/env python
""" 
This is just for generating mastodon rake secrets and testing on the cli
"""
from smol_k8s_lab.utils.run.subproc import subproc


def generate_rake_secrets() -> None:
    """
    These are required for mastodon:
        https://docs.joinmastodon.org/admin/config/#secrets

    SECRET_KEY_BASE Generate with rake secret.
                    Changing it will break all active browser sessions.

    OTP_SECRET      Generate with rake secret.
                    Changing it will break two-factor authentication.

    VAPID_PRIVATE_KEY Generate with rake mastodon:webpush:generate_vapid_key.
                      Changing it will break push notifications.

    VAPID_PUBLIC_KEY  Generate with rake mastodon:webpush:generate_vapid_key.
                      Changing it will break push notifications.
    """
    final_dict = {"SECRET_KEY_BASE": "",
                  "OTP_SECRET": "",
                  "VAPID_PRIVATE_KEY": "",
                  "VAPID_PUBLIC_KEY": ""}

    # we use docker to generate all of these
    base_cmd = "docker run docker.io/tootsuite/mastodon:latest rake"

    # this is for the SECRET_KEY_BASE and OTP_SECRET values
    secret_cmd = base_cmd + " secret"
    final_dict['SECRET_KEY_BASE'] = subproc([secret_cmd]).split()[0]
    final_dict['OTP_SECRET'] = subproc([secret_cmd]).split()[0]

    # this is for the vapid keys
    vapid_cmd = base_cmd + " mastodon:webpush:generate_vapid_key"
    vapid_keys = subproc([vapid_cmd]).split()

    final_dict['VAPID_PRIVATE_KEY'] = vapid_keys[0].split("=")[1]
    final_dict['VAPID_PUBLIC_KEY'] = vapid_keys[1].split("=")[1]

    return final_dict

if __name__ == '__main__':
    print(generate_rake_secrets())

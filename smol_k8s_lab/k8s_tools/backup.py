# local libs
from smol_k8s_lab.utils.subproc import subproc
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_apps.social.nextcloud_occ_commands import Nextcloud

# external libs
# import asyncio
from datetime import datetime
import logging as log
from time import sleep


def create_pvc_restic_backup(app: str,
                             namespace: str,
                             endpoint: str,
                             bucket: str,
                             cnpg_backup: bool = True) -> None:
    """
    a function to immediately run a restic backup job
    unless it's nextcloud, then we put it into maintenance_mode first...
    """
    now = datetime.now().strftime('%Y-%m-%d-%H-%M')
    backup_name = f"{app}-onetime-backup-{now}"
    backup_yaml = {
            "apiVersion": "k8up.io/v1",
            "kind": "Backup",
            "metadata": {
              "name": backup_name,
              "namespace": namespace
              },
            "spec": {
              "failedJobsHistoryLimit": 5,
              "promURL": "push-gateway.prometheus.svc:9091",
              "successfulJobsHistoryLimit": 2,
              "backend": {
                "repoPasswordSecretRef": {
                  "key": "resticRepoPassword",
                  "name": "s3-backups-credentials"
                },
                "s3": {
                  "accessKeyIDSecretRef": {
                    "key": "accessKeyID",
                    "name": "s3-backups-credentials",
                    "optional": False
                    },
                  "bucket": bucket,
                  "endpoint": endpoint,
                  "secretAccessKeySecretRef": {
                    "key": "secretAccessKey",
                    "name": "s3-backups-credentials",
                    "optional": False
                    }
                  }
                }
              }
            }

    # nextcloud is special and needs to be put into maintenance mode before backups
    if app == "nextcloud":
        # nextcloud backups need to run as user 82 which is nginx
        backup_yaml['spec']['podSecurityContext'] = {"runAsUser": 82}
        nextcloud = Nextcloud(K8s(), namespace)
        nextcloud.set_maintenance_mode("on")

        # then wait for maintenance_mode to be fully on
        sleep(10)

    # do the database backup if this app has one
    if cnpg_backup:
        create_cnpg_cluster_backup(app, namespace)

    # then we can do the actual backup
    k8s = K8s()
    k8s.apply_custom_resources([backup_yaml])

    # wait for backup to complete
    wait_cmd = (f"kubectl wait job -n {namespace} --for=condition=complete "
                f"backup-{backup_name}-0 --timeout=15m")
    print(wait_cmd)
    while True:
        log.debug(f"Waiting for backup job: backup-{backup_name}-0")
        res = subproc([wait_cmd], error_ok=True)
        log.error(res)
        if "NotFound" in res:
            sleep(1)
        else:
            break

    if app == "nextcloud":
        # turn nextcloud maintenance_mode off after the backup
        nextcloud.set_maintenance_mode("off")

    return True


def create_cnpg_cluster_backup(app: str, namespace: str) -> None:
    """
    creates a backup for cnpg clusters and waits for it to complete
    """
    now = datetime.now().strftime('%Y-%m-%d-%H-%M')
    backup_name = f"{app}-onetime-cnpg-backup-{now}"
    cnpg_backup = {"apiVersion": "postgresql.cnpg.io/v1",
                   "kind": "Backup",
                   "metadata": {
                      "name": backup_name,
                      "namespace": namespace
                      },
                   "spec": {
                      "method": "barmanObjectStore",
                      "cluster": {
                        "name": f"{app}-postgres"
                        }
                      }
                   }

    # then we can do the actual backup
    k8s = K8s()
    k8s.apply_custom_resources([cnpg_backup])

    # wait for backup to complete
    wait_cmd = (f"kubectl get -n {namespace} --no-headers "
                "-o custom-columns=PHASE:.status.phase "
                f"backups.postgresql.cnpg.io/{backup_name}")
    while True:
        log.error(f"Waiting on backups.postgresql.cnpg.io/{backup_name} to complete")
        res = subproc([wait_cmd], error_ok=True)
        log.error(res)
        if "completed" in res:
            break
        sleep(1)

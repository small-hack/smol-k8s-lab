# local libs
from smol_k8s_lab.utils.subproc import subproc
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_apps.social.nextcloud_occ_commands import Nextcloud
from smol_k8s_lab.utils.minio_lib import BetterMinio

# external libs
# import asyncio
from datetime import datetime
import logging as log
from time import sleep


def create_pvc_restic_backup(app: str,
                             namespace: str,
                             endpoint: str,
                             bucket: str,
                             cnpg_backup: bool = True,
                             quiet: bool = False) -> None:
    """
    a function to immediately run a restic backup job
    unless it's nextcloud, then we put it into maintenance_mode first...

    pass in quiet=True to disable loading spinners for logging
    """
    now = datetime.now().strftime('%Y-%m-%d-%H-%M')
    # make sure we don't have any _, as some kubectl commands don't like them
    app = app.replace("_","-")
    backup_name = f"{app}-smol-k8s-lab-{now}"
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
        nextcloud = Nextcloud(K8s(), namespace, quiet)
        nextcloud.set_maintenance_mode("on")

        # then wait for maintenance_mode to be fully on
        sleep(10)

    # do the database backup if this app has one
    if cnpg_backup:
        create_cnpg_cluster_backup(app, namespace, quiet=quiet)

    # then we can do the actual backup
    k8s = K8s()
    k8s.apply_custom_resources([backup_yaml])

    # wait for backup to complete
    wait_cmd = (f"kubectl wait job -n {namespace} --for=condition=complete "
                f"backup-{backup_name}-0 --timeout=15m")
    print(wait_cmd)
    while True:
        log.debug(f"Waiting for backup job: backup-{backup_name}-0")
        res = subproc([wait_cmd], error_ok=True, spinner=quiet)
        log.debug(res)
        if "NotFound" in res:
            sleep(1)
        else:
            break

    if app == "nextcloud":
        # turn nextcloud maintenance_mode off after the backup
        nextcloud.set_maintenance_mode("off")

    return True


def create_cnpg_cluster_backup(app: str,
                               namespace: str,
                               s3_endpoint: str,
                               access_key_id: str,
                               secret_access_key: str,
                               quiet: bool = False) -> None:
    """
    creates a backup for cnpg clusters and waits for it to complete

    pass in quiet=True to disable loading spinners for logging
    """
    now = datetime.now().strftime('%Y-%m-%d-%H-%M')
    backup_name = f"{app}-smol-k8s-lab-cnpg-backup-{now}"
    cluster_name = f"{app}-postgres"
    cnpg_backup = {"apiVersion": "postgresql.cnpg.io/v1",
                   "kind": "Backup",
                   "metadata": {
                      "name": backup_name,
                      "namespace": namespace
                      },
                   "spec": {
                      "method": "barmanObjectStore",
                      "cluster": {
                        "name": cluster_name
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
        res = subproc([wait_cmd], error_ok=True, spinner=quiet)
        log.error(res)
        if "completed" in res:
            break
        sleep(1)

    # after the backup is completed, check which wal archive it says is the last one
    end_wal_cmd = (f"kubectl get backups.postgresql.cnpg.io/{backup_name} -o "
                   "custom-columns=endwal:.status.endWal --no-headers")
    end_wal = subproc([end_wal_cmd])
    end_wal_folder = f"{cluster_name}/wals/{end_wal[:16]}"
    log.debug(f"{end_wal_folder} is the Wal folder we expect for {cluster_name} backup")

    # wait till that wal archive is actually available before declaring the
    # function complete
    s3 = BetterMinio("", s3_endpoint, access_key_id, secret_access_key)
    while True:
        # after the backup is completed, wait for the final wal archive to complete
        try:
            wal_files = s3.list_object(cluster_name,
                                       end_wal_folder,
                                       recursive=True)
        except Exception as e:
            log.debug(e)
            log.debug(f"{end_wal_folder} still not found")
            continue

        # make sure the specific wal file we want is present
        for wal_obj in wal_files:
            if end_wal in wal_obj.object_name:
                log.info(f"Found ending wal archive, {end_wal}, so cnpg backup for {app} is now complete.")
                break

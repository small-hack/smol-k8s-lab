# local libs
from smol_k8s_lab.utils.run.subproc import subproc
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_apps.social.nextcloud_occ_commands import Nextcloud
from smol_k8s_lab.utils.minio_lib import BetterMinio

# external libs
# import asyncio
import base64
from datetime import datetime
import logging as log
from time import sleep


def create_pvc_restic_backup(app: str,
                             namespace: str,
                             endpoint: str,
                             bucket: str,
                             cnpg_backup: bool = True,
                             cnpg_s3_endpoint: str = "",
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
                    "key": "accessKeyId",
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
        create_cnpg_cluster_backup(app, namespace, cnpg_s3_endpoint, quiet=quiet)

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

    # get credentials and setup s3 object to check if all wal archives are there
    credentials = k8s.get_secret("s3-postgres-credentials", namespace)
    access_key_id = base64.b64decode(credentials['data']['accessKeyId']).decode('utf-8')
    secret_access_key = base64.b64decode(credentials['data']['secretAccessKey']).decode('utf-8')
    log.error("got credentials and about to check s3")
    s3 = BetterMinio("", s3_endpoint, access_key_id, secret_access_key)
    all_wals = f"{cluster_name}/wals"

    # after the backup is completed, check which wal archive it says is the last one
    end_wal_cmd = (
            f"kubectl get -n {namespace} backups.postgresql.cnpg.io/{backup_name}"
            f" -o custom-columns=endwal:.status.endWal --no-headers"
            )
    end_wal = subproc([end_wal_cmd]).strip()
    end_wal_folder = f"{all_wals}/{end_wal[:16]}/{end_wal}"
    log.error(f"Wal folder we expect for {cluster_name} backup is: '{end_wal_folder}'")
    check_for_specific_wal(s3, cluster_name, all_wals, end_wal)

    # wait till that wal archive is actually available before declaring the
    # function completed
    # while True:
    #     log.error("Checking if file is available")
    #     # after the backup is completed, wait for the final wal archive to complete
    #     try:
    #         wal_file = s3.list_object(cluster_name, end_wal_folder, recursive=True)
    #         for sub_obj in wal_file:
    #             log.info(sub_obj.object_name)
    #         log.error(f"{end_wal_folder} was found. Sleeping for 15 seconds just in case.")
    #         sleep(15)
    #         break
    #     except Exception as e:
    #         log.error(e)
    #         log.error(f"{end_wal_folder} still not found. Sleeping 5 seconds.")
    #         sleep(5)
    #         continue

    # new_total_wals = get_total_wals(s3, cluster_name, all_wals)
    # log.error(f"New total number of wals after is {str(new_total_wals)}")
    # verify the wal is absolutely completed by waiting for the next one
    # while True:
    #     new_total_wals = get_total_wals(s3, cluster_name, all_wals)
    #     log.error(f"New total number of wals after is {str(new_total_wals)}")
    #     if new_total_wals > total_wals:
    #         log.error(f"New Total number of wals is {str(new_total_wals)} which"
    #                   f"is more than our starting wal count: {str(total_wals)}"
    #                   ", so we break and return")
    #         return
    #     else:
    #         log.error(f"Total number of wals is {str(new_total_wals)} which is "
    #                   f"not more than our starting wal count: {str(total_wals)}"
    #                   ", so we will wait 10 seconds")
    #         sleep(10)

def check_for_specific_wal(s3: BetterMinio,
                           cluster_name: str,
                           all_wals_dir: str,
                           wall_to_chck: str):
    """
    count the number of wals in s3 for this cluster and log them each
    """

    while True:
        wal_files = s3.list_object(cluster_name, all_wals_dir, recursive=True)
        total_wals = 0
        for wal in wal_files:
            total_wals += 1
            log.error(f"{str(total_wals)}: Found a wal called {wal.object_name}")

            # return if we found the correct wal
            if wall_to_chck in wal.object_name:
                log.error("wal to check present 🎉")
                sleep(2)
                return True

        log.error(f"found {str(total_wals)} total wal files, but not the one we wanted: {wall_to_chck}. Sleeping 10 seconds...")
        sleep(10)

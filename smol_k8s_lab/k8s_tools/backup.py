import logging as log
from smol_k8s_lab.utils.subproc import subproc
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from time import sleep


def create_pvc_restic_backup(app: str,
                             namespace: str,
                             bucket: str,
                             endpoint: str,
                             cnpg_backup: bool = True) -> None:
    """
    a function to immediately run a restic backup job
    unless it's nextcloud, then we put it into maintenance_mode first...
    """
    backup_yaml = {
            "apiVersion": "k8up.io/v1",
            "kind": "Backup",
            "metadata": {
              "name": f"{app}-onetime-backup",
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

        # get current nextcloud pod
        pod = ("kubectl get pods -l=app.kubernetes.io/component=app,"
               "app.kubernetes.io/instance=nextcloud-web-app --no-headers "
               "-o custom-columns=NAME:.metadata.name")
        pod = subproc([pod]).strip()

        # check nextcloud maintenance mode status
        check_cmd = (f'kubectl exec -it {pod} -- /bin/sh -c '
                     '"php occ maintenance:mode"')
        maintenance_mode = subproc([check_cmd])
        # scan all the current files into the database first
        scan_cmd = (f'kubectl exec -it {pod} -- /bin/sh -c '
                    '"php occ files:scan --all"')
        on_cmd = (f'kubectl exec -it {pod} -- /bin/sh -c '
                  '"php occ maintenance:mode --on"')

        if maintenance_mode != "off":
            # scan all files into database then turn on maintenance_mode
            subproc([scan_cmd, on_cmd])
        else:
            # turn off maintenance_mode because you can only scan files when its
            # off, then scan all files into database then turn on maintenance
            off_cmd = (f'kubectl exec -it {pod} -- /bin/sh -c '
                       '"php occ maintenance:mode --off"')
            subproc([off_cmd, scan_cmd, on_cmd])

        # then wait for maintenance_mode to be fully on
        sleep(10)

    # do the database backup if this app has one
    if cnpg_backup:
        create_cnpg_cluster_backup(app, namespace)

    # then we can do the actual backup
    k8s = K8s()
    k8s.apply_custom_resources([backup_yaml])

    # wait for backup to complete
    wait_cmd = (f"kubectl wait -n {namespace} --for=condition=complete "
                f"job/{app}-onetime-backup")
    while True:
        log.debug(f"Waiting for backup job: {app}-onetime-backup")
        res = subproc([wait_cmd], error_ok=True)
        if "NotFound" in res:
            sleep(1)
        else:
            break

    if app == "nextcloud":
        # turn nextcloud maintenance_mode off after the backup
        subproc([off_cmd])

    return True


def create_cnpg_cluster_backup(app: str, namespace: str) -> None:
    """
    creates a backup for cnpg clusters and waits for it to complete
    """
    cnpg_backup = {"apiVersion": "postgresql.cnpg.io/v1",
                   "kind": "Backup",
                   "metadata": {
                      "name": f"{app}-cnpg-backup",
                      "namespace": namespace
                      },
                   "spec": {
                      "method": "barmanObjectStore",
                      "cluster": {
                        "name": f"{app}-postgresql"
                        }
                      }
                   }

    # then we can do the actual backup
    k8s = K8s()
    k8s.apply_custom_resources([cnpg_backup])

    # wait for backup to complete
    wait_cmd = (f"kubectl wait -n {namespace} --for=condition=complete "
                f"job/{app}-cnpg-backup")
    while True:
        log.debug(f"Waiting for cnpg backup job: {app}-cnpg-backup")
        res = subproc([wait_cmd], error_ok=True)
        if "NotFound" in res:
            sleep(1)
        else:
            break

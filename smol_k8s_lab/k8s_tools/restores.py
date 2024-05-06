"""
       Name: restores.py
DESCRIPTION: restore stuff with k8up (restic on k8s) and cnpg operator
     AUTHOR: @jessebot
    LICENSE: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
"""
# internal libraries
from smol_k8s_lab.constants import XDG_CACHE_DIR
from smol_k8s_lab.k8s_tools.argocd_util import ArgoCD
from smol_k8s_lab.k8s_tools.k8s_lib import K8s
from smol_k8s_lab.k8s_tools.helm import Helm
from smol_k8s_lab.utils.subproc import subproc

# external libraries
from datetime import datetime
from json import loads
import logging as log
from os import path, environ
from time import sleep
import yaml


def restore_seaweedfs(argocd: ArgoCD,
                      app: str,
                      namespace: str,
                      s3_endpoint: str,
                      s3_bucket: str,
                      access_key_id: str,
                      secret_access_key: str,
                      restic_repo_password: str,
                      s3_pvc_capacity: str,
                      storage_class: str = "local-path",
                      access_mode: str = "ReadWriteOnce",
                      volume_snapshot_id: str = "",
                      master_snapshot_id: str = "",
                      filer_snapshot_id: str = ""
                      ):
    """
    recreate the seaweedfs PVCs for a given namespace and restore them via restic,
    before applying the app's s3 provider Argo CD application set
    """
    snapshots = {'swfs-volume-data': volume_snapshot_id,
                 'swfs-master-data': master_snapshot_id,
                 'swfs-filer-data': filer_snapshot_id}

    for swfs_pvc, snapshot_id in snapshots.items():
        # master and filer have preset smaller capacities
        if swfs_pvc == "swfs-volume-data":
            pvc_capacity = s3_pvc_capacity

        elif swfs_pvc == "swfs-master-data":
            pvc_capacity = "2Gi"

        elif swfs_pvc == "swfs-filer-data":
            pvc_capacity = "5Gi"

        recreate_pvc(argocd.k8s,
                     app,
                     swfs_pvc,
                     namespace,
                     pvc_capacity,
                     storage_class,
                     access_mode,
                     f"{app}-s3-pvc")

        # build a k8up restore file and apply it
        k8up_restore_pvc(argocd.k8s,
                         app,
                         swfs_pvc,
                         namespace,
                         s3_endpoint,
                         s3_bucket,
                         access_key_id,
                         secret_access_key,
                         restic_repo_password,
                         snapshot_id)

    # deploy the seaweedfs appset, which will use the restored PVCs above
    # ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️
    # WARNING: change this back to main when done testing
    # ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️
    ref = "add-pvc-helm-chart-for-nextcloud"
    seaweedfs_appset = (
            f"https://raw.githubusercontent.com/small-hack/argocd-apps/{ref}/"
            f"{app}/app_of_apps/s3_provider_argocd_appset.yaml")
    argocd.k8s.apply_manifests(seaweedfs_appset, argocd.namespace)

    # and finally wait for the seaweedfs helm chart app to be ready
    argocd.wait_for_app(f"{app}-seaweedfs", retry=True)


def k8up_restore_pvc(k8s_obj: K8s,
                     app: str,
                     pvc: str,
                     namespace: str,
                     s3_endpoint: str,
                     s3_bucket: str,
                     access_key_id: str,
                     secret_access_key: str,
                     restic_repo_password: str,
                     snapshot_id: str = "latest"):
    """
    builds a k8up restore manifest and applies it
    """

    # we timestamp this restore job just in case there's others around
    now = datetime.now().strftime('%Y-%m-%d-%H-%M')
    restore_dict = {'apiVersion': 'k8up.io/v1',
                    'kind': 'Restore',
                    'metadata': {
                        'name': f"{pvc}-{now}",
                        'namespace': namespace
                        },
                    'spec': {
                        'failedJobsHistoryLimit': 5,
                        'successfulJobsHistoryLimit': 1,
                        'podSecurityContext': {
                            'runAsUser': 0
                            },
                        'restoreMethod': {
                            'folder': {
                                'claimName': pvc
                                }
                            },
                        'backend': {
                            'repoPasswordSecretRef': {
                                'name': "s3-backups-credentials",
                                'key': 'resticRepoPassword'
                                },
                            's3': {
                                'endpoint': s3_endpoint,
                                'bucket': s3_bucket,
                                'accessKeyIDSecretRef': {
                                    'name': "s3-backups-credentials",
                                    'key': 'accessKeyID'
                                    },
                                'secretAccessKeySecretRef': {
                                    'name': "s3-backups-credentials",
                                    'key': 'secretAccessKey'
                                    }
                                }
                            }
                        }
                    }

    # if snapshot not passed in, restic/k8up use the latest snapshot
    if snapshot_id and snapshot_id != "latest":
        restore_dict['spec']['snapshot'] = snapshot_id
    else:
        restore_dict['spec']['snapshot'] = get_latest_snapshot(pvc,
                                                               s3_endpoint,
                                                               s3_bucket,
                                                               access_key_id,
                                                               secret_access_key,
                                                               restic_repo_password)

    # apply the k8up restore job
    k8s_obj.apply_custom_resources([restore_dict])

    # loop on check to make sure the restore is done before continuing
    check_cmd = (f"kubectl get restore -n {namespace} --no-headers -o "
                 f"custom-columns=COMPLETION:.status.finished {pvc}-{now}")
    while True:
        restore_done = subproc([check_cmd]).strip()
        log.debug(f"restore done returns {restore_done}")

        pod_cmd = (f"kubectl get pods -n {namespace} --no-headers -o "
                   f"custom-columns=NAME:.metadata.name | grep {pvc}-{now}")
        pod = subproc([pod_cmd], universal_newlines=True, shell=True)
        subproc([f"kubectl logs -n {namespace} --tail=5 {pod}"], error_ok=True)

        if restore_done != "true":
            # sleep then try again
            sleep(5)
        else:
            break


def get_latest_snapshot(pvc: str,
                        s3_endpoint: str,
                        s3_bucket: str,
                        access_key_id: str,
                        secret_access_key: str,
                        restic_repo_password: str) -> str:
    """
    gets the latest snapshot for a pvc via restic and returns the ID of it
    """
    # set restic environment variables
    env = {"PATH": environ.get("PATH"),
           "HOME": environ.get("HOME"),
           "RESTIC_REPOSITORY": f"s3:{s3_endpoint}/{s3_bucket}",
           "RESTIC_PASSWORD_COMMAND": f"echo -n '{restic_repo_password}'",
           "AWS_ACCESS_KEY_ID": access_key_id,
           "AWS_SECRET_ACCESS_KEY": secret_access_key}

    snapshots = loads(subproc(["restic snapshots --latest 1 --json"],
                              env=env))

    for snapshot in snapshots:
        # makes sure this is the snapshot for the correct path
        if pvc in snapshot["paths"][0]:
            # gets the long ID of the latest snapshot for this path
            return snapshot['id']


def restore_postgresql(k8s_obj: K8s,
                       app: str,
                       namespace: str,
                       cluster_name: str,
                       postgresql_version: float,
                       s3_endpoint: str,
                       s3_bucket: str
                       ):
    """
    restore a CNPG operator controlled postgresql cluster
    """

    restore_dict = {
            "name": cluster_name,
            "instances": 1,
            "imageName": f"ghcr.io/cloudnative-pg/postgresql:{postgresql_version}",
            "bootstrap": {
              "initdb": [],
              "recovery": {
                "source": cluster_name
                }
             },
            "certificates": {
              "server": {
                "enabled": True,
                "generate": True
                },
              "client": {
                "enabled": True,
                "generate": True
                },
              "user": {
                "enabled": True,
                "username": [app]
                }
              },
            "backup": {},
            "scheduledBackup": {},
            "externalClusters": [{
                "name": cluster_name,
                "barmanObjectStore": {
                    "destinationPath": f"s3://{s3_bucket}",
                    "endpointURL": f"https://{s3_endpoint}",
                    "s3Credentials": {
                      "accessKeyId": {
                        "name": "s3-postgres-credentials",
                        "key": "S3_USER"
                        },
                      "secretAccessKey": {
                        "name": "s3-postgres-credentials",
                        "key": "S3_PASSWORD"
                        }
                      },
                    "wal": {
                      "maxParallel": 8
                      }
                  }
                }],
            "monitoring": {
              "enablePodMonitor": False
              },
            "storage": {
              "size": "1Gi"
              },
            "testApp": {
              "enabled": False
              }
            }

    # this creates a values.yaml from restore_dict above
    values_file_name = path.join(XDG_CACHE_DIR,
                                 f'{app}_cnpg_restore_values.yaml')
    with open(values_file_name, 'w') as values_file:
        yaml.dump(restore_dict, values_file)

    release_dict = {"release_name": f"{app}-postgres-cluster",
                    "namespace": namespace,
                    "values_file": values_file_name,
                    "chart_name": "cnpg-cluster/cnpg-cluster"}
    release = Helm.chart(**release_dict)

    # this actually applies the helm chart release we've defined above
    # and waits for it to be ready
    release.install(wait=True)

    # check for cnpg recovery job and wait for it.
    # example job name: nextcloud-postgres-1-full-recovery
    recover_job = f"{cluster_name}-1-full-recovery"
    wait_cmd = (f"kubectl wait -n {namespace} --for=condition=complete "
                f"--timeout=30m job/{recover_job}")
    wait_msg = f"Waiting on cnpg recovery job: {recover_job}"
    while True:
        log.debug(wait_msg)
        res = subproc([wait_cmd], error_ok=True)
        if "NotFound" in res:
            sleep(1)
        else:
            pods = k8s_obj.get_pod_names(recover_job, namespace)
            if pods:
                tail_out = subproc([f"kubectl tail -n {namespace} {pods[0]}"])
                log.info(tail_out)
            break

    # fix backups after restore
    restore_dict['bootstrap'].pop('recovery')
    restore_dict['backup'] = {
            "barmanObjectStore": {
                "destinationPath": f"s3://{s3_bucket}",
                "endpointURL": f"https://{s3_endpoint}",
                "s3Credentials": {
                  "accessKeyId": {
                    "name": "s3-postgres-credentials",
                    "key": "S3_USER"
                    },
                  "secretAccessKey": {
                    "name": "s3-postgres-credentials",
                    "key": "S3_PASSWORD"
                    }
                  }
                },
            "retentionPolicy": "30d"}

    restore_dict['scheduledBackup'] = {
            "name": f"{app}-pg-backup",
            "spec": {
              "schedule": "0 0 0 * * *",
              "backupOwnerReference": "self",
                "cluster": {
                  "name": f"{app}-postgres"
                }
              }
            }

    # this creates a values.yaml from restore_dict above
    values_file_name = path.join(XDG_CACHE_DIR,
                                 f'{app}_cnpg_values_after_restore.yaml')
    with open(values_file_name, 'w') as values_file:
        yaml.dump(restore_dict, values_file)
    release_dict = {"release_name": f"{app}-postgres-cluster",
                    "namespace": namespace,
                    "values_file": values_file_name,
                    "chart_name": "cnpg-cluster/cnpg-cluster"}
    release = Helm.chart(**release_dict)
    release.install()


def recreate_pvc(k8s_obj: K8s,
                 app: str,
                 pvc: str,
                 namespace: str,
                 pvc_capacity: str,
                 storage_class: str = "local-path",
                 access_mode: str = "ReadWriteOnce",
                 argo_label: str = "") -> None:
    """
    builds a PVC manifest and applies it
    """
    pvc_dict = {"kind": "PersistentVolumeClaim",
                "apiVersion": "v1",
                "metadata": {
                  "name": pvc,
                  "namespace": namespace,
                  "annotations": {"k8up.io/backup": "true"}
                  },
                "spec": {
                  "storageClassName": storage_class,
                  "accessModes": [access_mode],
                  "resources": {
                    "requests": {"storage": pvc_capacity}
                    }
                  }
                }

    # apply the pvc_dict
    k8s_obj.apply_custom_resources([pvc_dict])

    # label the PVCs so Argo CD doesn't complain
    if argo_label:
        cmd = (f"kubectl label pvc -n {namespace} {pvc} "
               f"argocd.argoproj.io/instance={argo_label}")
        subproc([cmd])


def create_restic_restore_job(k8s_obj: K8s,
                              app: str,
                              pvc: str,
                              namespace: str,
                              pvc_capacity: str,
                              label: str,
                              s3_endpoint: str,
                              s3_bucket: str,
                              access_key_id: str,
                              secret_access_key: str,
                              restic_repo_password: str,
                              storage_class: str = "local-path",
                              access_mode: str = "ReadWriteOnce",
                              snapshot_id: str = "latest",
                              mount_path: str = "/config",
                              affinity_dict: dict = {},
                              tolerations_dict: dict = {}):
    """
    builds a k8up restore manifest and applies it
    """
    recreate_pvc(k8s_obj,
                 app,
                 pvc,
                 namespace,
                 pvc_capacity,
                 storage_class,
                 access_mode,
                 app)

    # if snapshot not passed in or set to "latest", use the latest snapshot
    if snapshot_id and snapshot_id != "latest":
        snapshot = snapshot_id
    else:
        snapshot = get_latest_snapshot(pvc,
                                       s3_endpoint,
                                       s3_bucket,
                                       access_key_id,
                                       secret_access_key,
                                       restic_repo_password)

    # timestamp the job, for easier finding if there's been a lot of trial/error
    now = datetime.now().strftime('%Y-%m-%d-%H-%M')

    # k8s job to run: restic restore $SNAPSHOT_ID:/data/$pvc --target $mount_path
    restore_job = {
      "apiVersion": "batch/v1",
      "kind": "Job",
      "metadata": {
        "name": f"{app}-restic-restore-{now}",
        "namespace": namespace
      },
      "spec": {
        "template": {
          "metadata": {
            "name": f"{app}-restic-restore-job",
            "namespace": namespace
          },
          "spec": {
            "volumes": [
              {
                "name": "restic-repo-password",
                "secret": {
                  "secretName": "s3-backups-credentials"
                }
              },
              {
                "name": app,
                "persistentVolumeClaim": {
                  "claimName": app
                }
              }
            ],
            "containers": [
              {
                "name": "restic-restore",
                "image": "instrumentisto/restic:latest",
                "command": [
                  "restic",
                  "restore",
                  f"{snapshot}:/data/{pvc}",
                  "--target",
                  mount_path
                ],
                "volumeMounts": [
                  {
                    "name": "restic-repo-password",
                    "readOnly": True,
                    "mountPath": "/secrets/"
                  },
                  {
                    "name": app,
                    "mountPath": mount_path
                  }
                ],
                "env": [
                  {
                    "name": "RESTIC_REPOSITORY",
                    "value": f"s3:{s3_endpoint}/{s3_bucket}"
                  },
                  {
                    "name": "RESTIC_PASSWORD_FILE",
                    "value": "/secrets/resticRepoPassword"
                  },
                  {
                    "name": "AWS_ACCESS_KEY_ID",
                    "valueFrom": {
                      "secretKeyRef": {
                        "key": "accessKeyID",
                        "name": "s3-backups-credentials"
                      }
                    }
                  },
                  {
                    "name": "AWS_SECRET_ACCESS_KEY",
                    "valueFrom": {
                      "secretKeyRef": {
                        "key": "secretAccessKey",
                        "name": "s3-backups-credentials"
                      }
                    }
                  }
                ]
              }
            ],
            "restartPolicy": "Never"
          }
        }
      }
    }

    if affinity_dict:
        restore_job['spec']['template']['spec']['affinity'] = affinity_dict

    if tolerations_dict:
        restore_job['spec']['template']['spec']['tolerations'] = tolerations_dict

    # creates the restore job
    k8s_obj.apply_custom_resources([restore_job])

    # wait for restore job to complete
    wait_cmd = (f"kubectl wait job -n {namespace} --for=condition=complete "
                f"{app}-restic-restore-{now} --timeout=15m")
    pod_cmd = (f"kubectl get pods -n {namespace} --no-headers -o "
               f"custom-columns=NAME:.metadata.name | grep {app}-restic-restore-{now}")
    log.info(wait_cmd)
    while True:
        log.debug(f"Waiting for restore job: {app}-restic-restore-{now}")
        res = subproc([wait_cmd], error_ok=True)
        log.debug(res)

        if "NotFound" in res:
            sleep(1)
        else:
            # tail the logs out for the pod if we're done
            pod = subproc([pod_cmd], universal_newlines=True, shell=True)
            subproc([f"kubectl logs -n {namespace} --tail=5 {pod}"], error_ok=True)
            break

from minio import Minio
import logging as log


def create_bucket(hostname: str, access_key: str, secret_key: str,
                  bucket_name: str) -> None:
    """
    Takes credentials and a bucket_name and creates a bucket via the minio sdk
    """
    # Create a client with the MinIO hostname, its access key and secret key.
    client = Minio(hostname, access_key=access_key, secret_key=secret_key)
    
    # Make bucket if it does not exist already
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
    else:
        log.info(f'Bucket "{bucket_name}" already exists')

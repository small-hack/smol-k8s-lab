from os import environ

nextcloud_fields = [
        "NEXTCLOUD_SMTP_PASSWORD",
        "NEXTCLOUD_S3_ACCESS_KEY",
        "NEXTCLOUD_S3_ACCESS_ID",
        "NEXTCLOUD_RESTIC_REPO_PASSWORD"
        ]

mastodon_fields = [
        "MASTODON_SMTP_PASSWORD",
        "MASTODON_S3_ACCESS_KEY",
        "MASTODON_S3_ACCESS_ID",
        "MASTODON_RESTIC_REPO_PASSWORD"
        ]

matrix_fields = ["MATRIX_SMTP_PASSWORD"]


def check_for_required_env_vars(env_var_list: list) -> None:
    # keep track of a list of stuff to prompt for
    prompt_values = []

    # iterate through list of env vars and append any missing to prompt_values
    for item in env_var_list:
        value = environ.get(item, default="")
        if not value:
            # pretty prompt by making it lower case and replacing _ with space
            prompt_values(item.lower().replace("_", " "))

    return prompt_values

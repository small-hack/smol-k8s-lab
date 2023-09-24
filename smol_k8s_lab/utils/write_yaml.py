from ruamel.yaml import YAML
from smol_k8s_lab.constants import XDG_CONFIG_FILE


yaml = YAML()


def dump_to_file(data: dict, config_file: str = XDG_CONFIG_FILE):
    """
    takes a ruamel.yaml obj and writes it back out with comments
    """
    with open(config_file, 'w') as smol_k8s_config:
        yaml.dump(data, smol_k8s_config)

from rich.syntax import Syntax
import ruamel.yaml


def syntax_highlighted_yaml(yaml_dict: dict):
    yaml = ruamel.yaml.YAML(typ=['rt', 'string'])
    return Syntax(yaml.dump_to_string(yaml_dict),
                  lexer="yaml",
                  theme="github-dark",
                  background_color="#232336")

"""
Name: help_text
Desc: the help text for smol-k8s-lab
"""
import click
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from .env_config import VERSION, XDG_CONFIG_DIR


RECORD = False


def pretty_choices(default_list):
    """
    Takes a list of default choices and surrounds them with a meta markup tag
    and join them with a comma for a pretty return "Choices" string.
    Example: pretty_choices(['beep', 'boop']) returns:
             'Choices: [meta]beep[/meta], [meta]boop[/meta]'
    """
    defaults = '[/meta], [meta]'.join(default_list)
    return 'Choices: [meta]' + defaults + '[/meta]'


def options_help():
    """
    Help text for all the options/switches for main()
    Returns a dict.
    """
    logging_choices = pretty_choices(['debug', 'info', 'warn', 'error'])

    return {
        'argo':
        'Install Argo CD as part of this script. Default: False',

        'config':
        'Full path and name of yml to parse.\n Defaults to '
        f'[light_steel_blue]{XDG_CONFIG_DIR}[/]',

        'delete':
        'Delete the existing cluster.',

        'extras':
        'Install/update extra tools such as kubectl, krew, k9s, helm, and '
        'more via brew.',

        'external_secret_operator':
        'Install the external secrets operator to pull secrets from somewhere '
        'else, so far only supporting gitlab.',

        'k9s':
        'Run k9s as soon as this script is complete. Default: False',

        'kyverno':
        'beta. Install kyverno, a k8s native policy manager. Default: False',

        'log_level':
        f'Logging level. {logging_choices} Default: [meta]info[/meta].',

        'log_file':
        'File to log to. Default: None',

        'password_manager':
        'Store generated admin passwords directly into your password manager.'
        'Only Bitwarden currently supported. Requires you to manually enter '
        'your vault password. Default: False',

        'version':
        f'Print the version of smol-k8s-lab (v{VERSION})'
        }


class RichCommand(click.Command):
    """
    Override Clicks help with a Rich-er version.

    This is from the Textualize/rich-cli project, link here:
        https://github.com/Textualize/rich-cli
    """

    def format_help(self, ctx, formatter):

        class OptionHighlighter(RegexHighlighter):
            highlights = [r"(?P<switch>\-\w)",
                          r"(?P<option>\-\-[\w\-]+)",
                          r"(?P<unstable>[b][e][t][a])",
                          r"(?P<skl_title>[s][m][o][l]\-[k][8][s]\-[l][a][b])"]

        highlighter = OptionHighlighter()

        console = Console(theme=Theme({"option": "light_slate_blue",
                                       "switch": "sky_blue2",
                                       "meta": "light_steel_blue",
                                       "skl_title": "cornflower_blue"}),
                          highlighter=highlighter, record=RECORD)

        title = "☁️  [cornflower_blue][i]smol k8s lab[/] 🧸\n"
        desc = ("[steel_blue]Quickly install a k8s distro for a lab setup."
                "\n[i]Installs:[/i] metallb, nginx-ingess-controller, cert-"
                "manager\n[i]Optional Installs:[/i] Argo CD, kynervo, "
                "external secrets operator.\n")

        console.print(title + desc, justify="center")

        console.print("[steel_blue]Usage:[/] smol-k8s-lab "
                      "[meta]<k0s, k3s, kind>[meta/] [option][OPTIONS]\n")

        options_table = Table(highlight=True, box=None, show_header=False,
                              row_styles=["dim", ""],
                              padding=(1, 1, 0, 0))

        for param in self.get_params(ctx)[1:]:

            if len(param.opts) == 2:
                opt1 = highlighter(param.opts[1])
                opt2 = highlighter(param.opts[0])
            else:
                opt2 = highlighter(param.opts[0])
                opt1 = Text("")

            if param.metavar:
                opt2 += Text(f" {param.metavar}",
                             style="bold light_steel_blue")

            options = Text(" ".join(reversed(param.opts)))
            help_record = param.get_help_record(ctx)
            if help_record is None:
                help = ""
            else:
                help = Text.from_markup(param.get_help_record(ctx)[-1],
                                        emoji=False)

            if param.metavar:
                options += f" {param.metavar}"

            if "help" in opt1:
                opt1 = "-h"
                opt2 = "--help"

            options_table.add_row(opt1, opt2, highlighter(help))

        url = ("♥ [link=https://jessebot.github.io/smol-k8s-lab]"
               "jessebot.github.io/smol-k8s-lab[/link]")
        console.print(Panel(options_table,
                            border_style="light_steel_blue",
                            title="ʕ ᵔᴥᵔʔ Options",
                            title_align="left",
                            subtitle_align="right",
                            subtitle=url))

        # I use this to print a pretty svg at the end sometimes
        if RECORD:
            console.save_svg("docs/screenshots/help_text.svg")

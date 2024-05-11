"""
Name: help_text
Desc: the help text for smol-k8s-lab
"""
import click
from os import environ
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from smol_k8s_lab.constants import VERSION, XDG_CONFIG_FILE


RECORD = environ.get("SMOL_SCREENSHOT", False)


def pretty_choices(default_list: list):
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
    help_dict = {
        'delete':
        'Delete an existing cluster by name.',

        'interactive':
        '⚙️ Interactively configures smol-k8s-lab',

        'command':
        'Run command immediately after smol-k8s-lab before main cli phase',

        'version':
        f'Print the version of smol-k8s-lab (v{VERSION})'
        }

    if RECORD:
        help_dict['config'] = (
        'Full path and name of the YAML config file to parse.\nDefaults to '
        '[light_steel_blue]$XDG_CONFIG_HOME/smol-k8s-lab/config.yaml[/]'
        )
    else:
        help_dict['config'] = (
        'Full path and name of the YAML config file to parse.\nDefaults to '
        f'[light_steel_blue]{XDG_CONFIG_FILE}[/]'
        )

    return help_dict


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

        title =" 🧸[cornflower_blue]smol k8s lab[/]\n"
        desc = ("\n[steel_blue][i]Install slim Kubernetes distros + plus all your "
                "apps via Argo CD.\n")

        console.print(title + desc, justify="center")

        console.print("[steel_blue]Usage:[/] smol-k8s-lab [option][OPTIONS]\n")

        options_table = Table(highlight=True, box=None, show_header=False,
                              row_styles=["", "dim"],
                              padding=(1, 1, 0, 0))

        for param in self.get_params(ctx):

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

        url = ("♥ docs: [link=https://small-hack.github.io/smol-k8s-lab]"
               "https://small-hack.github.io/smol-k8s-lab[/link]")
        console.print(Panel(options_table,
                            border_style="light_steel_blue",
                            title="ʕ ᵔᴥᵔʔ Options",
                            title_align="left",
                            subtitle_align="right",
                            subtitle=url))

        # I use this to print a pretty svg at the end sometimes
        if RECORD:
            console.save_svg("docs/assets/images/screenshots/help_text.svg", title="term")

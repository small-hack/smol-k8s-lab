from argparse import ArgumentParser
import click
from rich import print
from rich import console
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.progress import track
from rich.table import Table
from rich.text import Text
from rich.theme import Theme


class RichCommand(click.Command):
    """
    Override Clicks help with a Richer version.

    This is from the Textualize/rich-cli project on github.com, link here:
    github.com/Textualize/rich-cli/blob/
    53cb0e9f8ddcfccafc2073a05370928fed2bb8b9/src/rich_cli/__main__.py#L163
    """

    def format_help(self, ctx, formatter):

        class OptionHighlighter(RegexHighlighter):
            highlights = [r"(?P<switch>\-\w)",
                          r"(?P<option>\-\-[\w\-]+)"]

        highlighter = OptionHighlighter()

        console = Console(theme=Theme({"option": "bold cyan",
                                       "switch": "bold green"}),
                          highlighter=highlighter)

        header = (f"[b]Smol K8s Lab[/b]\n\n[dim]Quickly install a k8s distro "
                  "for a lab setup. Installs k3s with metallb, "
                  "nginx-ingess-controller, cert-manager, and argocd")

        console.print(header, justify="center")

        console.print("Usage: [b]smol-k8s-lab.py[/b] [b cyan]<k3s,kind> " +
                      "[b][OPTIONS][/] \n")

        options_table = Table(highlight=True, box=None, show_header=False)

        for param in self.get_params(ctx)[1:]:

            if len(param.opts) == 2:
                opt1 = highlighter(param.opts[1])
                opt2 = highlighter(param.opts[0])
            else:
                opt2 = highlighter(param.opts[0])
                opt1 = Text("")

            if param.metavar:
                opt2 += Text(f" {param.metavar}", style="bold yellow")

            options = Text(" ".join(reversed(param.opts)))
            help_record = param.get_help_record(ctx)
            if help_record is None:
                help = ""
            else:
                help = Text.from_markup(param.get_help_record(ctx)[-1],
                                        emoji=False)

            if param.metavar:
                options += f" {param.metavar}"

            options_table.add_row(opt1, opt2, highlighter(help))

        console.print(Panel(options_table, border_style="dim", title="Options",
                            title_align="left"))

        console.print("♥ formatting from https://www.textualize.io",
                      justify="left", style="bold")


k9_help = 'Run k9s as soon as this script is complete, defaults to False'
a_help = 'Install Argo CD as part of this script, defaults to False'
f_help = 'Full path and name of yml to parse, e.g. -f /tmp/config.yml'
k_help = ('distribution of kubernete to install: k3s or kind. k0s coming soon')
d_help = 'Delete the existing cluster, REQUIRES -k/--k8s [k3s|kind]'
s_help = 'Install bitnami sealed secrets, defaults to False'
p_help = ('Store generated admin passwords directly into your password manager'
          '. Right now, this defaults to Bitwarden and requires you to input '
          'your vault password to unlock the vault temporarily.')
e_help = ('Install the external secrets operator to pull secrets from '
          'somewhere else, so far only supporting gitlab')

@click.command(cls=RichCommand)
@click.argument("k8s_distro", metavar="<k3s OR kind>", default="")
@click.option( "-a", "--argo", is_flag=True, help=a_help)
@click.option('-d', '--delete', is_flag=True, help=d_help)
@click.option('-e', '--external_secret_operator', help=e_help)
@click.option('-f', '--file', metavar="TEXT", default='./config.yml',
              help=f_help)
@click.option('-k', '--k9s', help=k9_help)
@click.option('-p', '--password_manager', help=p_help)
@click.option('-s', '--sealed_secrets', help=s_help)
def main(argo: bool = False,
         delete: bool = False,
         external_secret_operator: bool = False,
         file: str = "",
         k9s: bool = False,
         password_manager: bool = False,
         sealed_secrets: bool = False):
    """
    console output stuff
    """
    def print_usage() -> None:
        console.print("Usage: [b]smol-k8s-lab.py[/b] [b cyan]<k3s,kind> " +
                      "[b][OPTIONS][/] \n")
        console.print("See [bold green]smol-k8s-lab.py --help[/] for options")
        console.print()
        sys.exit(0)

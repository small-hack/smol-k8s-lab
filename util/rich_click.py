# file for rich printing
import click
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme


class RichCommand(click.Command):
    """
    Override Clicks help with a Rich-er version.

    This is from the Textualize/rich-cli project, link here:
        https://github.com/Textualize/rich-cli
    """

    def format_help(self, ctx, formatter):

        class OptionHighlighter(RegexHighlighter):
            highlights = [r"(?P<switch>\-\w)",
                          r"(?P<option>\-\-[\w\-]+)"]

        highlighter = OptionHighlighter()

        console = Console(theme=Theme({"option": "cornflower_blue",
                                       "switch": "light_sky_blue1"}),
                          highlighter=highlighter, record=True)

        title = "☁️  [cornflower_blue][i]smol k8s lab[/] 🧸 \n"
        desc = ("[steel_blue]Quickly install a k8s distro for a lab setup."
                "\n[i]Installs:[/i] metallb, nginx-ingess-controller, cert-"
                "manager\n[i]Optionally Installed:[/i] Argo CD, kynervo, "
                "external secrets operator.")

        console.print(title + desc, justify="center")

        console.print("\n[b]Usage[/b]: smol-k8s-lab [cornflower_blue]" +
                      "<k3s OR kind> [royal_blue1][OPTIONS]\n")

        options_table = Table(highlight=True, box=None, show_header=False,
                              row_styles=["", "dim"],
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

            options_table.add_row(opt1, opt2, highlighter(help))

        url = "♥ https://jessebot.github.io/smol_k8s_lab/"
        console.print(Panel(options_table,
                            border_style="dim light_steel_blue",
                            title="ʕ ᵔᴥᵔʔ Options",
                            title_align="left",
                            subtitle_align="right",
                            subtitle=url))
        # I use this to print a pretty svg at the end sometimes
        console.save_svg("docs/screenshots/help_text.svg")

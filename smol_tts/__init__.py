from .constants import DEFAULT_SAVE_PATH

# external libs
import click
from click import option, command, Choice
from os import environ
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme


# Get device and decide if we're using the GPU for this
HELP_SETTINGS = dict(help_option_names=["-h", "--help"])
RECORD = environ.get("SMOL_SCREENSHOT", False)


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

        title ="🗣️ [cornflower_blue]smol-tts[/]\n"
        desc = ("\n[steel_blue][i]An internal tool for smol-k8s-lab to update the current text to speech audio files and print how long it took[/i][/steel_blue]\n")

        console.print(title + desc, justify="center")

        console.print("[steel_blue]Usage:[/] smol-tts [option][OPTIONS]\n")

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
            console.save_svg("docs/assets/images/screenshots/smol_tts_help_text.svg",
                             title="term")


# an ugly list of decorators, but these are the opts/args for the whole script
@command(cls=RichCommand, context_settings=HELP_SETTINGS)
@option("--category", "-c",
        metavar="CATEGORY",
        type=Choice(
            ["all", "apps", "cluster_names", "numbers","phrases", "screens"],
            case_sensitive=False
            ),
        help='category of text to generate audio files for')
@option("--language", "-l",
        metavar="LANGUAGE",
        type=Choice(["all", "en", "nl"], case_sensitive=False),
        required=True,
        help='2 character language')
@option("--save_path", "-s",
        metavar="PATH",
        default=DEFAULT_SAVE_PATH,
        type=str,
        help="override the default path to save generated audio files to")
def tts_gen(category: str = "", language: str = "", save_path: str = ""):
    """
    regenerate TTS audio files and report how long it took
    """
    if language:
        # internal libs
        from .audio_generation import AudioGenerator
        import asyncio
        import time

        # start the timer
        s = time.perf_counter()

        print(f"💾 Saving files to {save_path}")
        lang_obj = AudioGenerator(languages=language,
                                  category=category,
                                  save_path=save_path)
        asyncio.run(lang_obj.process_all_languages())

        # print how long everything took
        elapsed = time.perf_counter() - s
        print(f"⏱️ smol-tts executed in {elapsed:0.2f} seconds.")


if __name__ == "__main__":
    tts_gen()

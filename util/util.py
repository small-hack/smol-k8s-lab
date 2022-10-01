#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
some pretty printing of the help :)
"""
from time import sleep
# this is for rich text, to pretty print things
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from .subproc_wrapper import subproc


CONSOLE = Console()


def header(text, header=True):
    """
    pretty print a header
    """
    print('\n')
    title = '☁ [cornflower_blue]₍ᐢ•ﻌ•ᐢ₎ ♥  ૮ ・ﻌ・ა  ♥  ʕᵔᴥᵔ ʔ[/] ☁'
    print(Panel(text, title=title))
    print('\n')


def simple_loading_bar(seconds=3, command=''):
    """
    prints a small loading bar using rich
    """
    print('\n')
    for i in track(range(1), description="Processing..."):
        # loops until this succeeds
        while True:
            try:
                subproc(command)
            except Exception as reason:
                print(f"Hmmm, that didn't work because: {reason}")
                sleep(seconds)
                continue
            # execute if no exception
            else:
                seconds = 0
                break
    print('\n')
    return

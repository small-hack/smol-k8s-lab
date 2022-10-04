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


def header(text):
    """
    pretty print a header
    """
    print('\n')
    title = f'☁ ₍ᐢ•ﻌ•ᐢ₎ [cyan]{text}[/] ʕᵔᴥᵔ ʔ ☁ '
    CONSOLE.rule(title, style="cornflower_blue")
    print('')


def simple_loading_bar(seconds=5, command=''):
    """
    prints a small loading bar using rich
    """
    print('\n')
    not_completed = True

    for i in track(range(seconds), description="Processing..."):
        # loops until this succeeds
        while not_completed:
            try:
                subproc([command])
            except Exception as reason:
                print(f"Hmmm, that didn't work because: {reason}")
                sleep(seconds)
                continue
            # execute if no exception
            else:
                not_completed = False
                seconds = 0
                break
    print('\n')
    return

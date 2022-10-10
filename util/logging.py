#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
some pretty printing of the help :)
"""
from time import sleep
# this is for rich text, to pretty print things
from rich import print
from rich.console import Console
from rich.progress import Progress
from .subproc_wrapper import subproc


CONSOLE = Console()


def header(text):
    """
    pretty print a header with lines extending the full width of the terminal
    """
    print('\n')
    title = f'☁ ₍ᐢ•ﻌ•ᐢ₎ [cyan]{text}[/] ʕᵔᴥᵔ ʔ ☁ '
    CONSOLE.rule(title, style="cornflower_blue")
    print('')


def sub_header(text):
    """
    pretty print a SUB header
    """
    print('\n')
    title = f'[dim]☁  {text} ☁ [/dim]'
    CONSOLE.print(title, justify="center")
    print('')


def simple_loading_bar(command=''):
    """
    prints a small loading bar using rich
    """
    total_steps = 15
    with Progress(transient=True) as progress:
        task1 = progress.add_task("[green]Processing...", total=total_steps)
        while not progress.finished:
            sleep(1)
            progress.update(task1, advance=3)
            total_steps -= 3
            # loops until this succeeds
            try:
                subproc([command])
            except Exception as reason:
                print(f"Hmmm, that didn't work because: {reason}")
                sleep(3)
                progress.update(task1, advance=3)
                total_steps -= 3
                continue
            # execute if no exception
            else:
                progress.update(task1, advance=total_steps)
                sleep(.1)
                break
    print('')
    return

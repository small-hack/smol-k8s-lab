#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
some pretty printing of the help :)
"""
import logging
# this is for rich text, to pretty print things
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.logging import RichHandler
# custom lib
from .subproc_wrapper import subproc
from time import sleep
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")

# for console logging only
CONSOLE = Console()


def header(text):
    """
    pretty print a header with lines extending the full width of the terminal
    """
    print('\n')
    title = f'[b]☁ ૮ ・ﻌ・ა[/] [cyan]{text}[/cyan] [b]ʕᵔᴥᵔ ʔ ☁ [/]'
    CONSOLE.rule(title, style="cornflower_blue")
    print('')


def sub_header(text, extra_starting_blank_line=True):
    """
    pretty print a SUB header
    """
    if extra_starting_blank_line:
        print('\n')
    else:
        print('')
    title = f'[dim]☁  {text} ☁ [/dim]'
    CONSOLE.print(title, justify="center")
    print('')


def simple_loading_bar(tasks={}):
    """
    Prints a small loading bar using rich.
    Accepts a dict of {"task_name": "task"}
    example: {'Installing custom resource', 'kubectl apply -f thing.yml'}

    read more here:
        https://rich.readthedocs.io/en/stable/progress.html
    """
    for task_name, task_command in tasks.items():
        total_steps = 45
        with Progress(transient=True) as progress:
            task1 = progress.add_task(f"[green]{task_name}...",
                                      total=total_steps)
            while not progress.finished:
                sleep(1)
                progress.update(task1, advance=3)
                total_steps -= 3
                # loops until this succeeds
                try:
                    subproc([task_command], False, True, False)
                except Exception as reason:
                    log.debug(f"Encountered Exception: {reason}")
                    sleep(3)
                    progress.update(task1, advance=3)
                    total_steps -= 3
                    continue
                # execute if no exception
                else:
                    progress.update(task1, completed=15)
                    sleep(.1)
                    break
    print('')
    return

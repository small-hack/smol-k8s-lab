#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
some pretty printing of the help :)
"""
import logging as log
# this is for rich text, to pretty print things
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from rich.theme import Theme
from time import sleep
# custom lib
from .subproc import subproc


# for console logging only
CONSOLE = Console(theme=Theme({"warn": "bold yellow",
                               "grn": "medium_spring_green",
                               "ohno": "magenta"}))


def header(text):
    """
    pretty print a header with lines extending the full width of the terminal
    """
    print('\n')
    title = f'[b]☁  [/]૮ ・ﻌ・ა [cyan]{text}[/cyan] ʕᵔᴥᵔ ʔ [b]☁ [/]'
    CONSOLE.rule(title, style="cornflower_blue")
    print('')
    return


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
    return


def print_msg(text='', alignment='center', style='dim italic'):
    """
    prints text centered in the width of the terminal
    """
    CONSOLE.print(text, justify=alignment, style=style)
    return


def simple_loading_bar(tasks={}, time_to_wait=120):
    """
    Prints a small loading bar using rich.
    Accepts a dict of {"task_name": "task"}
    example: {'Installing custom resource', 'kubectl apply -f thing.yml'}

    read more here:
        https://rich.readthedocs.io/en/stable/progress.html
    """
    for task_name, task_command in tasks.items():
        with Progress(transient=True) as progress:
            task1 = progress.add_task(f"[green]{task_name}...",
                                      total=time_to_wait)
            while not progress.finished:
                sleep(1)
                progress.update(task1, advance=2)
                # loops until this succeeds
                try:
                    subproc([task_command], spinner=False)
                except Exception as reason:
                    log.debug(f"Encountered Exception: {reason}")
                    sleep(3)
                    progress.update(task1, advance=2)
                    continue
                # execute if no exception
                else:
                    progress.update(task1, completed=time_to_wait)
                    sleep(.1)
                    break
    print('')
    return


def print_panel(content='', title_txt='', title_alignment='center',
                border_style="light_steel_blue"):
    """
    prints text in a box with a light_steel_blue1 border and title_txt
    """
    print('')
    panel = Panel(content, title=title_txt, title_align=title_alignment,
                  border_style=border_style)
    CONSOLE.print(panel)
    return

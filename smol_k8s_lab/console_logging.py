#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
some pretty printing of the help :)
"""
# this is for rich text, to pretty print things
from rich import print
from rich.console import Console
from rich.panel import Panel
# from rich.table import Table
from rich.theme import Theme


# this is for rich text, to pretty print things
soft_theme = Theme({"info": "dim cornflower_blue",
                    "grn": "medium_spring_green",
                    "warn": "yellow on black",
                    "danger": "bold magenta",
                    "ohno": "pale_violet_red1"})
CONSOLE = Console(theme=soft_theme)


def header(text):
    """
    pretty print a header with lines extending the full width of the terminal
    """
    print('\n')
    title = f'[b]☁  [/]ʕ ᵔﻌᵔʔ [cyan]{text}[/cyan] ʕᵔﻌᵔ ʔ [b]☁ [/]'
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

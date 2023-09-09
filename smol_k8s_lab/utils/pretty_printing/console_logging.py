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


def header(text: str, emoji: str = ""):
    """
    pretty print a header with lines extending the full width of the terminal
    Accepts optional emoji to use to surround header text
    """
    print('\n')
    if emoji:
        title = f'{emoji} [cyan]{text}[/cyan] {emoji}'
    else:
        title = f'[b]☁  [/]ʕ ᵔﻌᵔʔ [cyan]{text}[/cyan] ʕᵔﻌᵔ ʔ [b]☁ [/]'
    CONSOLE.rule(title, style="cornflower_blue")
    print('')

    return True


def sub_header(text: str,
               extra_starting_blank_line: bool = True,
               ending_blank_line: bool = True):
    """
    pretty print a SUB header. params:
      text                      - "", text to pretty print. REQUIRED.
      extra_starting_blank_line - True, optionally print 2 new lines at start
      ending_blank_line         - True, optionally print 1 new line at end
    """
    if extra_starting_blank_line:
        print('\n')
    else:
        print('')

    title = f'[dim]☁  {text} ☁ [/dim]'
    CONSOLE.print(title, justify="center")

    if ending_blank_line:
        print('')

    return


def print_msg(text: str,
              alignment: str = 'center',
              style: str = 'dim italic'):
    """
    prints text centered in the width of the terminal
    """
    CONSOLE.print(text, justify=alignment, style=style)

    return True


def print_panel(content: str,
                title_txt: str = '',
                title_alignment: str = 'center',
                border_style: str = "light_steel_blue"):
    """
    prints text in a box with a light_steel_blue border and title_txt
    """
    print('')
    panel = Panel(content, title=title_txt, title_align=title_alignment,
                  border_style=border_style)
    CONSOLE.print(panel)

    return True

#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
some pretty printing of the help :)
"""
import subprocess
from time import sleep
# this is for rich text, to pretty print things
from rich.console import Console
from rich.panel import Panel
from rich.progress import track


CONSOLE = Console()


def header(text, header=True):
    """
    pretty print a header
    """
    print('\n')
    if header:
        print(Panel(text, title='[green]♡ ₍ᐢ•ﻌ•ᐢ₎  ♥  ૮ ・ﻌ・ა  ♥  ʕᵔᴥᵔ ʔ ♡'))
    else:
        CONSOLE.rule(f"[green]♥ {text} ♥")
    print('\n')


def simple_loading_bar(seconds=3, command=''):
    """
    prints a small loading bar using rich
    """
    print('\n')
    for i in track(range(5), description="Processing..."):
        # loops until this succeeds
        while True:
            try:
                sub_proc(command)
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


def sub_proc(command="", error_ok=False, print_output=True):
    """
    Takes a str commmand to run in BASH, as well as optionals bools to pass on
    errors in stderr/stdout and suppress_output
    """
    if print_output:
        print('')
        print(f'\n\033[92m Running cmd:\033[00m {command}')
    cmd = command.split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = p.returncode
    res = p.communicate()
    res_stdout = '  ' + res[0].decode('UTF-8').replace('\n', '\n  ')
    res_stderr = '  ' + res[1].decode('UTF-8').replace('\n', '\n  ')

    if not error_ok:
        # check return code, raise error if failure
        if not return_code or return_code != 0:
            # also scan both stdout and stdin for weird errors
            for output in [res_stdout.lower(), res_stderr.lower()]:
                if 'error' in output:
                    err = f'Return code not zero! Return code: {return_code}'
                    # this just prints the error in red
                    raise Exception(f'\033[0;33m {err} \n {output} \033[00m')

    for output in [res_stdout, res_stderr]:
        if output:
            if print_output:
                print(output.rstrip())
            return output

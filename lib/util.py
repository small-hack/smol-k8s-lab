#!/usr/bin/env python3
"""
AUTHOR: @jessebot email: jessebot(AT)linux(d0t)com
these are just some quick utilities we'll need to move quickly
"""
import subprocess
from time import sleep


def header(text, header=True):
    """
    pretty print a header
    """
    print('')
    if header:
        print('♡ ₍ᐢ•ﻌ•ᐢ₎  ♥  ૮ ・ﻌ・ა  ♥  ʕᵔᴥᵔ ʔ ♡'.center(80, ' '))
        print('-'.center(80, '-'))
        print(f"\033[92m❤︎ {text} ❤︎\033[00m".center(80, ' '))
    else:
        print(f"\033[92m{text}\033[00m".center(80, ' '))
    print('')


def simple_loading_bar(seconds):
    """
    prints a little heart for int(seconds)
    """
    for second in range(seconds):
        print("\033[92m❤︎\033[00m".center(80), end=" ")
        sleep(1)
    print('')


def sub_proc(command="", error_ok=False):
    """
    Takes a str commmand to run in BASH, as well as optionals bools to pass on
    errors in stderr/stdout and suppress_output
    """
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
            print(output.rstrip())
            return output

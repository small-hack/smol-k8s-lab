"""
Using Textualize's rich library to pretty print subprocess outputs,
so during long running commands, the user isn't wondering what's going on,
even if you don't actually output anything from stdout/stderr of the command.
"""
import logging as log
from subprocess import Popen, PIPE
from rich.console import Console
from rich.theme import Theme
from os import environ


soft_theme = Theme({"info": "dim cornflower_blue",
                    "warn": "bold black on yellow",
                    "danger": "bold magenta"})
console = Console(theme=soft_theme)


def basic_syntax(bash_string=""):
    """
    splits up a string and does some basic syntax highlighting
    """
    parts = bash_string.split(' ')
    base_cmd = f'[magenta]{parts[0]}[/magenta]'
    if len(parts) == 1:
        return base_cmd
    else:
        bash_string = bash_string.replace(parts[0], base_cmd)
        bash_string = bash_string.replace(parts[1],
                                          f'[yellow]{parts[1]}[/yellow]')
        return bash_string


def subproc(commands=[], error_ok=False, output=True, spinner="aesthetic",
            env={}):
    """
    Takes a list of command strings to run in subprocess
    Optional vars - default, description:
         error_ok -   False, catch errors, defaults to False
         output   -   True,  output anything form stderr, or stdout
         spinner  -   True,  show an animated progress spinner
         env      -   {},    key = name of env var, value = value of env var
    """
    # if certain env vars needed when running, otherwise we pass in defaults
    env_vars = environ.copy()
    if env:
        env_vars = env_vars.update(env)

    for cmd in commands:
        # do some very basic syntax highlighting
        printed_cmd = basic_syntax(cmd)
        if output:
            status_line = "[green] Running:[/green] "
            # make sure I'm not about to print a password, oof
            if 'password' not in cmd.lower():
                status_line += printed_cmd
            else:
                status_line += printed_cmd.split('assword')[0] + \
                    'assword[warn]:warning: TRUNCATED'
        else:
            cmd_parts = printed_cmd.split(' ')
            msg = '[green]Running [i]secret[/i] command:[b] ' + cmd_parts[0]
            status_line = " ".join([msg, cmd_parts[1], '[dim]...'])
        status_line += '\n'

        log.info(status_line, extra={"markup": True})
        # Sometimes we need to not use a little loading bar
        if not spinner:
            output = run_subprocess(cmd, error_ok, output, env_vars)
        else:
            with console.status(status_line,
                                spinner=spinner,
                                speed=0.75) as status:
                output = run_subprocess(cmd, error_ok, output, env_vars)

    return output


def run_subprocess(cmd="", error_ok=False, output=True, env_vars={}):
    """
    Takes a str commmand to run in BASH in a subprocess.
    Typically run from subproc, which handles output printing

    Optional vars:
        env_vars - dict, environmental variables for shell
        error_ok - bool, catch errors, defaults to False
    """
    try:
        p = Popen(cmd.split(), env=env_vars, stdout=PIPE, stderr=PIPE)
        res = p.communicate()
    except Exception as e:
        log.error(str(e))
    return_code = p.returncode
    res_stdout, res_stderr = res[0].decode('UTF-8'), res[1].decode('UTF-8')
    if output:
        log.info(res_stdout)

    # check return code, raise error if failure
    if not return_code or return_code != 0:
        # also scan both stdout and stdin for weird errors
        for output in [res_stdout.lower(), res_stderr.lower()]:
            if 'error' in output:
                err = f'Return code: "{str(return_code)}". Expected code is 0.'
                error_msg = f'\033[0;33m{err}\n{output}\033[00m'
                if error_ok:
                    log.error(error_msg)
                else:
                    raise Exception(error_msg)

    # sometimes stderr is empty, but sometimes stdout is empty
    for output in [res_stdout, res_stderr]:
        if output:
            return output

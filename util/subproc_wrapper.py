"""
Using Textualize's rich library to pretty print subprocess outputs,
so during long running commands, the user isn't wondering what's going on,
even if you don't actually output anything from stdout/stderr of the command.
"""
import subprocess
from rich import print
from rich.console import Console
from os import environ


console = Console()


def subproc(commands=[], error_ok=False, suppress_output=False, spinner=True,
            env={}):
    """
    Takes a list of command strings to run in subprocess
    Optional vars:
        error_ok        - bool, catch errors, defaults to False
        suppress_output - bool, don't output anything form stderr, or stdout
        spinner         - bool, show an animated progress spinner
        env             - dict, key = name of env var, value = value of env var
    """
    # if certain env vars needed when running, otherwise we pass in defaults
    env_vars = environ.copy()
    if env:
        env_vars = env_vars.update(env)

    # Sometimes we need to not use a little loading bar
    if not spinner:
        for command in commands:
            output = run_subprocess(command, env_vars, error_ok)
            if output:
                if not suppress_output:
                    print('')
                    print(output)
    else:
        for command in commands:
            print('')
            status_line = f"[bold green]Running cmd:[/bold green] {command}"
            with console.status(status_line) as status:
                output = run_subprocess(command, env_vars, error_ok)
                if output:
                    if not suppress_output:
                        print('')
                        print(output)
    return output


def run_subprocess(command="", env_vars={}, error_ok=False):
    """
    Takes a str commmand to run in BASH in a subprocess.
    Typically run from subproc, which handles output printing

    Optional vars:
        error_ok - bool, catch errors, defaults to False
    """
    # subprocess expects a list
    cmd = command.split()
    p = subprocess.Popen(cmd,
                         env=env_vars,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = p.returncode
    res = p.communicate()
    res_stdout = res[0].decode('UTF-8')
    res_stderr = res[1].decode('UTF-8')

    if not error_ok:
        # check return code, raise error if failure
        if not return_code or return_code != 0:
            # also scan both stdout and stdin for weird errors
            for output in [res_stdout.lower(), res_stderr.lower()]:
                if 'error' in output:
                    err = ('Return code not zero! Return code: ' + return_code)
                    raise Exception(f'\033[0;33m {err} \n {output} '
                                    '\033[00m')

    # sometimes stderr is empty, but sometimes stdout is empty
    for output in [res_stdout, res_stderr]:
        if output:
            return output

"""
Using Textualize's rich library to pretty print subprocess outputs,
so during long running commands, the user isn't wondering what's going on,
even if you don't actually output anything from stdout/stderr of the command.
"""
import logging
from subprocess import Popen, PIPE
from rich.console import Console
from rich.logging import RichHandler
from os import environ


# console logging
console = Console()
# all logging
FORMAT = "%(message)s"
logging.basicConfig(level="INFO", format=FORMAT, datefmt="[%X]",
                    handlers=[RichHandler()])
log = logging.getLogger("rich")


def subproc(commands=[], error_ok=False, output=True, spinner=True,
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
        if output:
            status_line = "[green]Running Command:[/green] "
            # make sure I'm not about to print a password, oof
            if 'password' not in cmd.lower():
                status_line += cmd
            else:
                status_line += cmd.split('assword')[0] + 'assword!truncated'
        else:
            cmd_parts = cmd.split(' ')
            secret_cmd = " ".join([cmd_parts[0], cmd_parts[1]])
            status_line = (f'[green]Running a [b]secret [dim]{secret_cmd}[/b]'
                           '[/dim] command.')
        status_line += '\n'

        log.info(status_line, extra={"markup": True})
        # Sometimes we need to not use a little loading bar
        if not spinner:
            output = run_subprocess(cmd, env_vars, error_ok, output)
        else:
            with console.status(status_line) as status:
                output = run_subprocess(cmd, env_vars, error_ok, output)

    return output


def run_subprocess(cmd="", env_vars={}, error_ok=False, output=True):
    """
    Takes a str commmand to run in BASH in a subprocess.
    Typically run from subproc, which handles output printing

    Optional vars:
        env_vars - dict, environmental variables for shell
        error_ok - bool, catch errors, defaults to False
    """
    p = Popen(cmd.split(), env=env_vars, stdout=PIPE, stderr=PIPE)
    res = p.communicate()
    return_code = p.returncode
    res_stdout, res_stderr = res[0].decode('UTF-8'), res[1].decode('UTF-8')
    if output:
        log.info(res_stdout)

    # check return code, raise error if failure
    if not return_code or return_code != 0:
        # also scan both stdout and stdin for weird errors
        for output in [res_stdout.lower(), res_stderr.lower()]:
            if 'error' in output:
                err = ('Return code not zero! ' +
                       f'Return code: {str(return_code)}')
                error_msg = f'\033[0;33m{err}\n{output}\033[00m'
                if error_ok:
                    log.error(error_msg)
                else:
                    raise Exception(error_msg)

    # sometimes stderr is empty, but sometimes stdout is empty
    for output in [res_stdout, res_stderr]:
        if output:
            return output

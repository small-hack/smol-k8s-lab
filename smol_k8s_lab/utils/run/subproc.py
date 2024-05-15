"""
Using Textualize's rich library to pretty print subprocess outputs,
so during long running commands, the user isn't wondering what's going on,
even if you don't actually output anything from stdout/stderr of the command.
"""
import logging as log
from subprocess import Popen, PIPE
import re
from rich.console import Console
from rich.markup import MarkupError
from rich.theme import Theme
from rich.progress import Progress
from time import sleep


soft_theme = Theme({"info": "dim cornflower_blue",
                    "warn": "bold black on yellow",
                    "danger": "bold magenta"})
console = Console(theme=soft_theme)


def basic_syntax(bash_string: str):
    """
    splits up a string and does some basic syntax highlighting
    """
    parts = bash_string.split(' ')
    base_cmd = f'[yellow]{parts[0]}[/yellow]'
    if len(parts) == 1:
        return base_cmd
    else:
        bash_string = bash_string.replace(parts[0], base_cmd, 1)
        formatted_str = f'[cornflower_blue]{parts[1]}[/cornflower_blue]'
        bash_string = bash_string.replace(parts[1], formatted_str, 1)
        return bash_string


def subproc(commands: list, **kwargs):
    """
    Takes a list of command strings to run in subprocess
    Optional vars - default, description:
        error_ok        - catch Exceptions and log them, default: False
        quiet           - don't output from stderr/stdout, Default: False
        spinner         - show an animated progress spinner. can break sudo
                          prompts and should be turned off. Default: True
        cwd             - path to run commands in. Default: pwd of user
        shell           - use shell with subprocess or not. Default: False
        env             - dictionary of env variables for BASH. Default: None
    """
    # get/set defaults and remove the 2 output specific args from the key word
    # args dict so we can use the rest to pass into subproc.Popen later on
    spinner = kwargs.pop('spinner', True)
    quiet = kwargs.get('quiet', False)

    if spinner:
        # only need this if we're doing a progress spinner
        console = Console()

    for cmd in commands:

        # do some very basic syntax highlighting
        printed_cmd = basic_syntax(cmd)
        if not quiet:
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

        # Sometimes we need to not use a little loading bar
        if not spinner:
            log.info(status_line, extra={"markup": True})
            output = run_subprocess(cmd, **kwargs)
        else:
            log.debug(cmd)
            with console.status(status_line,
                                spinner='aesthetic',
                                speed=0.75) as status:
                output = run_subprocess(cmd, **kwargs)

    return output


def run_subprocess(command: str, decode_ascii: bool = False, **kwargs):
    """
    Takes a str commmand to run in BASH in a subprocess.
    Typically run from subproc, which handles output printing.
    Optional keyword vars:
        error_ok  - bool, catch errors, defaults to False
        cwd       - str, current working dir which is the dir to run command in
        env       - environment variables you'd like to pass in
        shell     - bool, run shell or not
        text, universal_newlines - allow for "" in commands
        decode_ascii - decode ascii strings instead of the default UTF-8
    """
    # get the values if passed in, otherwise, set defaults
    quiet = kwargs.pop('quiet', False)
    error_ok = kwargs.pop('error_ok', False)

    try:
        if kwargs.get('universal_newlines', None):
            p = Popen(command, stdout=PIPE, stderr=PIPE, **kwargs)
        else:
            p = Popen(command.split(), stdout=PIPE, stderr=PIPE, **kwargs)
    except Exception as e:
        if error_ok:
            log.debug(str(e))
            return str(e)
        else:
            raise Exception(e)

    res = p.communicate()
    return_code = p.returncode

    # decode the output only if universal_newlines is not true
    if kwargs.get('universal_newlines', None) or kwargs.get('text', None):
        log.debug("universal_newlines or text is true")
        res_stdout, res_stderr = res[0], res[1]
    elif decode_ascii:
        log.debug("decode_ascii is true")
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        res_stdout = ansi_escape.sub('', res[0].decode('UTF-8'))
        res_stderr = ansi_escape.sub('', res[1].decode('UTF-8'))
    else:
        res_stdout, res_stderr = res[0].decode('UTF-8'), res[1].decode('UTF-8')

    # if quiet = True, or res_stdout is empty, we hide this
    if res_stdout and not quiet:
        try:
            log.info(res_stdout)
        except MarkupError:
            log.debug(
                "Rich logging errored because there's special characters in the"
                " output and rich can't render the markdown.")
            log.info(res_stdout, extra={"markup": False})

    if res_stderr and not quiet:
        log.info(res_stderr)

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


def simple_loading_bar(tasks: dict, time_to_wait: int = 120) -> None:
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

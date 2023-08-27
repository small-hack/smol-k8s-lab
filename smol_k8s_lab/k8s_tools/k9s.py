from ..utils.subproc import subproc


def run_k9s(command: str = 'applications.argoproj.io'):
    """
    runs k9s
    takes one command str to run when k9s is launched
    """
    subproc([f'k9s --command {command}'])

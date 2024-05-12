from .subproc import subproc
from smol_k8s_lab.utils.rich_cli.console_logging import header, sub_header


def run_final_cmd(command: str = 'applications.argoproj.io',
                  terminal: str = "wezterm",
                  window_behavior: str = "") -> None:
    """
    runs k9s
    takes one command str to run when k9s is launched
    """
    header("Running post-config command", "💻")
    sub_header(f"Running command: '{command}'")
    sub_header(f"terminal: '{terminal}'")
    sub_header(f"window_behavior: '{window_behavior}'")

    if not window_behavior:
        subproc([command], spinner=False)
    else:
        if terminal == "wezterm":
            run_wezterm_command(command, window_behavior)

        if terminal == "zellij":
            run_zellij_command(command, window_behavior)


def run_zellij_command(command: str, window_behavior: str = ""):
    """
    run a command in zellij either in the same pane or a different one
    """
    if not window_behavior or window_behavior == "same window":
        cmd = command

    elif window_behavior == "split right":
        cmd = f"zellij run --direction right -- {command}"

    elif window_behavior == "split left":
        cmd = f"zellij run --direction left -- {command}"

    elif window_behavior == "split top":
        cmd = f"zellij run --direction up -- {command}"

    elif window_behavior == "split bottom":
        cmd = f"zellij run --direction down -- {command}"

    elif window_behavior == "new tab" or window_behavior == "new-window":
        cmd = f"zellij run --floating -- {command}"

    elif window_behavior == "new window":
        cmd = f"zellij run --floating --  {command}"

    subproc([cmd], spinner=False, quiet=True)


def run_wezterm_command(command: str, window_behavior: str = ""):
    """
    run a command in wezterm either in the same pane or a different tab/window
    """
    if not window_behavior or window_behavior == "same window":
        cmd = command

    elif window_behavior == "split right":
        cmd = f"wezterm cli split-pane --right {command}"

    elif window_behavior == "split left":
        cmd = f"wezterm cli split-pane --left {command}"

    elif window_behavior == "split top":
        cmd = f"wezterm cli split-pane --top {command}"

    elif window_behavior == "split bottom":
        cmd = f"wezterm cli split-pane --bottom {command}"

    elif window_behavior == "new tab":
        cmd = f"wezterm cli spawn {command}"

    elif window_behavior == "new window":
        cmd = f"wezterm cli spawn --new-window {command}"

    subproc([cmd], spinner=False, quiet=True)

from .subproc import subproc


def run_final_cmd(command: str = 'applications.argoproj.io',
                  terminal: str = "wezterm",
                  window_behavior: str = "") -> None:
    """
    runs k9s
    takes one command str to run when k9s is launched
    """
    if not window_behavior:
        subproc([command], spinner=False)
    else:
        if terminal == "wezterm":
            if not window_behavior:
                cmd = command
            elif window_behavior == "split-right":
                cmd = f"wezterm cli split-pane --right {command}"
            elif window_behavior == "split-left":
                cmd = f"wezterm cli split-pane --left {command}"
            elif window_behavior == "split-top":
                cmd = f"wezterm cli split-pane --top {command}"
            elif window_behavior == "split-bottom":
                cmd = f"wezterm cli split-pane --bottom {command}"
            elif window_behavior == "new-tab":
                cmd = f"wezterm cli spawn {command}"
            elif window_behavior == "new-window":
                cmd = f"wezterm cli spawn --new-window {command}"

            subproc([cmd], spinner=False)

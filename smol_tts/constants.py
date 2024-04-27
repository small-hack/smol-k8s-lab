from os import path
from xdg_base_dirs import xdg_data_home

DEFAULT_SAVE_PATH = path.join(xdg_data_home(), "smol-k8s-lab/audio_files")
SPEECH_TEXT_DIRECTORY = path.join(path.dirname(__file__), '../smol_k8s_lab/config/audio')

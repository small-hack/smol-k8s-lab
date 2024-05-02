# NOTE: this will only work if you already have ffmpeg installed
from .constants import DEFAULT_SAVE_PATH, SPEECH_TEXT_DIRECTORY

# external libs
from os import path, makedirs, remove, uname
from pydub import AudioSegment
from ruamel.yaml import YAML
from smol_k8s_lab.utils.rich_cli.console_logging import header, sub_header
import torch
from TTS.api import TTS


if uname().machine == "arm64":
    DEVICE = "mps"
else:
    # Get device and decide if we're using the GPU for this
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# for nl but too fast = tts_models/nl/css10/vits
# doesn't work for nl = tts_models/nl/mai/tacotron2-DDC
# we love jenny. she's our favorite English speaking model
TTS_MODELS = {'en': "tts_models/en/jenny/jenny",
              'nl': "tts_models/nl/css10/vits"}


class AudioGenerator():
    """
    for each file in the speech config directory, open the file and generate .wav
    files before converting them all to smaller mp3s. takes two optional args:
      languages:  list of 2 character language codes like ["en","nl"]
      categories: str of specific category for generation of audio, e.g. screens
      save_path:  defaults to XDG_DATA_HOME (~/.local/share/smol-k8s-lab)
    """

    def __init__(self,
                 languages: list|str = None,
                 category: str = "all",
                 save_path: str = DEFAULT_SAVE_PATH,
                 cached_cfg: str = ""):
        self.category = category
        self.languages = languages
        self.save_path = save_path
        self.cached_dir = cached_cfg
        self.cached_cfg = {}

        # immediately initialize a dict of TTS models to use
        self.tts = {}

        # this is using yaml
        self.yaml = YAML()

    async def process_all_languages(self,):
        if not self.languages:
            for language, model in TTS_MODELS.items():
                # keep track of the tts instance with each language's model
                self.tts[language] = TTS(model_name=model).to(DEVICE)
                # kick off each language's config concurrently
                await self.process_audio_config(language, self.category)
        else:
            if isinstance(self.languages, list):
                for language in self.languages:
                    self.tts[language] = TTS(model_name=TTS_MODELS[language]).to(DEVICE)
                    await self.process_audio_config(language, self.category)
            else:
                self.tts[self.languages] = TTS(model_name=TTS_MODELS[self.languages]).to(DEVICE)
                await self.process_audio_config(self.languages, self.category)

    async def process_audio_config(self,
                                   lang: str = "",
                                   category: str = None) -> None:
        """
        process an audio config file for a given language and category
        """
        # open the list of things to generate speech files for
        lang_file_path = path.join(SPEECH_TEXT_DIRECTORY, f"{lang}.yml")
        # this is for comparing the old config
        try:
            with open(path.join(self.cached_cfg, f"{lang}.yml"), 'r') as yml_f:
                self.cached_cfg = self.yaml.load(yml_f)
        except Exception as e:
            self.cached_cfg = {}

        header(f"Opening {lang_file_path} to process speech text categories...")
        with open(lang_file_path, 'r') as yaml_file:
            yaml_obj = self.yaml.load(yaml_file)

            if not category or category == "apps":
                # generate audio files for apps
                apps = yaml_obj.get('apps', None)
                if apps:
                    header(f"Processing [green]apps[/] category for {lang} lang.")
                    if apps != self.cached_cfg.get('apps', {}):
                        await self.process_apps(lang, apps)
                    else:
                        sub_header("Looks like the apps category hasn't actually changed, so moving on...")

            if not category or category == "cluster_names":
                # generate audio files for cluster names
                cluster_names = yaml_obj.get('cluster_names', None)
                if cluster_names:
                    header(f"processing [green]cluster_names[/] category for {lang} lang.")
                    if cluster_names != self.cached_cfg.get('cluster_names', {}):
                        await self.process_cluster_names(lang, cluster_names)
                    else:
                        sub_header("Looks like the cluster_names category hasn't actually changed, so moving on...")

            if not category or category == "screens":
                # generate audio files for screens
                header(f"processing [green]screens[/] category for {lang} lang.")
                screens = yaml_obj.get('screens', {})
                if screens != self.cached_cfg.get('screens', {}):
                    await self.process_screens(lang, screens)
                else:
                    sub_header("Looks like the screens category hasn't actually changed, so moving on...")

            if not category or category == "phrases":
                # generate audio files for phrases
                phrases = yaml_obj.get('phrases', {})
                if phrases:
                    header(f"processing [green]phrases[/] category for {lang} lang.")
                    if phrases != self.cached_cfg.get('phrases', {}):
                        await self.process_phrases(lang, phrases)
                    else:
                        sub_header("Looks like the phrases category hasn't actually changed, so moving on...")

            if not category or category == "numbers":
                # generate audio files for phrases
                numbers = yaml_obj.get('numbers', {})
                if numbers:
                    header(f"processing [green]numbers[/] category for {lang} lang.")
                    if numbers != self.cached_cfg.get('numbers', {}):
                        await self.process_numbers(lang, numbers)
                    else:
                        sub_header("Looks like the numbers category hasn't actually changed, so moving on...")

    async def process_apps(self, language: str, apps: dict):
        """
        process just the apps
        """
        save_path_base = path.join(self.save_path, f"{language}/apps")
        if not path.exists(save_path_base):
            sub_header(f"{save_path_base} didn't exist, so we're creating it now...")
            makedirs(save_path_base, exist_ok=True)

        # for each screen and it's titles,
        for app, app_text in apps.items():

            mp3_exists = path.exists(path.join(save_path_base, f"{app}.mp3"))
            cached_app = self.cached_cfg.get('apps', {}).get(app, "") == app

            if not mp3_exists or not cached_app:
                await self.generate_single_audio_file(self.tts[language],
                                                      save_path_base,
                                                      app,
                                                      app_text)

    async def process_cluster_names(self, language: str, cluster_names: dict):
        """
        process just the cluster names
        """
        save_path_base = path.join(self.save_path, f"{language}/cluster_names")
        if not path.exists(save_path_base):
            sub_header(f"{save_path_base} didn't exist, so we're creating it now...")
            makedirs(save_path_base, exist_ok=True)

        await self.generate_audio_files_from_dict(self.tts[language],
                                                  save_path_base,
                                                  cluster_names)

    async def process_numbers(self, language: str, numbers: dict):
        """
        process just the numbers
        """
        save_path_base = path.join(self.save_path, f"{language}/numbers")
        if not path.exists(save_path_base):
            sub_header(f"{save_path_base} didn't exist, so we're creating it now...")
            makedirs(save_path_base, exist_ok=True)

        await self.generate_audio_files_from_dict(self.tts[language],
                                                  save_path_base,
                                                  numbers)

    async def process_phrases(self, language: str, phrases: dict):
        """
        process just the common phrases
        """
        save_path_base = path.join(self.save_path, f"{language}/phrases")
        if not path.exists(save_path_base):
            sub_header(f"{save_path_base} didn't exist, so we're creating it now...")
            makedirs(save_path_base, exist_ok=True)

        await self.generate_audio_files_from_dict(self.tts[language],
                                                  save_path_base,
                                                  phrases)

    async def process_screens(self, language: str, screen_texts: dict):
        """
        calls generate method to create a .wav audio file for each screen's
        title and description and save them to a directory based on the language
        """
        save_path_base = path.join(self.save_path, f"{language}/screens")
        if not path.exists(save_path_base):
            sub_header(f"{save_path_base} didn't exist, so we're creating it now...")
            makedirs(save_path_base, exist_ok=True)

        # for each screen and it's titles,
        for screen, titles in screen_texts.items():
            await self.generate_audio_files_from_dict(self.tts[language],
                                                      save_path_base,
                                                      titles,
                                                      screen)

    async def generate_single_audio_file(self,
                                         tts: TTS,
                                         save_path_base: str,
                                         file_name: str,
                                         text_to_speak: str):
        """
        generate an audio .wav format for a single string and then converts it to
        an mp3 # NOTE: this will only work if you already have ffmpeg installed
        """
        save_path = path.join(save_path_base, f"{file_name}.wav")
        tts.tts_to_file(text=text_to_speak, file_path=save_path)
        # convert the .wav to .mp3
        # may consider adding codec="libmp3lame"
        AudioSegment.from_wav(save_path).export(save_path.replace(".wav", ".mp3"),
                                                format="mp3",
                                                bitrate="64k")
        remove(save_path)

    async def generate_audio_files_from_dict(self,
                                             tts: TTS,
                                             save_path_base: str,
                                             text_dict: dict,
                                             prefix: str = ""):
        """
        generate an audio .wav format and then converts it to an mp3 for each
        thing in a dictionary
        # NOTE: this will only work if you already have ffmpeg installed
        """
        for text_category, text in text_dict.items():
            if prefix:
                sound_file = f"{prefix}_{text_category}.wav"
            else:
                sound_file = f"{text_category}.wav"

            save_path = path.join(save_path_base, sound_file)
            mp3_file = save_path.replace("wav", "mp3")

            if not path.exists(mp3_file):
                tts.tts_to_file(text=text, file_path=save_path)
                AudioSegment.from_wav(save_path).export(mp3_file,
                                                        format="mp3",
                                                        bitrate="64k")
                remove(save_path)
            else:
                sub_header(f"{mp3_file} already exists, continuing...")

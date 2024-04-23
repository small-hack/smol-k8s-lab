from .constants import DEFAULT_SAVE_PATH, SPEECH_TEXT_DIRECTORY

# external libs
from os import path, makedirs
from ruamel.yaml import YAML
import torch
from TTS.api import TTS


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
    files. takes two optional args:
      languages:  list of 2 character language codes like ["en","nl"]
      categories: str of specific category for generation of audio, e.g. screens
      save_path:  defaults to XDG_DATA_HOME (~/.local/share/smol-k8s-lab)
    """

    def __init__(self,
                 languages: list|str = None,
                 category: str = "all",
                 save_path: str = DEFAULT_SAVE_PATH):
        # immediately initialize a dict of TTS models to use
        self.category = category
        self.languages = languages
        self.save_path = save_path
        self.tts = {}
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
                                   language: str = "",
                                   category: str = None) -> None:
        """
        process an audio config file for a given language
        """
        # open the list of things to generate speech files for
        language_file_path = path.join(SPEECH_TEXT_DIRECTORY, f"{language}.yml")
        print(f"Opening {language_file_path} to process speech text categories...")
        with open(language_file_path, 'r') as yaml_file:
            yaml_obj = self.yaml.load(yaml_file)

            if not category or category == "apps":
                # generate audio files for apps
                apps  = yaml_obj.get('apps', None)
                if apps:
                    print(f"processing apps category for {language} language.")
                    await self.process_apps(language, apps)

            if not category or category == "cluster_names":
                # generate audio files for cluster names
                cluster_names = yaml_obj.get('cluster_names', None)
                if cluster_names:
                    print(f"processing cluster_names category for {language} language.")
                    await self.process_cluster_names(language, cluster_names)

            if not category or category == "screens":
                # generate audio files for screens
                print(f"processing screens category for {language} language.")
                await self.process_screens(language, yaml_obj['screens'])

            if not category or category == "phrases":
                # generate audio files for phrases
                phrases = yaml_obj.get('phrases', None)
                if phrases:
                    print(f"processing phrases category for {language} language.")
                    await self.process_phrases(language, phrases)

            if not category or category == "numbers":
                # generate audio files for phrases
                numbers = yaml_obj.get('numbers', None)
                if numbers:
                    print(f"processing numbers category for {language} language.")
                    await self.process_numbers(language, numbers)

    async def process_apps(self, language: str, apps: dict):
        """
        process just the apps
        """
        save_path_base = path.join(self.save_path, f"{language}/apps")
        if not path.exists(save_path_base):
            print(f"{save_path_base} didn't exist, so we're creating it now...")
            makedirs(save_path_base, exist_ok=True)

        # for each screen and it's titles,
        for app, app_text in apps.items():
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
            print(f"{save_path_base} didn't exist, so we're creating it now...")
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
            print(f"{save_path_base} didn't exist, so we're creating it now...")
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
            print(f"{save_path_base} didn't exist, so we're creating it now...")
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
            print(f"{save_path_base} didn't exist, so we're creating it now...")
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
        generate an audio .wav format for a single string
        """
        save_path = path.join(save_path_base, f"{file_name}.wav")
        tts.tts_to_file(text=text_to_speak, file_path=save_path)

    async def generate_audio_files_from_dict(self,
                                             tts: TTS,
                                             save_path_base: str,
                                             text_dict: dict,
                                             prefix: str = ""):
        """
        generate an audio .wav format for each thing in a dictionary
        """
        for text_category, text in text_dict.items():
            if prefix:
                sound_file = f"{prefix}_{text_category}.wav"
            else:
                sound_file = f"{text_category}.wav"
            save_path = path.join(save_path_base, sound_file)
            tts.tts_to_file(text=text, file_path=save_path)

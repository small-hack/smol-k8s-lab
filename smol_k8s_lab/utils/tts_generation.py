import asyncio
from smol_k8s_lab.constants import PWD
import torch
from TTS.api import TTS
from os import path, walk
from ruamel.yaml import YAML
yaml = YAML()
# Get device and decide if we're using the GPU for this
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# we love jenny
# alternative_for_nl_but_too_fast = tts_models/nl/css10/vits
# doesn't work = tts_models/nl/mai/tacotron2-DDC
tts_dict = {'en': "tts_models/en/jenny/jenny",
            'nl': "tts_models/nl/css10/vits"}

SPEECH_TEXT_DIRECTORY = path.join(PWD, 'config/speech')

async def save_audio_for_language(language_file: str = "") -> None:
    """
    saves the audio for a language
    """
    language = language_file.split('.')[0]
    tts = TTS(model_name=tts_dict[language]).to(DEVICE)
    save_path_base = path.join(PWD, f"speech/{language}/")

    # open the list of things to generate speech files for
    language_file_path = path.join(SPEECH_TEXT_DIRECTORY, language_file)
    with open(language_file_path, 'r') as yaml_file:
        text_obj = yaml.load(yaml_file)

        # for each screen and it's titles,
        for screen, titles in text_obj.items():
            await generate_audio_files(tts, save_path_base, screen, titles)


async def generate_audio_files(tts, save_path_base, screen, titles):
    for text_category, text in titles.items():
       save_path = path.join(save_path_base, f"{screen}_{text_category}.wav")
       tts.tts_to_file(text=text, file_path=save_path)


async def main():
    """
    for each file in the speech config directory, open the file and generate wav files
    """
    for (root,dirs,language_files) in walk(SPEECH_TEXT_DIRECTORY):
        print(f"root is {root}")
        for language_file in language_files:
            await save_audio_for_language(language_file)

if __name__ == "__main__":
    import time
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")

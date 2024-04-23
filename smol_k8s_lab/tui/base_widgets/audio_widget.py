# smol-k8s-lab libraries
from smol_k8s_lab.constants import SPEECH_TEXT, SPEECH_MP3_DIR, load_yaml

# external libraries
from os import system, path
from playsound import playsound, PlaysoundException
# from textual import on, work
from textual import work
from textual.app import Widget
from textual.containers import VerticalScroll
from textual.events import DescendantFocus
from textual.widgets import (Button, DataTable, Input, Switch, Select,
                             SelectionList, _collapsible)
from textual.worker import Worker, get_current_worker


class SmolAudio(Widget):
    """
    widget to handle the audio of smol-k8s-lab. we handle beeps and text to speech
    """
    def __init__(self, user_config: dict) -> None:
        """
        the input is the self.app.cfg['smol_k8s_lab']['tui']['accessibility']
        """
        self.cfg = user_config

        # configure global accessibility
        tts = self.cfg['text_to_speech']
        self.speak_on_focus = tts['on_focus']
        self.speak_screen_titles = tts['screen_titles']
        self.speak_screen_desc = tts['screen_descriptions']
        self.speak_on_key_press = tts['on_key_press']
        self.speech_program = tts['speech_program']
        lang = tts['language']
        self.bell_on_focus = self.cfg['bell']['on_focus']
        self.bell_on_error = self.cfg['bell']['on_error']

        # core audio files
        self.tts_files = path.join(SPEECH_MP3_DIR, f'{lang}/')
        self.tts_texts = load_yaml(path.join(SPEECH_TEXT, f'{lang}.yml'))
        self.screen_audio = path.join(self.tts_files, 'screens')
        self.phrase_audio = path.join(self.tts_files, 'phrases')
        self.apps_audio = path.join(self.tts_files, 'apps')
        self.highlighted_audio = path.join(self.tts_files, 'phrases/highlighted.wav')
        self.element_audio = path.join(self.tts_files, 'phrases/element.wav')
        self.value_audio = path.join(self.tts_files, 'phrases/value.wav')
        self.k3s_audio = path.join(self.tts_files, 'cluster_names/k3s.wav')
        self.um_audio = path.join(self.phrase_audio, 'um.wav')
        super().__init__()

    # def on_mount(self) -> None:
    #     self.log("audio widget has been mounted")

    def play_screen_audio(self,
                          screen: str,
                          alt: bool = False,
                          say_title: bool = True,
                          say_desc: bool = True) -> None:
        """
        plays out the screen title for the given screen
        """
        if alt:
            title = "alt_title"
            desc = "alt_description"
        else:
            title = "title"
            desc = "description"

        if self.speak_screen_titles and say_title:
            if not self.speech_program:
                audio_file = path.join(self.screen_audio, f'{screen}_{title}.wav')
                self.say(audio_file=audio_file)
            else:
                self.say(text=self.tts_texts['screens'][f'{screen}'][title])

        if self.speak_screen_desc and say_desc:
            if not self.speech_program:
                number_of_workers = len(self.workers)
                while number_of_workers > 1:
                    self.log(f"play screen audio number of workers is {number_of_workers}")
                audio_file = path.join(self.screen_audio, f'{screen}_{desc}.wav')
                self.say(audio_file=audio_file)
            else:
                self.say(text=self.tts_texts['screens'][f'{screen}'][desc])

    @work(thread=True, group="say-workers")
    async def say(self, text: str = "", audio_file: str = "") -> None:
        """
        Use the configured speech program to read a string aloud.
        """
        say = self.speech_program
        if say:
            if text:
                text_for_speech = text.replace("(", "").replace(")", "")
                tts = text_for_speech.replace("[i]", "").replace("[/]", "")
                system(f"{say} {tts}")

            elif not text:
                # if the use pressed f5, the key to read the widget ID aloud
                if self.speak_on_key_press:
                    focused = self.app.focused
                    if isinstance(focused, _collapsible.CollapsibleTitle):
                        system(f"{say} element is a Collapsible called {focused.label}.")
                    else:
                        system(f"{say} element is {focused.id}")

                    # if it's a data table, read out the row content
                    if isinstance(focused, DataTable):
                        self.say_row(focused)
        else:
            worker = get_current_worker()
            if not worker.is_cancelled:
                # don't play a sound if there's already a sound playing
                number_of_workers = len(self.workers)
                desc_audio = "description.wav" in audio_file
                if desc_audio or "/screens/" not in audio_file and number_of_workers > 1:
                    self.log(f"say: number of workers is {number_of_workers}"
                             f" and we must wait to play {audio_file}")
                    for worker_obj in self.workers:
                        if worker_obj != worker and worker_obj.group == "say-workers":
                            await self.workers.wait_for_complete([worker_obj])

                self.app.call_from_thread(playsound, sound=audio_file)
                # playsound(audio_file)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""
        self.log(event)

    def speak_element_app_name(self,
                               element_id: str,
                               trim_text: str|list):
        """
        trims the end of the element to play just the app's name audio
        """
        if isinstance(trim_text, str):
            app_name = element_id.replace(trim_text, "")

        elif isinstance(trim_text, list):
            app_name = element_id
            for text_to_trim in trim_text:
                app_name = app_name.replace(text_to_trim, "")

        playsound(path.join(self.apps_audio, f'{app_name}.wav'))

    @work(exclusive=True, thread=True)
    def speak_element(self):
        """
        speak the currently focused element ID, if the user pressed f5
        """
        focused = self.app.focused
        focused_id = focused.id.replace("-","_") if focused.id else None
        self.log("😘🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶")
        self.log(focused)
        self.log(focused_id)
        self.log("😘🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶")

        # sometimes there's no id for a given element, so we handle that
        if not focused_id:
            focused_id = focused.parent.id.replace("-", "_")
            self.log("⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡")
            self.log(focused_id)
            self.log("⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡")

            # play the basic beginning of the sentence "Collapsible element is..."
            if isinstance(focused, _collapsible.CollapsibleTitle):
                playsound(path.join(self.phrase_audio, 'element_collapsible.wav'))
                if focused_id.endswith("_init_values_collapsible"):
                    self.speak_element_app_name(focused_id, "_init_values_collapsible")
                    playsound(path.join(self.phrase_audio, "init_values.wav"))
            else:
                # play phrase "Element is..."
                playsound(self.element_audio)

                if "k3s" in focused_id:
                    playsound(self.k3s_audio)
                    clean_id = focused_id.replace("k3s_", "")

                # state the ID of the tabbed content out loud
                playsound(path.join(self.phrase_audio, f'{clean_id}.wav'))

                # state the phrase for "selected tab is" ID of the tab
                playsound(path.join(self.phrase_audio, 'element_tab.wav'))

                focused_id = focused.parent.active_pane.id.replace("-", "_")
                if "k3s" in focused_id:
                    playsound(self.k3s_audio)
                    focused_id = focused_id.replace("k3s_", "")

                # state the ID of the tabbed content out loud
                playsound(path.join(self.phrase_audio, f'{focused_id}.wav'))
        else:
            # play the basic beginning of the sentence "Element is..."
            playsound(self.element_audio)
            # if k3s is in the text to play, play that seperately
            if "k3s" in focused_id:
                playsound(self.k3s_audio)
                focused_id = focused_id.replace("k3s_", "")

            if isinstance(focused, Input):
                if focused_id.endswith("_repo"):
                    self.speak_element_app_name(focused_id, "_repo")
                    playsound(path.join(self.phrase_audio, 'repo.wav'))
                elif focused_id.endswith("_path") and "usb" not in focused_id \
                and "bluetooth" not in focused_id:
                        self.speak_element_app_name(focused_id, "_path")
                        playsound(path.join(self.phrase_audio, 'path.wav'))
                elif focused_id.endswith("_revision"):
                    self.speak_element_app_name(focused_id, "_revision")
                    playsound(path.join(self.phrase_audio, 'revision.wav'))
                elif focused_id.endswith("_namespace"):
                    self.speak_element_app_name(focused_id, "_namespace")
                    playsound(path.join(self.phrase_audio, 'namespace.wav'))
                elif focused_id.endswith("_email_input"):
                    self.speak_element_app_name(focused_id, "_email_input")
                    playsound(path.join(self.phrase_audio, 'email_input.wav'))
                elif focused_id.endswith("_new_secret"):
                    self.speak_element_app_name(focused_id, "_new_secret")
                    playsound(path.join(self.phrase_audio, 'new_secret.wav'))
                elif focused_id.endswith("_language_input"):
                    self.speak_element_app_name(focused_id, "_language_input")
                    playsound(path.join(self.phrase_audio, 'language_input.wav'))
                elif focused_id.endswith("_password_input"):
                    self.speak_element_app_name(focused_id, "_password_input")
                    playsound(path.join(self.phrase_audio, 'password_input.wav'))
                elif focused_id.endswith("_user_name_input") or focused_id.endswith("_username_input"):
                    self.speak_element_app_name(focused_id, ["_user_name_input", "_username_input"])
                    playsound(path.join(self.phrase_audio, 'user_name_input.wav'))
                elif focused_id.endswith("_name_input"):
                    self.speak_element_app_name(focused_id, "_name_input")
                    playsound(path.join(self.phrase_audio, 'name_input.wav'))
                elif focused_id.endswith("_toleration_key_input"):
                    self.speak_element_app_name(focused_id, "_toleration_key_input")
                    playsound(path.join(self.phrase_audio, 'toleration_key_input.wav'))
                elif focused_id.endswith("_toleration_value_input"):
                    self.speak_element_app_name(focused_id, "_toleration_value_input")
                    playsound(path.join(self.phrase_audio, 'toleration_value_input.wav'))
                elif focused_id.endswith("_toleration_effect_input"):
                    self.speak_element_app_name(focused_id, "_toleration_effect_input")
                    playsound(path.join(self.phrase_audio, 'toleration_effect_input.wav'))
                else:
                    try:
                        playsound(path.join(self.phrase_audio, f'{focused_id}.wav'))
                    except PlaysoundException:
                        playsound(self.um_audio)

            elif isinstance(focused, Button):
                if focused_id.endswith("_new_secret_button"):
                    self.speak_element_app_name(focused_id, "_new_secret_button")
                    playsound(path.join(self.phrase_audio, 'new_secret_button.wav'))
                else:
                    try:
                        playsound(path.join(self.phrase_audio, f'{focused_id}.wav'))
                    except PlaysoundException:
                        playsound(self.um_audio)

            # if this is a switch of any kind
            elif isinstance(focused, Switch):
                # if it's an application initialization enabled switch...
                if focused_id.endswith("_init_switch"):
                    self.speak_element_app_name(focused_id, "_init_switch")
                    playsound(path.join(self.phrase_audio, 'init_switch.wav'))
                elif focused_id.endswith("_directory_recursion"):
                    self.speak_element_app_name(focused_id, "_directory_recursion")
                    playsound(path.join(self.phrase_audio, 'directory_recursion.wav'))
                else:
                    playsound(path.join(self.phrase_audio, f'{focused_id}.wav'))

            # if this is an app inputs widget container, we need to get the app
            # name and then read that first before the name of the vertical scroll
            elif isinstance(focused, VerticalScroll):
                if focused_id.endswith("_inputs"):
                    self.speak_element_app_name(focused_id, "_inputs")
                    playsound(path.join(self.phrase_audio, 'inputs.wav'))
                elif focused_id.endswith("_argo_config_container"):
                    self.speak_element_app_name(focused_id, "_argo_config_container")
                    playsound(path.join(self.phrase_audio, 'argo_config_container.wav'))
                else:
                    playsound(path.join(self.phrase_audio, f'{focused_id}.wav'))

            # if this is a dropdown menu, we need to read out the value
            elif isinstance(focused, Select):
                playsound(self.value_audio)
                if focused_id == "distro_drop_down":
                    playsound(path.join(self.tts_files,
                                        f'cluster_names/{focused.value}.wav'))
                if focused_id == "node_type":
                    playsound(path.join(self.phrase_audio, f'{focused.value}.wav'))

            # if this is a selection list, such as the apps list
            elif isinstance(focused, SelectionList):
                playsound(self.highlighted_audio)
                # get the actual highlighted app
                highlighted_idx = focused.highlighted
                highlighted_app = focused.get_option_at_index(highlighted_idx).value
                # say name of app
                playsound(path.join(self.apps_audio, f'{highlighted_app}.wav'))

            # if this is a datatable, just call self.say_row
            elif isinstance(focused, DataTable):
                self.say_row(focused)

            # if not any special element then play the id of the element
            else:
                try:
                    playsound(path.join(self.phrase_audio, f'{focused_id}.wav'))
                except PlaysoundException:
                    self.log(f"{focused_id}.wav was not found")
                    playsound(self.um_audio)


    @work(exclusive=True, thread=True)
    def say_row(self, data_table: DataTable) -> None:
        """
        get the column names and row content of a DataTable and read aloud
        """
        row_index = data_table.cursor_row
        row = data_table.get_row_at(row_index)

        # get the row's first column and remove whitespace
        row_column1 = row[0].plain.strip()

        # change ? to question mark so it reads aloud well
        if row_column1 == "?":
            row_column1 = "question mark"

        row_column2 = row[1].plain.strip()
        row_column3 = row[2].plain.strip()
        row_column4 = row[3].plain.strip()

        # get the column names
        columns = list(data_table.columns.values())
        column1 = columns[0].label
        column2 = columns[1].label
        column3 = columns[2].label
        column4 = columns[3].label

        if self.speech_program:
            system(f"{self.speech_program} Selected {column1}: {row_column1}."
                   f" {column2}: {row_column2}. {column3}: {row_column3}. "
                   f"{column4}: {row_column4}.")

        else:
            # then play the row of the table
            element_audio = path.join(self.phrase_audio, 'row.wav')
            playsound(element_audio)
            if data_table.id == "clusters-data-table":
                # cluster name
                element_audio = path.join(self.phrase_audio, 'cluster.wav')
                playsound(element_audio)
                for name in row_column1.split("-"):
                    if name:
                        element_audio = path.join(self.tts_files,
                                                  f'cluster_names/{name}.wav')
                        playsound(element_audio)

                # distro name
                element_audio = path.join(self.phrase_audio, 'distro.wav')
                playsound(element_audio)
                element_audio = path.join(self.tts_files,
                                          f'cluster_names/{row_column2}.wav')
                playsound(element_audio)

                # version
                element_audio = path.join(self.phrase_audio, 'version.wav')
                playsound(element_audio)
                version = row_column3.replace("+k3s1","").replace("v", "").split(".")
                last_item = version[-1]
                for number in version:
                    element_audio = path.join(self.tts_files, f'numbers/{number}.wav')
                    playsound(element_audio)
                    if number != last_item:
                        element_audio = path.join(self.phrase_audio, 'point.wav')
                        playsound(element_audio)

                # platform
                element_audio = path.join(self.phrase_audio, 'platform.wav')
                playsound(element_audio)
                if row_column4 == "linux/arm64":
                    element_audio = path.join(self.tts_files, 'cluster_names/linux_arm.wav')
                    playsound(element_audio)
                elif row_column4 == "linux/amd64":
                    element_audio = path.join(self.tts_files, 'cluster_names/linux_amd.wav')
                    playsound(element_audio)

    def on_focus(self, event: DescendantFocus) -> None:
        """
        on focus, say the id of each element and the value or label if possible
        """
        # first ring the bell if the user would like that
        if self.bell_on_focus:
            self.app.bell()

        if self.speak_on_focus:
            id = event.widget.id
            self.say(f"element is {id}")

            # input fields
            if isinstance(event.widget, Input):
                content = event.widget.value
                placeholder = event.widget.placeholder
                if content:
                    self.say(f"value is {content}")
                elif placeholder:
                    self.say(f"place holder text is {placeholder}")

            # buttons
            elif isinstance(event.widget, Button):
                self.say(f"button text is {event.widget.label}")

            # switches
            elif isinstance(event.widget, Switch) or isinstance(event.widget, Select):
                self.say(f"value is {event.widget.value}")

            # also read the tooltip if there is one
            tooltip = event.widget.tooltip
            if tooltip:
                self.say(f"tooltip is {tooltip}")

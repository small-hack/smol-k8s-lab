# smol-k8s-lab libraries
from smol_k8s_lab.constants import SPEECH_TEXT, SPEECH_MP3_DIR, load_yaml

# external libraries
from os import system, path
from playsound import playsound as SAY
from playsound import PlaysoundException
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
        self.bell_on_focus = self.cfg['bell']['on_focus']

        # core audio files
        self.tts_files = path.join(SPEECH_MP3_DIR, f"{tts['language']}")
        self.tts_texts = load_yaml(path.join(SPEECH_TEXT, f"{tts['language']}.yml"))
        self.screen_audio = path.join(self.tts_files, 'screens')
        self.apps_audio = path.join(self.tts_files, 'apps')
        self.cluster_audio = path.join(self.tts_files, 'cluster_names')
        self.k3s_audio = path.join(self.cluster_audio, 'k3s.mp3')
        self.element_audio = path.join(self.tts_files, 'phrases/element.mp3')
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
        title = "title"
        desc = "description"
        if alt:
            title = "alt_title"
            desc = "alt_description"

        if self.speak_screen_titles and say_title:
            if not self.speech_program:
                audio_file = path.join(self.screen_audio, f'{screen}_{title}.mp3')
                self.say(audio_file=audio_file)
            else:
                self.say(text=self.tts_texts['screens'][f'{screen}'][title])

        if self.speak_screen_desc and say_desc:
            if not self.speech_program:
                number_of_workers = len(self.workers)
                while number_of_workers > 1:
                    self.log(f"play screen audio number of workers is {number_of_workers}")
                audio_file = path.join(self.screen_audio, f'{screen}_{desc}.mp3')
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
                desc_audio = "description.mp3" in audio_file
                if desc_audio or "/screens/" not in audio_file and number_of_workers > 1:
                    self.log(f"say: number of workers is {number_of_workers}"
                             f" and we must wait to play {audio_file}")
                    for worker_obj in self.workers:
                        if worker_obj != worker and worker_obj.group == "say-workers":
                            await self.workers.wait_for_complete([worker_obj])

                self.app.call_from_thread(SAY, sound=audio_file)
                # SAY(audio_file)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""
        self.log(event)

    def say_phrase(self, phrase: str):
        """
        say a phrase and if it can't be found, say um
        """
        try:
            SAY(path.join(self.tts_files, f"phrases/{phrase}"))
        except PlaysoundException:
            self.log(f"{phrase} was not found")
            SAY(path.join(self.tts_files, 'phrases/um.mp3'))

    def say_app(self,
                element_id: str,
                trim_text: str|list = None,
                say_trimmed: bool = True,
                smtp: bool = False):
        """
        trims the end of the element to play just the app's name audio
        if say_trimmed, or smtp is true, also says the rest of the element
        """
        if trim_text:
            if isinstance(trim_text, str):
                app_name = element_id.replace(trim_text, "")

            elif isinstance(trim_text, list):
                app_name = element_id
                for text_to_trim in trim_text:
                    app_name = app_name.replace(text_to_trim, "")

            SAY(path.join(self.apps_audio, f'{app_name}.mp3'))

            # say the element without the app if requested
            if say_trimmed:
                # clear cruft around the word we want to say
                self.log(trim_text)
                trim_text = trim_text.lstrip("_")
                if trim_text.endswith("input"):
                    trim_text = trim_text.rstrip("_input")
                self.log(trim_text)
                self.say_phrase(f"{trim_text}.mp3")

        elif smtp:
            # split string on _ into list of words
            sections = element_id.split("_")

            # remove _input from final string immediately
            if "input" in sections:
                sections.pop()

            # get the index of "smtp" in the list
            smtp_index = sections.index("smtp")

            # say name of app by joining indexes of list that come after smtp
            SAY(path.join(self.apps_audio,
                          f'{"_".join(sections[:smtp_index])}.mp3'))

            # say S.M.T.P.
            self.say_phrase("smtp.mp3")
            noun = sections[smtp_index + 1:][0]

            # say the SMTP noun such as hostname or user
            self.say_phrase(f"{noun}.mp3")

    def say_input(self, focused_id: str):
        """
        deal with any input fields by saying them with playsound()
        """
        if focused_id == "hostname":
            self.say_phrase('hostname.mp3')

        elif focused_id.endswith("_repo"):
            self.say_app(focused_id, "_repo")

        elif focused_id.endswith("_path") and "usb" not in focused_id \
        and "bluetooth" not in focused_id:
                self.say_app(focused_id, "_path")

        elif focused_id.endswith("_revision"):
            self.say_app(focused_id, "_revision")

        elif "project" in focused_id:
            self.say_phrase("project.mp3")
            self.say_phrase(focused_id.lstrip("project_") + ".mp3")

        elif focused_id.endswith("_namespace"):
            self.say_app(focused_id, "_namespace")

        elif focused_id.endswith("_email_input"):
            if "admin" in focused_id:
                self.say_app(focused_id, "_admin_email_input", say_trimmed=False)
                self.say_phrase('admin.mp3')
            else:
                self.say_app(focused_id, "_email_input", say_trimmed=False)

            self.say_phrase('email_input.mp3')

        elif focused_id.endswith("_emails_input"):
            self.say_app(focused_id, "_emails_input")

        elif "oidc" in focused_id:
            self.say_phrase("oidc.mp3")
            self.say_phrase("provider.mp3")

        elif focused_id.endswith("_domains_input"):
            self.say_app(focused_id, "_domains_input")

        elif focused_id.endswith("_new_secret"):
            self.say_app(focused_id, "_new_secret")

        elif focused_id.endswith("_gender"):
            self.say_app(focused_id, "_gender")

        # handle all S3 values at once
        elif "s3" in focused_id:
            # split string on _ into list of words
            sections = focused_id.split("_")

            # remove _input from final string immediately
            if "input" in sections:
                sections.pop()

            # get the index of "s3" in the list
            s3_index = sections.index("s3")

            # say "s three"
            self.say_phrase("s3.mp3")

            if "backup" not in sections:
                s3_index += 1
            else:
                self.say_phrase("backup.mp3")
                s3_index += 2

            # rejoin any remaining words with _ into one string
            noun = "_".join(sections[s3_index:])
            self.say_phrase(f"{noun}.mp3")

        # handle all mail values at once
        elif "smtp" in focused_id:
            self.say_app(focused_id, smtp=True)

        elif focused_id.endswith("restic_repo_password_input"):
            self.say_app(focused_id, "_restic_repo_password_input")

        elif focused_id.endswith("_password_input"):
            self.say_app(focused_id, "_password_input")

        elif "user" in focused_id:
            if "admin" in focused_id:
                self.say_phrase('admin.mp3')
            elif "root" in focused_id:
                self.say_app(focused_id, "_root_user_input", say_trimmed=False)
                self.say_phrase('root.mp3')
            else:
                self.say_app(focused_id, "_user_input", say_trimmed=False)
            self.say_phrase('user.mp3')

        elif "name" in focused_id and "app" not in focused_id:
            if "cluster" not in focused_id:
                self.say_app(focused_id, ["_last", "_first", "_admin"
                                          "_name_input"], say_trimmed=False)
                if "admin" in focused_id:
                    self.say_phrase('admin.mp3')

                if "last" in focused_id:
                    self.say_phrase('last.mp3')

                elif "first" in focused_id:
                    self.say_phrase('first.mp3')
            else:
                self.say_phrase('cluster.mp3')

            self.say_phrase('name.mp3')

        elif focused_id.endswith("_language_input"):
            self.say_app(focused_id, "_language_input")

        elif focused_id.endswith("_toleration_key_input"):
            self.say_app(focused_id, "_toleration_key_input")

        elif focused_id.endswith("_toleration_value_input"):
            self.say_app(focused_id, "_toleration_value_input")

        elif focused_id.endswith("_toleration_effect_input"):
            self.say_app(focused_id, "_toleration_effect_input")
        else:
            self.say_phrase(f'{focused_id}.mp3')

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
                self.say_phrase('element_collapsible.mp3')

                if focused_id.endswith("_init_values_collapsible"):
                    if "sensitive" in focused_id:
                        self.say_app(focused_id,
                                     "_sensitive_init_values_collapsible",
                                     say_trimmed=False)
                        self.say_phrase('sensitive.mp3')
                    else:
                        self.say_app(focused_id, "_init_values_collapsible")
                    self.say_phrase('init_values.mp3')
            else:
                # play phrase "Element is..."
                SAY(self.element_audio)

                if "k3s" in focused_id:
                    SAY(self.k3s_audio)
                    focused_id = focused_id.replace("k3s_", "")

                # state the ID of the tabbed content out loud
                self.say_phrase(f'{focused_id}.mp3')

                # state the phrase for "selected tab is" ID of the tab
                self.say_phrase('element_tab.mp3')

                focused_id = focused.parent.active_pane.id.replace("-", "_")
                if "k3s" in focused_id:
                    SAY(self.k3s_audio)
                    focused_id = focused_id.replace("k3s_", "")

                # state the ID of the tabbed content out loud
                self.say_phrase(f'{focused_id}.mp3')
        else:
            # play the basic beginning of the sentence "Element is..."
            SAY(self.element_audio)
            # if k3s is in the text to play, play that seperately
            if "k3s" in focused_id:
                SAY(self.k3s_audio)
                focused_id = focused_id.replace("k3s_", "")

            if isinstance(focused, Input):
                self.say_input(focused_id)

            elif isinstance(focused, Button):
                if focused_id.endswith("_new_secret_button"):
                    self.say_app(focused_id, "_new_secret_button")
                else:
                    self.say_phrase(f'{focused_id}.mp3')

            # if this is a switch of any kind
            elif isinstance(focused, Switch):
                # if it's an application initialization enabled switch...
                if focused_id.endswith("_init_switch"):
                    self.say_app(focused_id, "_init_switch")
                elif focused_id.endswith("_directory_recursion"):
                    self.say_app(focused_id, "_directory_recursion")
                else:
                    self.say_phrase(f'{focused_id}.mp3')

            # if this is an app inputs widget container, we need to get the app
            # name and then read that first before the name of the vertical scroll
            elif isinstance(focused, VerticalScroll):
                if focused_id.endswith("_inputs"):
                    self.say_app(focused_id, "_inputs")
                elif focused_id.endswith("_argo_config_container"):
                    self.say_app(focused_id, "_argo_config_container")
                else:
                    self.say_phrase(f'{focused_id}.mp3')

            # if this is a dropdown menu, we need to read out the value
            elif isinstance(focused, Select):
                self.say_phrase(f"{focused_id}.mp3")
                self.say_phrase("value.mp3")
                if focused_id == "distro_drop_down":
                    SAY(path.join(self.cluster_audio, f'{focused.value}.mp3'))
                elif focused_id == "node_type":
                    self.say_phrase(f'{focused.value}.mp3')
                elif focused_id == "log_level_select":
                    self.say_phrase(f'{focused.value}.mp3')

            # if this is a selection list, such as the apps list
            elif isinstance(focused, SelectionList):
                self.say_phrase("highlighted.mp3")
                # get the actual highlighted app
                highlighted_idx = focused.highlighted
                highlighted_app = focused.get_option_at_index(highlighted_idx).value
                # say name of app
                SAY(path.join(self.apps_audio, f'{highlighted_app}.mp3'))

            # if this is a datatable, just call self.say_row
            elif isinstance(focused, DataTable):
                self.say_phrase(f'{focused_id}.mp3')
                self.say_row(focused)

            # if not any special element then play the id of the element
            else:
                self.say_phrase(f'{focused_id}.mp3')

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

        # get the column names
        columns = list(data_table.columns.values())
        column1 = columns[0].label
        column2 = columns[1].label

        # then play the row of the table
        if data_table.id == "key-mappings-table":
            self.say_phrase('row.mp3')
            key_binding = row_column1.replace(" ", "_").replace("+","_plus_")
            if "?" in key_binding:
                self.say_phrase("question_mark_or_h.mp3")
            else:
                self.say_phrase(f"{key_binding}.mp3")

        # then play the row of the table
        elif data_table.id == "clusters-data-table":
            row_column3 = row[2].plain.strip()
            row_column4 = row[3].plain.strip()
            column3 = columns[2].label
            column4 = columns[3].label

            if self.speech_program:
                system(f"{self.speech_program} Selected row is "
                       f"{column1}: {row_column1}. "
                       f"{column2}: {row_column2}. {column3}: {row_column3}. "
                       f"{column4}: {row_column4}.")
            else:
                self.say_phrase('row.mp3')
                # cluster name
                self.say_phrase('cluster.mp3')
                for name in row_column1.split("-"):
                    if name:
                        SAY(path.join(self.cluster_audio, f'{name}.mp3'))

                # distro name
                self.say_phrase('distro.mp3')
                SAY(path.join(self.cluster_audio, f'{row_column2}.mp3'))

                # version
                self.say_phrase('version.mp3')
                version = row_column3.rstrip("+k3s1").lstrip("v").split(".")
                last_item = version[-1]
                for number in version:
                    SAY(path.join(self.tts_files, f'numbers/{number}.mp3'))
                    # say "point" between numbers
                    if number != last_item:
                        self.say_phrase('point.mp3')

                # platform
                self.say_phrase('platform.mp3')
                if row_column4 == "linux/arm64":
                    SAY(path.join(self.cluster_audio, 'linux_arm.mp3'))
                elif row_column4 == "linux/amd64":
                    SAY(path.join(self.cluster_audio, 'linux_amd.mp3'))
        else:
            self.say_phrase('row.mp3')

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

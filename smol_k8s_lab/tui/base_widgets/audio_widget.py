# smol-k8s-lab libraries
from smol_k8s_lab.constants import SPEECH_TEXT, SPEECH_MP3_DIR, load_yaml

# external libraries
from os import system, path
from textual import work
from textual.app import Widget
from textual.containers import VerticalScroll
from textual.events import DescendantFocus
from textual.widgets import (Button, DataTable, Input, Switch, Select,
                             SelectionList, _collapsible)
from textual.worker import Worker
from pygame import mixer, error
import logging as log

class SmolAudio(Widget):
    """
    widget to handle the audio of smol-k8s-lab. we handle beeps and
    text to speech
    """

    def __init__(self, user_config: dict) -> None:
        """
        the input is the self.app.cfg['smol_k8s_lab']['tui']['accessibility']
        """
        self.cfg = user_config

        # get text to speech settings
        tts = self.cfg['text_to_speech']
        self.speech_program = tts['speech_program']
        self.speak_on_focus = tts['on_focus']
        self.speak_screen_titles = tts['screen_titles']
        self.speak_screen_desc = tts['screen_descriptions']
        self.speak_on_key_press = tts['on_key_press']

        # get beep settings
        self.bell_on_focus = self.cfg['bell']['on_focus']

        # core audio files
        self.tts_files = path.join(SPEECH_MP3_DIR, f"{tts['language']}")
        self.tts_texts = load_yaml(path.join(SPEECH_TEXT,
                                             f"{tts['language']}.yml"))
        self.screen_audio = path.join(self.tts_files, 'screens')
        self.apps_audio = path.join(self.tts_files, 'apps')
        self.cluster_audio = path.join(self.tts_files, 'cluster_names')
        self.k3s_audio = path.join(self.cluster_audio, 'k3s.mp3')
        self.element_audio = path.join(self.tts_files, 'phrases/element.mp3')

        # only initialize the mixer if audio is requested for something
        if self.speak_on_focus or self.speak_screen_titles \
                or self.speak_on_key_press or self.speak_screen_desc:
            self.core_mixer = mixer
            try:
                self.core_mixer.init()
            except error:
                log.info("No audio device found")

        super().__init__()

    def on_mount(self) -> None:
        self.log("SmolAudio widget has been mounted")

    @work(group="pygame-play-workers")
    async def pyg_play(self, audio_file: str):
        """
        play audio file with pygame
        """
        try:
            audio = self.core_mixer.Sound(audio_file)
        except FileNotFoundError:
            self.log(f"audio file not found :( audio file is '{audio_file}'")
            audio = self.core_mixer.Sound(path.join(self.tts_files, 'phrases/um.mp3'))

        while True:
            if not self.core_mixer.get_busy():
                break
        audio.play()

    def say(self, text: str = "", audio_file: str = "") -> None:
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
            self.pyg_play(audio_file)

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
                audio_file = path.join(self.screen_audio,
                                       f'{screen}_{title}.mp3')
                self.say(audio_file=audio_file)
            else:
                self.say(text=self.tts_texts['screens'][f'{screen}'][title])

        if self.speak_screen_desc and say_desc:
            if not self.speech_program:
                number_of_workers = len(self.workers)
                while number_of_workers > 1:
                    self.log(f"play screen audio number of workers is {number_of_workers}")
                audio_file = path.join(self.screen_audio,
                                       f'{screen}_{desc}.mp3')
                self.say(audio_file=audio_file)
            else:
                self.say(text=self.tts_texts['screens'][f'{screen}'][desc])


    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""
        self.log(event)

    def say_phrase(self, phrase: str):
        """
        say a phrase and if it can't be found, say um
        """
        try:
            self.say(audio_file=path.join(self.tts_files, f"phrases/{phrase}"))
        except Exception as e:
            self.log(e)
            self.log(f"{phrase} was not found")
            self.say(audio_file=path.join(self.tts_files, 'phrases/um.mp3'))

    def say_app(self,
                element_id: str = "",
                trim_text: str|list = None,
                say_trimmed: bool = True,
                smtp: bool = False,
                restic_snapshot_id: bool = False,
                app: str = ""):
        """
        trims the end of the element to play just the app's name audio
        if say_trimmed, or smtp is true, also says the rest of the element

        if you pass in a key word argument "app" we can say just the app name
        """
        if app:
            self.say(audio_file=path.join(self.apps_audio, f'{app}.mp3'))
        elif trim_text:
            if isinstance(trim_text, str):
                app_name = element_id.replace(trim_text, "")

            elif isinstance(trim_text, list):
                app_name = element_id
                for text_to_trim in trim_text:
                    app_name = app_name.replace(text_to_trim, "")

            self.say(audio_file=path.join(self.apps_audio, f'{app_name}.mp3'))

            # say the element without the app if requested
            if say_trimmed:
                # clear cruft around the word we want to say
                self.log("💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁")
                self.log(trim_text)
                self.log("💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁")
                trim_text = trim_text.lstrip("_")
                if trim_text.endswith("input"):
                    trim_text = trim_text.rstrip("_input")
                self.log(trim_text)
                self.log("💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁💁")
                self.say_phrase(f"{trim_text}.mp3")
        elif restic_snapshot_id:
            # if it starts with seaweedfs, then it's for seaweedfs
            # and we have the full phrase already
            if element_id.startswith("seaweedfs"):
                self.say_phrase(element_id)
            # if it has seaweedfs_ in it, we also have that phrase
            elif "_seaweedfs_" in element_id:
                app_name = element_id.split("_seaweedfs_")[0]
                self.say(audio_file=path.join(self.apps_audio, f'{app_name}.mp3'))
                input_field = element_id.replace(f"{app_name}_", "") + ".mp3"
                self.say_phrase(input_field)
            else:
                if "_files_" in element_id:
                    app_name = element_id.replace("_files_restic_snapshot_id",
                                                  "")
                    self.say(audio_file=path.join(self.apps_audio, f'{app_name}.mp3'))
                    self.say_phrase("files_restic_snapshot_id.mp3")
                elif "_config_" in element_id:
                    app_name = element_id.replace("_config_restic_snapshot_id",
                                                  "")
                    self.say(audio_file=path.join(self.apps_audio, f'{app_name}.mp3'))
                    self.say_phrase("config_restic_snapshot_id.mp3")
        elif smtp:
            # split string on _ into list of words
            sections = element_id.split("_")

            # remove _input from final string immediately
            if "input" in sections:
                sections.pop()

            # get the index of "smtp" in the list
            smtp_index = sections.index("smtp")

            # say name of app by joining indexes of list that come after smtp
            self.say(audio_file=path.join(self.apps_audio,
                          f'{"_".join(sections[:smtp_index])}.mp3'))

            # say S.M.T.P.
            self.say_phrase("smtp.mp3")
            noun = sections[smtp_index + 1:][0]

            # say the SMTP noun such as hostname or user
            self.say_phrase(f"{noun}.mp3")

    def say_drop_down_menu(self, focused_id: str, focused_value: str):
        """
        deal with any drop down menu by saying it with pyglet
        """
        # first say the name of the drop down
        self.say_phrase(f"{focused_id}.mp3")

        # then say drop down menu
        self.say_phrase("drop_down.mp3")

        # then start to say "selected value is..."
        self.say_phrase("value.mp3")

        if focused_id == "distro_drop_down":
            self.say(audio_file=path.join(self.cluster_audio, f'{focused_value}.mp3'))

        # if there's a space in the value, split it up to say each word
        elif " " in focused_value:
            focused_values = focused_value.split(" ")
            for word in focused_values:
                self.say_phrase(f'{word}.mp3')

        else:
            self.say_phrase(f'{focused_value}.mp3')

    def say_switch(self, focused_id: str, focused_value: bool):
        """
        deal with any button by saying it with pyglet
        """
        # if it's an application initialization enabled switch...
        if focused_id.endswith("_init_switch"):
            self.say_app(focused_id, "_init_switch")
        elif focused_id.endswith("_directory_recursion"):
            self.say_app(focused_id, "_directory_recursion")
        elif focused_id.endswith("_restore_enabled"):
            if "cnpg" in focused_id:
                self.say_app(focused_id, "_cnpg_restore_enabled",
                             say_trimmed=False)
                self.say_app(app="cnpg_operator")
                self.say_phrase("restore_enabled.mp3")
            else:
                self.say_app(focused_id, "_restore_enabled")
        else:
            self.say_phrase(f'{focused_id}.mp3')

        # then say switch
        self.say_phrase('switch.mp3')

        # say if the switch is off or not
        if focused_value:
            self.say_phrase("switch_on.mp3")
        else:
            self.say_phrase("switch_off.mp3")

    def say_button(self, focused_id: str):
        """
        deal with any button by saying it with pyglet
        """
        if focused_id.endswith("_new_secret_button"):
            self.say_app(focused_id, "_new_secret_button", say_trimmed=False)
            self.say_phrase('new_secret.mp3')
        else:
            self.say_phrase(f'{focused_id.replace("_button","")}.mp3')

        self.say_phrase('button.mp3')

    def say_input(self, focused_id: str):
        """
        deal with any input fields by saying them with pyglet
        """
        if focused_id == "hostname":
            self.say_phrase('hostname.mp3')

        elif focused_id.endswith("control_plane_nodes_input"):
            self.say_phrase('control_plane_nodes_input.mp3')

        elif focused_id.endswith("worker_nodes_input"):
            self.say_phrase('worker_nodes_input.mp3')

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

        elif focused_id.endswith("postgres_backup_schedule"):
            self.say_app(focused_id, "_postgres_backup_schedule")

        elif focused_id.endswith("pvc_backup_schedule"):
            self.say_app(focused_id, "_pvc_backup_schedule")

        # handle all S3 values at once
        elif "s3" in focused_id:
            # split string on _ into list of words
            sections = focused_id.split("_")
            self.log("🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊")
            self.log(sections)
            self.log("🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊")

            # remove _input from final string immediately
            if "input" in sections:
                sections.pop()

            # say "s three"
            self.say_phrase("s3.mp3")
            sections.pop(sections.index("s3"))

            if "backup" in sections:
                self.say_phrase("backup.mp3")
                sections.pop(sections.index("backup"))


            self.say_app(app=sections[0])
            sections.pop(0)

            # rejoin any remaining words with _ into one string
            noun = "_".join(sections)
            self.log("🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊")
            self.log(noun)
            self.log("🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊")
            self.say_phrase(f"{noun}.mp3")

        # handle all mail values at once
        elif "smtp" in focused_id:
            self.say_app(focused_id, smtp=True)

        elif "restic_snapshot_id" in focused_id:
            self.say_app(focused_id, restic_snapshot_id=True)

        elif focused_id.endswith("restic_repository_password"):
            self.say_app(focused_id, "_restic_repository_password")

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

        elif "cloudflare_api_token" in focused_id:
            self.say_phrase('cloudflare_api_token.mp3')

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

        self.say_phrase('input.mp3')

    @work(exclusive=True, thread=True)
    def speak_element(self):
        """
        speak the currently focused element ID, if the user pressed f5
        """
        focused = self.app.focused
        self.log("😘🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶🐶")
        self.log(focused)

        # every now and then nothing is focused for some reason...
        if not focused:
            self.log("nothing is focused")
            return

        focused_id = focused.id.replace("-","_") if focused.id else None
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
                        self.say_phrase('init_values.mp3')
                    else:
                        self.say_app(focused_id, "_init_values_collapsible")
                elif focused_id.endswith("_argocd_app_config"):
                    self.say_app(focused_id, "_argocd_app_config")
                elif focused_id.endswith("_secret_keys_collapsible"):
                    self.say_app(focused_id, "_secret_keys_collapsible")
                elif focused_id.endswith("_argo_proj_config_collapsible"):
                    self.say_app(focused_id, "_argo_proj_config_collapsible")
                elif focused_id.endswith("_restore_config_collapsible"):
                    self.say_app(focused_id, "_restore_config_collapsible")
                elif focused_id.endswith("_s3_config_collapsible"):
                    self.say_app(focused_id, "_s3_config_collapsible")
                else:
                    self.say_phrase(focused_id)
            else:
                # play phrase "Element is..."
                self.say(audio_file=self.element_audio)

                if "k3s" in focused_id:
                    self.say(audio_file=self.k3s_audio)
                    focused_id = focused_id.replace("k3s_", "")
                if "kind" in focused_id:
                    self.say(audio_file=path.join(self.cluster_audio, 'kind.mp3'))
                    focused_id = focused_id.replace("kind_", "")

                # state the ID of the tabbed content out loud
                self.say_phrase(f'{focused_id}.mp3')

                # state the phrase for "selected tab is" ID of the tab
                self.say_phrase('element_tab.mp3')

                focused_id = focused.parent.active_pane.id.replace("-", "_")
                if "k3s" in focused_id:
                    self.say(audio_file=self.k3s_audio)
                    focused_id = focused_id.replace("k3s_", "")
                if "kind" in focused_id:
                    self.say(audio_file=path.join(self.cluster_audio, 'kind.mp3'))
                    focused_id = focused_id.replace("kind_", "")

                # state the ID of the tabbed content out loud
                self.say_phrase(f'{focused_id}.mp3')
        else:
            self.log("🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗")
            self.log(focused_id)
            self.log("🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗🆗")
            # play the basic beginning of the sentence "Element is..."
            self.say(audio_file=self.element_audio)
            # if k3s is in the text to play, play that seperately
            if "k3s" in focused_id:
                self.say(audio_file=self.k3s_audio)
                focused_id = focused_id.replace("k3s_", "")

            if focused_id.endswith("_app_widget"):
                self.say_app(focused_id, "_app_widget")

            elif isinstance(focused, Input):
                self.say_input(focused_id)

            elif isinstance(focused, Button):
                self.say_button(focused_id)

            # if this is a switch of any kind
            elif isinstance(focused, Switch):
                self.say_switch(focused_id, focused.value)

            # if this is an app inputs widget container, we need to get the app
            # name and then read that first before the name of the vertical scroll
            elif isinstance(focused, VerticalScroll):
                if focused_id.endswith("_argo_config_container"):
                    self.say_app(focused_id, "_argo_config_container")
                else:
                    self.say_phrase(f'{focused_id}.mp3')

            # if this is a dropdown menu, use the special method we have for that
            elif isinstance(focused, Select):
                self.say_drop_down_menu(focused_id, focused.value)

            # if this is a selection list, such as the apps list
            elif isinstance(focused, SelectionList):
                self.say_phrase(f'{focused_id}.mp3')
                # get the actual highlighted app
                highlighted_idx = focused.highlighted
                if not highlighted_idx:
                    highlighted_idx = 0
                    self.say_phrase("first_app_is.mp3")
                else:
                    self.say_phrase("highlighted.mp3")
                highlighted_app = focused.get_option_at_index(highlighted_idx).value
                # say name of app
                self.say(audio_file=path.join(self.apps_audio, f'{highlighted_app}.mp3'))

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

        # TODO: make node name, node labels, and node taints more capable
        # right now just says um i don't know that word
        if data_table.id == "nodes-data-table":
            # then play the row of the table
            self.say_phrase('row.mp3')

            row_column3 = row[2].plain.strip()
            row_column4 = row[3].plain.strip()
            row_column5 = row[4].plain.strip()
            row_column6 = row[5].plain.strip()
            column3 = columns[2].label
            column4 = columns[3].label
            column5 = columns[4].label
            column6 = columns[5].label

            # node name
            self.say_phrase('node.mp3')
            self.say_phrase('um.mp3')

            # node type
            self.say_phrase('node_type.mp3')
            if row_column2 == "worker":
                self.say_phrase("worker.mp3")
            elif row_column2 == "control_plane":
                self.say_phrase("control_plane.mp3")

            # ssh port
            self.say_phrase('ssh_port.mp3')
            if len(row_column3) == 4:
                # split into two numbers
                first_num = row_column3[:2]
                second_num = row_column3[2:]
                self.say(audio_file=path.join(self.tts_files, f'numbers/{first_num}.mp3'))
                self.say(audio_file=path.join(self.tts_files, f'numbers/{second_num}.mp3'))
            else:
                self.say(audio_file=path.join(self.tts_files, f'numbers/{column3}.mp3'))

            # ssh key
            self.say_phrase('ssh_key.mp3')
            self.say_phrase(f'{column4}.mp3')

            # node labels
            self.say_phrase('node_labels.mp3')
            self.say_phrase('um.mp3')

            # node taints
            self.say_phrase('node_taints.mp3')
            self.say_phrase('um.mp3')

        elif data_table.id == "invalid-apps-table":
            # then play the row of the table
            self.say_phrase('row.mp3')

            # say the application field
            application = row_column1.replace(" ", "_")
            self.say(audio_file=path.join(self.apps_audio, f"{application}.mp3"))

            # say the invalid fields
            self.say_phrase("invalid_fields.mp3")
            invalid_fields = row_column2.split(", ")
            for field in invalid_fields:
                if "smtp" in field:
                    # split string on _ into list of words
                    sections = field.split("_")

                    # remove _input from final string immediately
                    if "input" in sections:
                        sections.pop()

                    # get the index of "smtp" in the list
                    smtp_index = sections.index("smtp")

                    # say S.M.T.P.
                    self.say_phrase("smtp.mp3")
                    noun = sections[smtp_index + 1:][0]

                    # say the SMTP noun such as hostname or user
                    self.say_phrase(f"{noun}.mp3")
                elif "s3" in field:
                    # split string on _ into list of words
                    sections = field.split("_")

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
                else:
                    self.say_phrase(f"{field}.mp3")

        elif data_table.id == "key-mappings-table":
            # then play the row of the table
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
                for name in row_column1.split("-"):
                    if name:
                        self.say(audio_file=path.join(self.cluster_audio, f'{name}.mp3'))

                # distro name
                self.say_phrase('distro.mp3')
                self.say(audio_file=path.join(self.cluster_audio, f'{row_column2}.mp3'))

                # version
                self.say_phrase('version.mp3')

                if row_column3 == "unknown":
                    self.say(audio_file=path.join(self.tts_files,
                                       "phrases/unknown_version.mp3"))
                else:
                    version = row_column3.replace("+k3s1",
                                                  "").lstrip("v").split(".")
                    last_item = version[-1]
                    for number in version:
                        self.say(audio_file=path.join(self.tts_files,
                                           f'numbers/{number}.mp3'))
                        # say "point" between numbers
                        if number != last_item:
                            self.say_phrase('point.mp3')

                # say what platform we're running on
                self.say_phrase('platform.mp3')
                if row_column4 == "linux/arm64":
                    self.say(audio_file=path.join(self.cluster_audio, 'linux_arm.mp3'))
                elif row_column4 == "linux/amd64":
                    self.say(audio_file=path.join(self.cluster_audio, 'linux_amd.mp3'))
                elif row_column4 == "Darwin/arm64":
                    self.say(audio_file=path.join(self.cluster_audio, 'macos_arm.mp3'))
                else:
                    self.say(audio_file=path.join(self.tts_files, 'phrases/um.mp3'))

    def on_focus(self, event: DescendantFocus) -> None:
        """
        on focus, say the id of each element and the value or label if possible
        """
        # first ring the bell if the user would like that
        if self.bell_on_focus:
            self.app.bell()

        if self.speak_on_focus and self.speech_program:
            id = event.widget.id
            self.say(text=f"element is {id}")

            # input fields
            if isinstance(event.widget, Input):
                content = event.widget.value
                placeholder = event.widget.placeholder
                if content:
                    self.say(text=f"value is {content}")
                elif placeholder:
                    self.say(text=f"place holder text is {placeholder}")

            # buttons
            elif isinstance(event.widget, Button):
                self.say(text=f"button text is {event.widget.label}")

            # switches
            elif isinstance(event.widget, Switch) or isinstance(event.widget,
                                                                Select):
                self.say(text=f"value is {event.widget.value}")

            # also read the tooltip if there is one
            tooltip = event.widget.tooltip
            if tooltip:
                self.say(text=f"tooltip is {tooltip}")

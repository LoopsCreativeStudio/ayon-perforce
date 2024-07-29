"""Perforce Sync PreLaunch Hook."""
import re
import subprocess
from typing import Optional, Union, Dict

from qtpy.QtWidgets import QApplication, QLabel, QPushButton
from qtpy.QtGui import QIcon
from qtpy.QtCore import Qt

from ayon_core.lib import Logger
from ayon_core.resources import get_ayon_icon_filepath
from ayon_core.style import load_stylesheet
from ayon_core.tools.utils import ErrorMessageBox

from ayon_applications import (
    PreLaunchHook, LaunchTypes, ApplicationLaunchFailed
)

class PerforceErrorMessageBox(ErrorMessageBox):
    """Perforce Error Message Box."""
    def __init__(
        self,
        p4settings: Dict[str, Union[str, bool]],
        exc_msg: str,
        msg_type: str = "ERROR",
    ) -> None:
        self._p4settings = p4settings
        self._exc_msg = exc_msg
        self._msg_type = msg_type
        self.log = Logger.get_logger("PerforceResolve")
        super().__init__(
            f"Perforce {self._msg_type}", QApplication.activeWindow(),
        )
        self.setModal(True)
        self.setWindowIcon(QIcon(get_ayon_icon_filepath()))
        self.setStyleSheet(load_stylesheet())

        # get ok button
        footer_layout = self._footer_widget.layout()
        self.ok_btn = footer_layout.itemAt(2).widget()
        self.ok_btn.setText("Skip")

        # create resolve button
        self.resolve_btn = QPushButton("Resolve", self)
        self.resolve_btn.clicked.connect(self.resolve_warning)
        self.resolve_btn.hide()
        footer_layout.addWidget(self.resolve_btn, 0)

        if msg_type == "Warning":
            self.ok_btn.setText("Skip")
            self.resolve_btn.show()

    def _create_top_widget(self, parent_widget) -> QLabel:
        label_widget = QLabel(parent_widget)
        top_msg = (
            "Perforce failed to perform sync:"
            if self._msg_type == "ERROR"
            else "Perforce complete sync with warning messages:"
        )
        label_widget.setText(f"<span style='font-size:16pt;'>{top_msg}</span>")
        return label_widget

    def _create_content(self, content_layout) -> None:
        content_layout.addWidget(self._create_line())
        content_html = [
            f"<span style='font-weight:bold;'>{key}:</span> {value}"
            for key, value in self._p4settings.items()
            if key != "bypass" and (key != "P4USER" or value is not None)
        ]
        content_html.append(
            f"<br>{self.convert_text_for_html(self._exc_msg)}"
        )
        content_label = QLabel("<br>".join(content_html), self)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setCursor(Qt.IBeamCursor)
        content_layout.addWidget(content_label)

    def force_sync(self, depot_file:str) -> subprocess.CompletedProcess:
        """Force Perforce sync for the give depot file.

        Args:
            depot_file (str): the depot file to update.

        Returns:
            subprocess.CompletedProcess: The process result.
        """
        return subprocess.run(
            ['p4', 'sync', '-f', f'{depot_file}#head'],
            shell=True,
            text=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            errors='replace',
        )

    def resolve_warning(self) -> None:
        """Resolve Perforce sync warning.
        """
        result_html = ["<span style='font-size:14pt;'>Resolve Result:</span>"]
        result_failed = False
        for line in self._exc_msg.splitlines():
            wrn_match = re.match(
                r"^(?P<depotfile>.*)#\d+"
                r" - can't (overwrite existing|update modified) file "
                r"(?P<localfile>.*)$",
                line,
            )
            if not wrn_match:
                continue
            depot_file = wrn_match.group("depotfile")
            self.log.info(f"sync -f {depot_file}")
            result = self.force_sync(depot_file)
            stdout_result = result.stdout.strip()
            if " - refreshing " in stdout_result:
                self.log.info(f">>> {stdout_result}")
                color_result = "YellowGreen"
            else:
                self.log.info(f"!!! {stdout_result}")
                color_result = "Orange"
                result_failed = True

            result_html.append(
                f"<span style='color:{color_result};'>"
                f"{self.convert_text_for_html(stdout_result)}</span>"
            )

        resolve_label = QLabel("<br>".join(result_html), self)
        resolve_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        resolve_label.setCursor(Qt.IBeamCursor)
        content_layout = self._content_widget.layout()
        content_layout.insertWidget(2, self._create_line())
        content_layout.insertWidget(3, resolve_label)
        if not result_failed:
            self.resolve_btn.hide()
            self.ok_btn.setText("Ok")
        else:
            self.resolve_btn.setDisabled(True)

class PerforceSync(PreLaunchHook):
    """Run Perforce Sync for the given project config.
    """
    order = -1
    launch_types = {LaunchTypes.local}

    def _get_p4settings(self) -> Optional[Dict[str, Union[str, bool]]]:
        perforce_settings = self.data["project_settings"]["perforce"]
        perforce_hosts = {
            host["name"]: host["bypass"]
            for host in perforce_settings["hosts"]
        }

        if self.host_name not in perforce_hosts:
            return None

        p4port = (
            perforce_settings.get("p4port")
            or self.data["env"].get("P4PORT")
        )
        p4client = (
            perforce_settings.get("p4client")
            or self.data["env"].get("P4CLIENT")
            or "{project_name}_{COMPUTERNAME}_{USERNAME}"
        )
        p4user = (
            perforce_settings.get("p4user")
            or self.data["env"].get("P4USER")
        )

        if p4client.count("{") == p4client.count("}") > 0:
            p4client = p4client.format(
                project_name=self.data["project_name"],
                **self.data["env"]
            )
        if perforce_settings.get("p4client_lower"):
            p4client = p4client.lower()

        return {
            "P4PORT": p4port or None,
            "P4CLIENT": p4client or None,
            "P4USER": p4user or None,
            "bypass": perforce_hosts.get(self.host_name, False)
        }

    def run_perforce_sync(
        self, p4settings: Dict[str, Union[str, bool]]
    ) -> None:
        """Run Perforce Sync using the given settings.

        Args:
            p4settings (Dict[str, Union[str, bool]]): The perforce settings.
        """
        self.log.info("[SYNC PERFORCE PROJECT]")
        with subprocess.Popen(
            ['p4', '-I', 'sync', '-s', '-q'],
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            errors='replace',
        ) as process:
            complete_log = ""
            capture_log = ""
            last_percent = None
            read_log = None
            while True:
                read_log = process.stdout.read(1)
                if read_log == "" and not process.poll() is None:
                    break
                capture_log += read_log

                percent_match = re.search(r"(\d{1,3}%|finishing)", capture_log)
                warning_match = re.search(
                    r"(.* can't (overwrite|update) .*)\n", capture_log, re.M
                )
                if percent_match:
                    current_percent = percent_match.group(1)
                    if last_percent != current_percent:
                        self.log.info(f"sync {current_percent}")
                        last_percent = current_percent
                    capture_log = ""
                elif warning_match:
                    self.log.info(f"*** WRN: {warning_match.group(1)}")
                    complete_log += capture_log
                    capture_log = ""
                elif capture_log.endswith("\n"):
                    if capture_log.strip():
                        complete_log += capture_log.strip() + "\n"
                    capture_log = ""
                elif capture_log == "sync ":
                    capture_log = ""

            if process.returncode != 0:
                error_msg = (
                    "Perforce sync process return non-zero code: "
                    f"{process.returncode}"
                )
                self.log.error(error_msg)
                box = PerforceErrorMessageBox(
                    p4settings, f"{complete_log}\n{error_msg}"
                )
                box.exec_()
                if not p4settings["bypass"]:
                    raise ApplicationLaunchFailed(
                        "Couldn't run the application! Perforce sync failed!"
                    )
            elif complete_log:
                box = PerforceErrorMessageBox(
                    p4settings,
                    complete_log,
                    "Warning",
                )
                box.exec_()

    def execute(self, *_args, **_kwargs) -> None:
        """Execute prelaunch hook process."""

        p4settings = self._get_p4settings()

        if p4settings is None:
            return

        for key, value in p4settings.items():
            self.log.info(f"{key}={value}")

        if not p4settings["P4PORT"] or not p4settings["P4CLIENT"]:
            error_msg = "Incomplete p4 configuration: skip sync!"
            self.log.error(error_msg)
            if not p4settings["bypass"]:
                raise ApplicationLaunchFailed(
                    "Couldn't run the application! Perforce config error!"
                )
            box = PerforceErrorMessageBox(p4settings, error_msg)
            box.exec_()
            return

        for p4env in ("P4PORT", "P4CLIENT", "P4USER"):
            if p4settings[p4env] is not None:
                subprocess.run(
                    ["p4", "set", f"{p4env}={p4settings[p4env]}"], check=True
                )

        self.run_perforce_sync(p4settings)

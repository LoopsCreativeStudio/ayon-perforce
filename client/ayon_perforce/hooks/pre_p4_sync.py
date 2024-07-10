
import re
import subprocess

from ayon_applications import (
    PreLaunchHook, LaunchTypes, ApplicationLaunchFailed
)

class PerforceSync(PreLaunchHook):
    """Run Perforce Sync for the given project config.
    """
    order = -1
    launch_types = {LaunchTypes.local}

    def execute(self, *args, **kwargs):

        perforce_settings = self.data["project_settings"]["perforce"]

        perforce_hosts = {
            host["name"]: host["bypass"]
            for host in perforce_settings["hosts"]
        }

        if self.host_name not in perforce_hosts:
            return

        host_bypass = perforce_hosts[self.host_name]

        p4_port = (
            perforce_settings.get("p4port")
            or self.data["env"].get("P4PORT")
        )
        p4_client = (
            perforce_settings.get("p4client")
            or self.data["env"].get("P4CLIENT")
            or "{project_name}_{COMPUTERNAME}_{USERNAME}"
        )
        p4_user = (
            perforce_settings.get("p4user")
            or self.data["env"].get("P4USER")
        )

        if p4_client.count("{") == p4_client.count("}") > 0:
            p4_client = p4_client.format(
                project_name=self.data["project_name"],
                **self.data["env"]
            )

        if perforce_settings.get("p4client_lower"):
            p4_client = p4_client.lower()

        self.log.info(f"P4PORT={p4_port or None}")
        self.log.info(f"P4CLIENT={p4_client or None}")
        self.log.info(f"P4USER={p4_user or None}") 

        if not p4_port or not p4_client:
            self.log.warning("incomplete p4 configuration: skip sync !")
            if not host_bypass:
                raise ApplicationLaunchFailed(
                    "Couldn't run the application! Perforce config error!"
                )

        subprocess.run(["p4", "set", f"P4PORT={p4_port}"], check=True)
        subprocess.run(["p4", "set", f"P4CLIENT={p4_client}"], check=True)
        if p4_user:
            subprocess.run(["p4", "set", f"P4USER={p4_user}"], check=True)

        # start sync
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
            capture_log = ""
            last_percent = None
            while process.poll() is None:
                capture_log += process.stdout.read(1)
                percent_match = re.search(r"\d{1,3}%|finishing", capture_log)
                if percent_match:
                    current_percent = percent_match.group(0)
                    if last_percent != current_percent:
                        self.log.info(f"sync {current_percent}")
                        last_percent = current_percent
                    capture_log = ""
            if process.returncode != 0:
                self.log.info(capture_log + process.stdout.read())
                self.log.warning("sync error !")
                if not host_bypass:
                    raise ApplicationLaunchFailed(
                        "Couldn't run the application! Perforce sync failed!"
                    )

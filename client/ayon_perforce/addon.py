

import os

from ayon_core.addon import AYONAddon
from .version import __version__

PERFORCE_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class PerforceAddon(AYONAddon):
    """Perfrorce Addon
    """
    name = "perforce"
    version = __version__
    label = "Perforce"

    def initialize(self, module_settings):
        self.enabled = True

    def get_launch_hook_paths(self, app):
        """Implementation for applications launch hooks.

        Returns:
            (str): full absolut path to directory with hooks for the module
        """
        return os.path.join(PERFORCE_MODULE_DIR, "hooks")

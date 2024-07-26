"""Perforce Addon Settings Module."""
from typing import List

from ayon_server.settings import BaseSettingsModel, SettingsField

DEFAULT_VALUES = {
    "p4port": "",
    "p4client": "{project_name}_{COMPUTERNAME}_{USERNAME}",
    "p4client_lower": True,
    "p4user": "",
    "hosts": [],
}


class HostItemModel(BaseSettingsModel):
    """Host item model for Perforce settings."""
    _layout = "compact"
    name: str = SettingsField("", title="Host name")
    bypass: bool = SettingsField(False, title="Bypass permission")


class PerforceSettings(BaseSettingsModel):
    """Perforce project settings."""
    enabled: bool = SettingsField(True)
    hosts: List[HostItemModel] = SettingsField(
        default_factory=list,
        title="Hosts",
        description=(
            "Sync Preforce for the given host names. "
            "Bypass set to True allow host to launch even if sync fails."
        ),
    )
    p4port: str = SettingsField(
        "",
        title="P4Port",
        description="Mendatory",
        section="P4Config",
    )
    p4client: str = SettingsField(
        "",
        title="P4Client",
        description=(
            "Client pattern use 'project_name' key and environment variables."
        ),
    )
    p4client_lower: bool = SettingsField(
        True,
        title="Force P4Client to Lowercase",
    )
    p4user: str = SettingsField(
        "",
        title="P4User",
        description="Optional, let Perforce default behavior if not set.",
    )

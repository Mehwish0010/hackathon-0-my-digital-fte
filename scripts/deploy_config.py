"""
Deployment Configuration for AI Employee.

Controls which services run based on deployment mode (cloud/local/hybrid).
All other Platinum-tier scripts import from this module.

Config via env vars:
    DEPLOYMENT_MODE   - "local" | "cloud" | "hybrid" (default: "local")
    CLOUD_AGENT_ID    - Identifier for the cloud agent (default: "cloud")
    LOCAL_AGENT_ID    - Identifier for the local agent (default: "local")
    VAULT_GIT_REMOTE  - Git remote URL for vault sync
    ENABLE_*          - Feature flags for individual services
"""

import os
from enum import Enum


class DeploymentMode(Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


def get_mode() -> DeploymentMode:
    """Get the current deployment mode from DEPLOYMENT_MODE env var."""
    raw = os.environ.get("DEPLOYMENT_MODE", "local").lower().strip()
    try:
        return DeploymentMode(raw)
    except ValueError:
        return DeploymentMode.LOCAL


def is_cloud() -> bool:
    return get_mode() == DeploymentMode.CLOUD


def is_local() -> bool:
    return get_mode() == DeploymentMode.LOCAL


def is_hybrid() -> bool:
    return get_mode() == DeploymentMode.HYBRID


def get_agent_id() -> str:
    """Return the agent ID for the current deployment mode."""
    mode = get_mode()
    if mode == DeploymentMode.CLOUD:
        return os.environ.get("CLOUD_AGENT_ID", "cloud")
    elif mode == DeploymentMode.LOCAL:
        return os.environ.get("LOCAL_AGENT_ID", "local")
    else:
        return os.environ.get("LOCAL_AGENT_ID", "local")


def get_vault_git_remote() -> str:
    """Return the Git remote URL for vault sync."""
    return os.environ.get("VAULT_GIT_REMOTE", "")


def _env_flag(name: str, default: bool = True) -> bool:
    """Read a boolean feature flag from env."""
    val = os.environ.get(name, "").lower().strip()
    if val in ("0", "false", "no", "off"):
        return False
    if val in ("1", "true", "yes", "on"):
        return True
    return default


# Service definitions per zone
CLOUD_SERVICES = [
    "gmail_watcher",
    "social_media_server",
    "ceo_briefing",
    "social_media_summarizer",
    "vault_sync",
    "cloud_agent",
]

LOCAL_SERVICES = [
    "approval_watcher",
    "linkedin_poster",
    "facebook_poster",
    "twitter_poster",
    "odoo_server",
    "email_server",
    "vault_sync",
    "local_agent",
]


def get_zone_services() -> list[str]:
    """Return the list of services that should run in the current zone."""
    mode = get_mode()
    if mode == DeploymentMode.CLOUD:
        services = list(CLOUD_SERVICES)
    elif mode == DeploymentMode.LOCAL:
        services = list(LOCAL_SERVICES)
    else:
        # Hybrid — run everything
        services = list(set(CLOUD_SERVICES + LOCAL_SERVICES))

    # Apply per-service feature flags
    filtered = []
    for svc in services:
        flag_name = f"ENABLE_{svc.upper()}"
        if _env_flag(flag_name, default=True):
            filtered.append(svc)

    return filtered


def should_run(service_name: str) -> bool:
    """Check if a specific service should run in the current deployment mode."""
    return service_name in get_zone_services()


def get_sync_interval() -> int:
    """Return vault sync interval in seconds (default 60)."""
    try:
        return int(os.environ.get("VAULT_SYNC_INTERVAL", "60"))
    except ValueError:
        return 60


def get_config_summary() -> dict:
    """Return a summary of the current deployment configuration."""
    return {
        "mode": get_mode().value,
        "agent_id": get_agent_id(),
        "vault_git_remote": get_vault_git_remote() or "(not set)",
        "sync_interval": get_sync_interval(),
        "active_services": get_zone_services(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_config_summary(), indent=2))

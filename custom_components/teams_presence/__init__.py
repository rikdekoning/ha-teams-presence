"""Microsoft Teams Presence integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    GRAPH_PRESENCE_URL,
    PLATFORMS,
    UPDATE_INTERVAL,
)
from .token_manager import TokenManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Teams Presence from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    token_manager = TokenManager(hass, entry)

    async def async_fetch_presence():
        """Fetch presence data from Microsoft Graph API."""
        try:
            token = await token_manager.async_get_token()
        except Exception as err:
            raise ConfigEntryAuthFailed(f"Token refresh failed: {err}") from err

        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(GRAPH_PRESENCE_URL, headers=headers) as resp:
                    if resp.status == 401:
                        raise ConfigEntryAuthFailed("Access token rejected by Microsoft Graph")
                    if resp.status != 200:
                        raise UpdateFailed(f"Graph API returned status {resp.status}")
                    data = await resp.json()
                    return {
                        "availability": data.get("availability", "Unknown"),
                        "activity": data.get("activity", "Unknown"),
                        "out_of_office_settings": data.get("outOfOfficeSettings", {}),
                    }
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching presence: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_presence",
        update_method=async_fetch_presence,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "token_manager": token_manager,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

"""Sensor platform for Microsoft Teams Presence."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ACTIVITY_STATES,
    AVAILABILITY_STATES,
    CONF_USER_DISPLAY_NAME,
    CONF_USER_EMAIL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Map availability → icon
AVAILABILITY_ICONS = {
    "Available": "mdi:check-circle",
    "AvailableIdle": "mdi:check-circle-outline",
    "Away": "mdi:clock-outline",
    "BeRightBack": "mdi:keyboard-return",
    "Busy": "mdi:minus-circle",
    "BusyIdle": "mdi:minus-circle-outline",
    "DoNotDisturb": "mdi:minus-circle",
    "Offline": "mdi:circle-off-outline",
    "PresenceUnknown": "mdi:help-circle-outline",
}

# Map availability → colour for Home Assistant frontend
AVAILABILITY_COLORS = {
    "Available": "green",
    "AvailableIdle": "green",
    "Away": "yellow",
    "BeRightBack": "yellow",
    "Busy": "red",
    "BusyIdle": "red",
    "DoNotDisturb": "red",
    "Offline": "grey",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teams Presence sensors for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = [
        TeamsAvailabilitySensor(coordinator, entry),
        TeamsActivitySensor(coordinator, entry),
        TeamsOutOfOfficeSensor(coordinator, entry),
    ]
    async_add_entities(entities)


class TeamsPresenceBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Teams presence sensors."""

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._user_name = entry.data.get(CONF_USER_DISPLAY_NAME, "Teams User")
        self._user_email = entry.data.get(CONF_USER_EMAIL, "")

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info to group sensors under one device."""
        return {
            "identifiers": {(DOMAIN, self._user_email)},
            "name": f"Teams – {self._user_name}",
            "manufacturer": "Microsoft",
            "model": "Microsoft 365 Teams",
            "entry_type": "service",
        }


class TeamsAvailabilitySensor(TeamsPresenceBaseSensor):
    """Sensor representing the Teams availability state."""

    @property
    def unique_id(self) -> str:
        return f"{self._user_email}_availability"

    @property
    def name(self) -> str:
        return f"{self._user_name} Teams Availability"

    @property
    def state(self) -> str | None:
        if self.coordinator.data:
            raw = self.coordinator.data.get("availability", "PresenceUnknown")
            return AVAILABILITY_STATES.get(raw, raw)
        return None

    @property
    def icon(self) -> str:
        if self.coordinator.data:
            raw = self.coordinator.data.get("availability", "PresenceUnknown")
            return AVAILABILITY_ICONS.get(raw, "mdi:microsoft-teams")
        return "mdi:microsoft-teams"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        raw = self.coordinator.data.get("availability", "PresenceUnknown")
        return {
            "raw_availability": raw,
            "color": AVAILABILITY_COLORS.get(raw, "grey"),
            "user_email": self._user_email,
        }


class TeamsActivitySensor(TeamsPresenceBaseSensor):
    """Sensor representing the Teams activity state."""

    @property
    def unique_id(self) -> str:
        return f"{self._user_email}_activity"

    @property
    def name(self) -> str:
        return f"{self._user_name} Teams Activity"

    @property
    def state(self) -> str | None:
        if self.coordinator.data:
            raw = self.coordinator.data.get("activity", "PresenceUnknown")
            return ACTIVITY_STATES.get(raw, raw)
        return None

    @property
    def icon(self) -> str:
        if self.coordinator.data:
            activity = self.coordinator.data.get("activity", "")
            if activity in ("InACall", "InAConferenceCall", "InAMeeting"):
                return "mdi:phone-in-talk"
            if activity == "Presenting":
                return "mdi:presentation"
        return "mdi:microsoft-teams"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        return {
            "raw_activity": self.coordinator.data.get("activity", ""),
            "user_email": self._user_email,
        }


class TeamsOutOfOfficeSensor(TeamsPresenceBaseSensor):
    """Sensor representing out-of-office status."""

    @property
    def unique_id(self) -> str:
        return f"{self._user_email}_out_of_office"

    @property
    def name(self) -> str:
        return f"{self._user_name} Teams Out of Office"

    @property
    def state(self) -> str:
        if self.coordinator.data:
            ooo = self.coordinator.data.get("out_of_office_settings", {})
            return "on" if ooo.get("isOutOfOffice", False) else "off"
        return "off"

    @property
    def icon(self) -> str:
        return "mdi:beach" if self.state == "on" else "mdi:briefcase-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        ooo = self.coordinator.data.get("out_of_office_settings", {})
        return {
            "message": ooo.get("message", ""),
            "user_email": self._user_email,
        }

"""Config flow for Microsoft Teams Presence - Device Code Flow."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, CONF_TOKEN_EXPIRY, CONF_USER_DISPLAY_NAME, CONF_USER_EMAIL, DOMAIN
from .token_manager import TokenManager

_LOGGER = logging.getLogger(__name__)

GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"


async def _async_fetch_user_info(access_token: str) -> dict[str, str]:
    """Fetch display name and email from Graph /me endpoint."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(GRAPH_ME_URL, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    CONF_USER_DISPLAY_NAME: data.get("displayName", "Unknown"),
                    CONF_USER_EMAIL: data.get("userPrincipalName", ""),
                }
    return {CONF_USER_DISPLAY_NAME: "Teams User", CONF_USER_EMAIL: ""}


class TeamsPresenceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Microsoft Teams Presence."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise."""
        self._device_flow_data: dict[str, Any] = {}
        self._poll_task: asyncio.Task | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Start the device code flow and show the sign-in instructions."""
        errors: dict[str, str] = {}

        try:
            flow = await TokenManager.async_initiate_device_flow()
        except Exception as err:
            _LOGGER.error("Failed to start device code flow: %s", err)
            return self.async_abort(reason="device_flow_failed")

        self._device_flow_data = flow

        # Start polling for the token in the background
        self._poll_task = self.hass.async_create_task(
            self._async_wait_for_token(flow["device_code"], flow.get("interval", 5))
        )

        message = (
            f"**Step 1:** Open [{flow['verification_uri']}]({flow['verification_uri']}) in your browser\n\n"
            f"**Step 2:** Enter code: `{flow['user_code']}`\n\n"
            f"**Step 3:** Sign in with your Microsoft 365 account (MFA is supported)\n\n"
            f"**Step 4:** Return here and click **Submit** once you've signed in"
        )

        return self.async_show_form(
            step_id="device_code",
            data_schema=vol.Schema({}),
            description_placeholders={
                "verification_uri": flow["verification_uri"],
                "user_code": flow["user_code"],
                "message": message,
            },
            errors=errors,
        )

    async def async_step_device_code(self, user_input: dict[str, Any] | None = None):
        """User clicked Submit — check if we have a token yet."""
        if self._poll_task is None or not self._poll_task.done():
            # Still waiting — ask them to wait a moment
            return self.async_show_form(
                step_id="device_code",
                data_schema=vol.Schema({}),
                description_placeholders={
                    "verification_uri": self._device_flow_data.get("verification_uri", ""),
                    "user_code": self._device_flow_data.get("user_code", ""),
                    "message": "⏳ Still waiting for sign-in to complete. If you've signed in, click Submit again in a few seconds.",
                },
                errors={"base": "still_waiting"},
            )

        try:
            token_response = self._poll_task.result()
        except Exception as err:
            _LOGGER.error("Device code authentication failed: %s", err)
            return self.async_abort(reason="auth_failed")

        tokens = TokenManager.extract_tokens(token_response)
        user_info = await _async_fetch_user_info(tokens[CONF_ACCESS_TOKEN])

        # Prevent duplicate entries for the same account
        await self.async_set_unique_id(user_info[CONF_USER_EMAIL])
        self._abort_if_unique_id_configured()

        entry_data = {**tokens, **user_info}

        return self.async_create_entry(
            title=f"Teams – {user_info[CONF_USER_DISPLAY_NAME]}",
            data=entry_data,
        )

    async def _async_wait_for_token(self, device_code: str, interval: int) -> dict[str, Any]:
        """Background task: poll Microsoft until the user signs in."""
        return await TokenManager.async_poll_for_token(device_code, interval)

"""Token management for Microsoft Teams Presence - Device Code Flow."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    AUTHORITY,
    CLIENT_ID,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRY,
    SCOPES,
)

_LOGGER = logging.getLogger(__name__)

TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"
DEVICE_CODE_URL = f"{AUTHORITY}/oauth2/v2.0/devicecode"


class TokenManager:
    """Manages access tokens using the OAuth2 Device Code flow."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the token manager."""
        self.hass = hass
        self.entry = entry

    @staticmethod
    async def async_initiate_device_flow() -> dict[str, Any]:
        """Start the device code flow and return the user-facing code + verification URL."""
        payload = {
            "client_id": CLIENT_ID,
            "scope": " ".join(SCOPES),
        }
        _LOGGER.debug("Initiating device code flow with client_id=%s scopes=%s", CLIENT_ID, SCOPES)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(DEVICE_CODE_URL, data=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    text = await resp.text()
                    _LOGGER.debug("Device code response status=%s body=%s", resp.status, text)
                    if resp.status != 200:
                        raise Exception(f"Microsoft returned HTTP {resp.status}: {text}")
                    import json
                    return json.loads(text)
        except aiohttp.ClientError as err:
            raise Exception(f"Network error contacting Microsoft: {err}") from err

    @staticmethod
    async def async_poll_for_token(device_code: str, interval: int = 5) -> dict[str, Any]:
        """Poll Microsoft until the user completes sign-in. Returns token data."""
        payload = {
            "client_id": CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
        }
        deadline = time.time() + 900
        async with aiohttp.ClientSession() as session:
            while time.time() < deadline:
                await asyncio.sleep(interval)
                async with session.post(TOKEN_URL, data=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = await resp.json()
                    error = data.get("error")
                    if error == "authorization_pending":
                        continue
                    elif error == "slow_down":
                        interval += 5
                        continue
                    elif error:
                        _LOGGER.error("Token poll error: %s — %s", error, data.get("error_description", ""))
                        raise Exception(f"Device code polling error: {data.get('error_description', error)}")
                    return data
        raise Exception("Device code flow timed out — user did not complete sign-in within 15 minutes")

    async def async_get_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        data = dict(self.entry.data)
        expiry = data.get(CONF_TOKEN_EXPIRY, 0)

        if time.time() < expiry - 300:
            return data[CONF_ACCESS_TOKEN]

        _LOGGER.debug("Access token expiring soon, refreshing...")
        new_tokens = await self._async_refresh_token(data[CONF_REFRESH_TOKEN])

        updated = {
            **data,
            CONF_ACCESS_TOKEN: new_tokens["access_token"],
            CONF_TOKEN_EXPIRY: time.time() + new_tokens["expires_in"],
        }
        if "refresh_token" in new_tokens:
            updated[CONF_REFRESH_TOKEN] = new_tokens["refresh_token"]

        self.hass.config_entries.async_update_entry(self.entry, data=updated)
        return updated[CONF_ACCESS_TOKEN]

    @staticmethod
    async def _async_refresh_token(refresh_token: str) -> dict[str, Any]:
        """Use a refresh token to obtain a new access token."""
        payload = {
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join(SCOPES),
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(TOKEN_URL, data=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                if "error" in data:
                    _LOGGER.error("Token refresh error: %s — %s", data["error"], data.get("error_description", ""))
                    raise Exception(f"Token refresh failed: {data.get('error_description', data['error'])}")
                return data

    @staticmethod
    def extract_tokens(token_response: dict[str, Any]) -> dict[str, Any]:
        """Extract and normalise token fields from a raw token response."""
        return {
            CONF_ACCESS_TOKEN: token_response["access_token"],
            CONF_REFRESH_TOKEN: token_response.get("refresh_token", ""),
            CONF_TOKEN_EXPIRY: time.time() + token_response.get("expires_in", 3600),
        }

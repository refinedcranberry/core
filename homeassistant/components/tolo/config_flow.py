"""Config flow for tolo."""

from __future__ import annotations

import logging
from typing import Any

from tololib import ToloClient
from tololib.errors import ResponseTimedOutError
import voluptuous as vol

from homeassistant.components import dhcp
from homeassistant.components.dhcp import IP_ADDRESS, MAC_ADDRESS
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.device_registry import format_mac

from .const import DEFAULT_NAME, DEFAULT_RETRY_COUNT, DEFAULT_RETRY_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ToloSaunaConfigFlow(ConfigFlow, domain=DOMAIN):
    """ConfigFlow for TOLO Sauna."""

    VERSION = 1

    _discovered_host: str | None = None

    @staticmethod
    def _check_device_availability(host: str) -> bool:
        client = ToloClient(host)
        try:
            result = client.get_status_info(
                resend_timeout=DEFAULT_RETRY_TIMEOUT, retries=DEFAULT_RETRY_COUNT
            )
            return result is not None
        except ResponseTimedOutError:
            return False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

            device_available = await self.hass.async_add_executor_job(
                self._check_device_availability, user_input[CONF_HOST]
            )

            if not device_available:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME, data={CONF_HOST: user_input[CONF_HOST]}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    async def async_step_dhcp(self, discovery_info: dhcp.DhcpServiceInfo) -> FlowResult:
        """Handle a flow initialized by discovery."""
        await self.async_set_unique_id(format_mac(discovery_info[MAC_ADDRESS]))
        self._abort_if_unique_id_configured({CONF_HOST: discovery_info[IP_ADDRESS]})
        self._async_abort_entries_match({CONF_HOST: discovery_info[IP_ADDRESS]})

        device_available = await self.hass.async_add_executor_job(
            self._check_device_availability, discovery_info[IP_ADDRESS]
        )

        if device_available:
            self._discovered_host = discovery_info[IP_ADDRESS]
            return await self.async_step_confirm()
        return self.async_abort(reason="not_tolo_device")

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user-confirmation of discovered node."""
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: self._discovered_host})
            return self.async_create_entry(
                title=DEFAULT_NAME, data={CONF_HOST: self._discovered_host}
            )

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={CONF_HOST: self._discovered_host},
        )

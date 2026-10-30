"""Config flow for CocktailBerry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    CocktailBerryAuthError,
    CocktailBerryClient,
    CocktailBerryConnectionError,
    CocktailBerryError,
)
from .const import (
    CONF_ALLOW_PREPARE,
    CONF_MAKER_PASSWORD,
    CONF_MAX_HAND_ADD,
    DEFAULT_MAX_HAND_ADD,
    DEFAULT_PORT,
    DOMAIN,
)


async def _validate(hass: HomeAssistant, data: Mapping[str, Any]) -> dict[str, Any]:
    """Check the API answers and, if a password is given, that it is accepted."""
    client = CocktailBerryClient(
        async_get_clientsession(hass),
        data[CONF_HOST],
        data[CONF_PORT],
        data.get(CONF_MAKER_PASSWORD),
    )
    info = await client.get_info()
    if info.get("project_name") != "CocktailBerry":
        raise CocktailBerryError("Not a CocktailBerry API")
    return info


def _user_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Optional(
                CONF_MAKER_PASSWORD, description={"suggested_value": defaults.get(CONF_MAKER_PASSWORD)}
            ): str,
        }
    )


class CocktailBerryConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            try:
                info = await _validate(self.hass, user_input)
            except CocktailBerryConnectionError:
                errors["base"] = "cannot_connect"
            except CocktailBerryAuthError:
                errors["base"] = "invalid_auth"
            except CocktailBerryError:
                errors["base"] = "not_cocktailberry"
            else:
                return self.async_create_entry(
                    title=f"CocktailBerry ({user_input[CONF_HOST]})",
                    data=user_input,
                    description_placeholders={"version": info.get("version", "?")},
                )
        return self.async_show_form(
            step_id="user", data_schema=_user_schema(user_input or {}), errors=errors
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, CONF_MAKER_PASSWORD: user_input.get(CONF_MAKER_PASSWORD, "")}
            try:
                await _validate(self.hass, data)
            except CocktailBerryConnectionError:
                errors["base"] = "cannot_connect"
            except CocktailBerryError:
                errors["base"] = "invalid_auth"
            else:
                return self.async_update_reload_and_abort(entry, data=data)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Optional(CONF_MAKER_PASSWORD): str}),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await _validate(self.hass, user_input)
            except CocktailBerryConnectionError:
                errors["base"] = "cannot_connect"
            except CocktailBerryAuthError:
                errors["base"] = "invalid_auth"
            except CocktailBerryError:
                errors["base"] = "not_cocktailberry"
            else:
                return self.async_update_reload_and_abort(entry, data=user_input)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_user_schema(user_input or entry.data),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return CocktailBerryOptionsFlow()


class CocktailBerryOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ALLOW_PREPARE, default=options.get(CONF_ALLOW_PREPARE, False)
                    ): bool,
                    vol.Required(
                        CONF_MAX_HAND_ADD, default=options.get(CONF_MAX_HAND_ADD, DEFAULT_MAX_HAND_ADD)
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
                }
            ),
        )

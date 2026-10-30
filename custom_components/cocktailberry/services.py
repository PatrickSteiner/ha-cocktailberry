"""Services and the shared prepare logic for CocktailBerry."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import CocktailBerryAuthError, CocktailBerryError
from .const import (
    ATTR_ALCOHOL_FACTOR,
    ATTR_COCKTAIL,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_VIRGIN,
    ATTR_VOLUME,
    CONF_ALLOW_PREPARE,
    DOMAIN,
    SERVICE_PREPARE,
    SERVICE_REFRESH,
    SERVICE_STOP,
)
from .coordinator import CocktailBerryConfigEntry

PREPARE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(ATTR_COCKTAIL): vol.Any(cv.positive_int, cv.string),
        vol.Required(ATTR_VOLUME): vol.All(vol.Coerce(int), vol.Range(min=25, max=1000)),
        vol.Optional(ATTR_ALCOHOL_FACTOR, default=100): vol.All(vol.Coerce(int), vol.Range(min=0, max=200)),
        vol.Optional(ATTR_VIRGIN, default=False): cv.boolean,
    }
)
ENTRY_SCHEMA = vol.Schema({vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string})


def _get_entry(hass: HomeAssistant, entry_id: str | None) -> CocktailBerryConfigEntry:
    entries = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.state is ConfigEntryState.LOADED and (entry_id is None or e.entry_id == entry_id)
    ]
    if not entries:
        raise ServiceValidationError("No loaded CocktailBerry machine found")
    if entry_id is None and len(entries) > 1:
        raise ServiceValidationError("Several machines configured, please pass config_entry_id")
    return entries[0]


async def async_prepare(
    entry: CocktailBerryConfigEntry,
    cocktail: int | str,
    volume: int,
    alcohol_percent: int = 100,
    virgin: bool = False,
) -> dict[str, Any]:
    """Start a cocktail. Shared by the button and the service."""
    if not entry.options.get(CONF_ALLOW_PREPARE, False):
        raise ServiceValidationError(
            "Remote preparation is disabled. Enable it in the CocktailBerry integration options "
            "(and make sure a glass is under the outlet)."
        )
    rt = entry.runtime_data
    if rt.status.is_busy:
        raise ServiceValidationError("The machine is already preparing a cocktail")

    machine = rt.data.data
    # Accept a recipe ID or a name; a name that happens to be a number is tried as name first.
    found = machine.cocktail_by_name(str(cocktail))
    if found is None and str(cocktail).strip().isdigit():
        found = machine.cocktail_by_id(int(cocktail))
    if found is None:
        raise ServiceValidationError(f"Cocktail '{cocktail}' is not available with the current bottles")
    if found.get("only_virgin") and not virgin:
        virgin = True

    try:
        result = await rt.client.prepare_cocktail(
            found["id"], volume, alcohol_percent / 100, is_virgin=virgin
        )
    except CocktailBerryAuthError as err:
        entry.async_start_reauth(entry.runtime_data.data.hass)
        raise HomeAssistantError(f"Maker password rejected: {err}") from err
    except CocktailBerryError as err:
        raise HomeAssistantError(f"CocktailBerry refused the request: {err}") from err

    rt.status.pending_cocktail = found["name"]
    await rt.status.async_request_refresh()
    return result


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    async def _prepare(call: ServiceCall) -> None:
        entry = _get_entry(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        await async_prepare(
            entry,
            call.data[ATTR_COCKTAIL],
            call.data[ATTR_VOLUME],
            call.data[ATTR_ALCOHOL_FACTOR],
            call.data[ATTR_VIRGIN],
        )

    async def _stop(call: ServiceCall) -> None:
        entry = _get_entry(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        try:
            await entry.runtime_data.client.stop_preparation()
        except CocktailBerryError as err:
            raise HomeAssistantError(str(err)) from err
        await entry.runtime_data.status.async_request_refresh()

    async def _refresh(call: ServiceCall) -> None:
        entry = _get_entry(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        await entry.runtime_data.data.async_request_refresh()
        await entry.runtime_data.status.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_PREPARE, _prepare, schema=PREPARE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, _stop, schema=ENTRY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH, _refresh, schema=ENTRY_SCHEMA)

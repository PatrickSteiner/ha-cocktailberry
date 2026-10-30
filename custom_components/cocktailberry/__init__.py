"""The CocktailBerry integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import CocktailBerryClient
from .const import CONF_MAKER_PASSWORD, DOMAIN
from .coordinator import (
    CocktailBerryConfigEntry,
    CocktailBerryDataCoordinator,
    CocktailBerryRuntimeData,
    CocktailBerryStatusCoordinator,
)
from .services import async_setup_services

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CocktailBerryConfigEntry) -> bool:
    client = CocktailBerryClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_MAKER_PASSWORD),
    )
    data = CocktailBerryDataCoordinator(hass, entry, client)
    status = CocktailBerryStatusCoordinator(hass, entry, client, data)
    await data.async_config_entry_first_refresh()
    await status.async_config_entry_first_refresh()

    entry.runtime_data = CocktailBerryRuntimeData(client=client, data=data, status=status)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CocktailBerryConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: CocktailBerryConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

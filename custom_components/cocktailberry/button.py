"""Prepare / stop buttons for CocktailBerry."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import CocktailBerryError
from .const import CONF_ALLOW_PREPARE
from .coordinator import CocktailBerryConfigEntry
from .entity import CocktailBerryEntity
from .services import async_prepare


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CocktailBerryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    entities: list[ButtonEntity] = [StopButton(entry), RefreshButton(entry)]
    # The prepare button only exists when remote preparation was explicitly enabled.
    if entry.options.get(CONF_ALLOW_PREPARE, False):
        entities.append(PrepareButton(entry))
    async_add_entities(entities)


class PrepareButton(CocktailBerryEntity, ButtonEntity):
    _attr_icon = "mdi:glass-cocktail"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "prepare")

    async def async_press(self) -> None:
        c = self._entry.runtime_data.controls
        if not c.cocktail:
            raise ServiceValidationError("No cocktail selected")
        await async_prepare(self._entry, c.cocktail, c.volume, c.alcohol_percent, c.virgin)


class StopButton(CocktailBerryEntity, ButtonEntity):
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "stop")

    async def async_press(self) -> None:
        rt = self._entry.runtime_data
        try:
            await rt.client.stop_preparation()
        except CocktailBerryError as err:
            raise HomeAssistantError(str(err)) from err
        await rt.status.async_request_refresh()


class RefreshButton(CocktailBerryEntity, ButtonEntity):
    _attr_icon = "mdi:refresh"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "refresh")

    async def async_press(self) -> None:
        await self._entry.runtime_data.data.async_request_refresh()

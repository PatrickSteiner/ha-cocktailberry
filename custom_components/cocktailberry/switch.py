"""Virgin toggle for the next HA-started cocktail."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .coordinator import CocktailBerryConfigEntry
from .entity import CocktailBerryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CocktailBerryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([VirginSwitch(entry)])


class VirginSwitch(CocktailBerryEntity, SwitchEntity, RestoreEntity):
    _attr_icon = "mdi:glass-cocktail-off"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "virgin")
        self._controls = entry.runtime_data.controls

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last := await self.async_get_last_state():
            self._controls.virgin = last.state == "on"

    @property
    def is_on(self) -> bool:
        return self._controls.virgin

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._controls.virgin = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._controls.virgin = False
        self.async_write_ha_state()

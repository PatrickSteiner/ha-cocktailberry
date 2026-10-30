"""Cocktail selection for CocktailBerry."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import CocktailBerryConfigEntry, CocktailBerryDataCoordinator
from .entity import CocktailBerryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CocktailBerryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([CocktailSelect(entry)])


class CocktailSelect(
    CocktailBerryEntity, CoordinatorEntity[CocktailBerryDataCoordinator], SelectEntity, RestoreEntity
):
    """Lists the cocktails possible with the current bottles."""

    _attr_icon = "mdi:glass-cocktail"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        CoordinatorEntity.__init__(self, entry.runtime_data.data)
        CocktailBerryEntity.__init__(self, entry, "cocktail")
        self._controls = entry.runtime_data.controls

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) and last.state in self.options:
            self._controls.cocktail = last.state
        self._ensure_valid()

    @property
    def options(self) -> list[str]:
        return [c["name"] for c in self.coordinator.data.cocktails]

    @property
    def current_option(self) -> str | None:
        return self._controls.cocktail

    def _ensure_valid(self) -> None:
        opts = self.options
        if self._controls.cocktail not in opts:
            self._controls.cocktail = opts[0] if opts else None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._ensure_valid()
        super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        self._controls.cocktail = option
        self.async_write_ha_state()

"""Volume and strength for the next HA-started cocktail."""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.const import PERCENTAGE, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CocktailBerryConfigEntry
from .entity import CocktailBerryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CocktailBerryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([VolumeNumber(entry), StrengthNumber(entry)])


class VolumeNumber(CocktailBerryEntity, RestoreNumber):
    _attr_native_min_value = 25
    _attr_native_max_value = 1000
    _attr_native_step = 5
    _attr_native_unit_of_measurement = UnitOfVolume.MILLILITERS
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:cup-water"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "volume")
        self._controls = entry.runtime_data.controls

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) and last.native_value is not None:
            self._controls.volume = int(last.native_value)

    @property
    def native_value(self) -> float:
        return self._controls.volume

    async def async_set_native_value(self, value: float) -> None:
        self._controls.volume = int(value)
        self.async_write_ha_state()


class StrengthNumber(CocktailBerryEntity, RestoreNumber):
    """Alcohol factor: 100 % = recipe as is."""

    _attr_native_min_value = 10
    _attr_native_max_value = 200
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:percent"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "strength")
        self._controls = entry.runtime_data.controls

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) and last.native_value is not None:
            self._controls.alcohol_percent = int(last.native_value)

    @property
    def native_value(self) -> float:
        return self._controls.alcohol_percent

    async def async_set_native_value(self, value: float) -> None:
        self._controls.alcohol_percent = int(value)
        self.async_write_ha_state()

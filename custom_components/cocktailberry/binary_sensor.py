"""Binary sensors for CocktailBerry."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import CocktailBerryConfigEntry, CocktailBerryStatusCoordinator
from .entity import CocktailBerryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CocktailBerryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([MixingBinarySensor(entry)])


class MixingBinarySensor(
    CocktailBerryEntity, CoordinatorEntity[CocktailBerryStatusCoordinator], BinarySensorEntity
):
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:blender"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        CoordinatorEntity.__init__(self, entry.runtime_data.status)
        CocktailBerryEntity.__init__(self, entry, "mixing")

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_busy

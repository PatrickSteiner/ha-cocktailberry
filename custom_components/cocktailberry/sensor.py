"""Sensors for CocktailBerry."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import STATUS_OPTIONS
from .coordinator import (
    CocktailBerryConfigEntry,
    CocktailBerryDataCoordinator,
    CocktailBerryStatusCoordinator,
)
from .entity import CocktailBerryEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CocktailBerryConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    rt = entry.runtime_data
    entities: list[SensorEntity] = [
        StatusSensor(entry),
        ProgressSensor(entry),
        MessageSensor(entry),
        LastCocktailSensor(entry),
        AvailableCocktailsSensor(entry),
        VersionSensor(entry),
    ]
    entities += [BottleSensor(entry, b["number"]) for b in rt.data.data.bottles]
    async_add_entities(entities)


class _StatusBase(CocktailBerryEntity, CoordinatorEntity[CocktailBerryStatusCoordinator]):
    def __init__(self, entry: CocktailBerryConfigEntry, key: str) -> None:
        CoordinatorEntity.__init__(self, entry.runtime_data.status)
        CocktailBerryEntity.__init__(self, entry, key)


class _DataBase(CocktailBerryEntity, CoordinatorEntity[CocktailBerryDataCoordinator]):
    def __init__(self, entry: CocktailBerryConfigEntry, key: str) -> None:
        CoordinatorEntity.__init__(self, entry.runtime_data.data)
        CocktailBerryEntity.__init__(self, entry, key)


class StatusSensor(_StatusBase, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [s.lower() for s in STATUS_OPTIONS]
    _attr_icon = "mdi:glass-cocktail"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "status")

    @property
    def native_value(self) -> str | None:
        status = self.coordinator.data.get("status")
        return status.lower() if status else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "cocktail": self.coordinator.current_cocktail,
            "hand_adds": self.coordinator.data.get("hand_adds", []),
        }


class ProgressSensor(_StatusBase, SensorEntity):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:progress-clock"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "progress")

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("progress")


class MessageSensor(_StatusBase, SensorEntity):
    _attr_icon = "mdi:message-text-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "message")

    @property
    def native_value(self) -> str | None:
        msg = self.coordinator.data.get("message")
        return msg[:255] if msg else None


class LastCocktailSensor(_StatusBase, SensorEntity):
    """Only known for cocktails started from Home Assistant (the API does not report the name)."""

    _attr_icon = "mdi:glass-cocktail"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "last_cocktail")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.last_cocktail


class AvailableCocktailsSensor(_DataBase, SensorEntity):
    _attr_icon = "mdi:format-list-bulleted"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "available_cocktails")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.cocktails)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "cocktails": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "alcohol": c.get("alcohol"),
                    "virgin_available": c.get("virgin_available"),
                    "hand_ingredients": [i["name"] for i in c.get("ingredients", []) if i.get("hand")],
                }
                for c in self.coordinator.data.cocktails
            ]
        }


class VersionSensor(_DataBase, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:information-outline"

    def __init__(self, entry: CocktailBerryConfigEntry) -> None:
        super().__init__(entry, "version")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.info.get("version")


class BottleSensor(_DataBase, SensorEntity):
    """Fill level of one bottle slot in percent; ml values in the attributes."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:bottle-wine-outline"

    def __init__(self, entry: CocktailBerryConfigEntry, number: int) -> None:
        super().__init__(entry, "bottle")
        self._number = number
        self._attr_unique_id = f"{entry.entry_id}_bottle_{number}"
        self._attr_translation_placeholders = {"number": str(number)}

    def _bottle(self) -> dict[str, Any] | None:
        return next((b for b in self.coordinator.data.bottles if b["number"] == self._number), None)

    @property
    def native_value(self) -> float | None:
        bottle = self._bottle()
        ing = bottle.get("ingredient") if bottle else None
        if not ing or not ing.get("bottle_volume"):
            return None
        return round(100 * ing["fill_level"] / ing["bottle_volume"], 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        bottle = self._bottle()
        ing = (bottle or {}).get("ingredient") or {}
        return {
            "ingredient": ing.get("name"),
            "fill_level_ml": ing.get("fill_level"),
            "bottle_volume_ml": ing.get("bottle_volume"),
            "alcohol": ing.get("alcohol"),
            "pump_speed": ing.get("pump_speed"),
            "unit": ing.get("unit", UnitOfVolume.MILLILITERS),
        }

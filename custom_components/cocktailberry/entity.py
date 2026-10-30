"""Base entity for CocktailBerry."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import CocktailBerryConfigEntry


def device_info(entry: CocktailBerryConfigEntry) -> DeviceInfo:
    rt = entry.runtime_data
    info = rt.data.data.info if rt.data.data else {}
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="CocktailBerry",
        manufacturer="CocktailBerry (DIY)",
        model="Cocktail machine",
        sw_version=info.get("version"),
        configuration_url=rt.client.base_url.removesuffix("/api"),
    )


class CocktailBerryEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, entry: CocktailBerryConfigEntry, key: str) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = device_info(entry)

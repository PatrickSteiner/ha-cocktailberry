"""Data coordinators for CocktailBerry."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CocktailBerryAuthError, CocktailBerryClient, CocktailBerryError
from .const import (
    BUSY_STATES,
    CONF_MAX_HAND_ADD,
    DATA_SCAN_INTERVAL,
    DEFAULT_MAX_HAND_ADD,
    DOMAIN,
    EVENT_PREPARATION_ENDED,
    EVENT_PREPARATION_STARTED,
    STATUS_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class MachineData:
    """Slowly changing data: bottles, possible cocktails, version."""

    info: dict[str, Any]
    bottles: list[dict[str, Any]]
    cocktails: list[dict[str, Any]]

    def cocktail_by_name(self, name: str) -> dict[str, Any] | None:
        lowered = name.strip().lower()
        return next((c for c in self.cocktails if c["name"].lower() == lowered), None)

    def cocktail_by_id(self, cocktail_id: int) -> dict[str, Any] | None:
        return next((c for c in self.cocktails if c["id"] == cocktail_id), None)


@dataclass
class Controls:
    """Selections made in HA (select/number/switch entities) used by the prepare button."""

    cocktail: str | None = None
    volume: int = 250
    alcohol_percent: int = 100
    virgin: bool = False


class CocktailBerryDataCoordinator(DataUpdateCoordinator[MachineData]):
    """Polls bottles and cocktails every minute."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: CocktailBerryClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} data",
            update_interval=DATA_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> MachineData:
        max_hand = self.config_entry.options.get(CONF_MAX_HAND_ADD, DEFAULT_MAX_HAND_ADD)
        try:
            info = await self.client.get_info()
            bottles = await self.client.get_bottles()
            cocktails = await self.client.get_cocktails(only_possible=True, max_hand_add=max_hand)
        except CocktailBerryAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except CocktailBerryError as err:
            raise UpdateFailed(str(err)) from err
        cocktails = sorted(
            (c for c in cocktails if c.get("enabled", True) and c.get("is_allowed", True)),
            key=lambda c: c["name"].lower(),
        )
        return MachineData(info=info, bottles=bottles, cocktails=cocktails)


class CocktailBerryStatusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the preparation status every few seconds and fires events on transitions."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: CocktailBerryClient,
        data_coordinator: CocktailBerryDataCoordinator,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} status",
            update_interval=STATUS_SCAN_INTERVAL,
            always_update=False,
        )
        self.client = client
        self._data_coordinator = data_coordinator
        self._was_busy: bool | None = None
        # The status endpoint does not tell which cocktail is mixed; we know it only for HA-started ones.
        self.pending_cocktail: str | None = None
        self.current_cocktail: str | None = None
        self.last_cocktail: str | None = None

    @property
    def is_busy(self) -> bool:
        return bool(self.data) and self.data.get("status") in BUSY_STATES

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status = await self.client.get_status()
        except CocktailBerryError as err:
            raise UpdateFailed(str(err)) from err

        busy = status.get("status") in BUSY_STATES
        if self._was_busy is not None and busy != self._was_busy:
            if busy:
                self.current_cocktail = self.pending_cocktail
                self.hass.bus.async_fire(
                    EVENT_PREPARATION_STARTED,
                    {
                        "entry_id": self.config_entry.entry_id,
                        "cocktail": self.current_cocktail,
                        "status": status.get("status"),
                    },
                )
            else:
                self.last_cocktail = self.current_cocktail
                self.hass.bus.async_fire(
                    EVENT_PREPARATION_ENDED,
                    {
                        "entry_id": self.config_entry.entry_id,
                        "cocktail": self.current_cocktail,
                        "status": status.get("status"),
                        "message": status.get("message"),
                        "hand_adds": status.get("hand_adds", []),
                    },
                )
                self.current_cocktail = None
                # Fill levels changed: refresh bottles soon.
                self.hass.async_create_task(self._data_coordinator.async_request_refresh())
            self.pending_cocktail = None
        self._was_busy = busy
        return status


@dataclass
class CocktailBerryRuntimeData:
    client: CocktailBerryClient
    data: CocktailBerryDataCoordinator
    status: CocktailBerryStatusCoordinator
    controls: Controls = field(default_factory=Controls)


type CocktailBerryConfigEntry = ConfigEntry[CocktailBerryRuntimeData]

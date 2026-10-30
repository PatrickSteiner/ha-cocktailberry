"""Constants for the CocktailBerry integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "cocktailberry"

CONF_MAKER_PASSWORD: Final = "maker_password"
CONF_ALLOW_PREPARE: Final = "allow_prepare"
CONF_MAX_HAND_ADD: Final = "max_hand_add"

DEFAULT_PORT: Final = 8000
DEFAULT_MAX_HAND_ADD: Final = 3

# Status changes need to be picked up quickly, bottles/recipes only occasionally.
STATUS_SCAN_INTERVAL: Final = timedelta(seconds=3)
DATA_SCAN_INTERVAL: Final = timedelta(seconds=60)

# Status values of CocktailBerry's PrepareResult enum.
STATUS_IN_PROGRESS: Final = "IN_PROGRESS"
STATUS_WAITING_FOR_PAYMENT: Final = "WAITING_FOR_PAYMENT"
STATUS_FINISHED: Final = "FINISHED"
STATUS_OPTIONS: Final = [
    "VALIDATION_OK",
    "IN_PROGRESS",
    "FINISHED",
    "CANCELED",
    "NOT_ENOUGH_INGREDIENTS",
    "ADDON_ERROR",
    "WAITING_FOR_PAYMENT",
    "NO_WAITER_LOGGED_IN",
    "NO_GLASS_DETECTED",
]
BUSY_STATES: Final = {STATUS_IN_PROGRESS, STATUS_WAITING_FOR_PAYMENT}

EVENT_PREPARATION_STARTED: Final = f"{DOMAIN}_preparation_started"
EVENT_PREPARATION_ENDED: Final = f"{DOMAIN}_preparation_ended"

SERVICE_PREPARE: Final = "prepare_cocktail"
SERVICE_STOP: Final = "stop_preparation"
SERVICE_REFRESH: Final = "refresh"

ATTR_COCKTAIL: Final = "cocktail"
ATTR_VOLUME: Final = "volume"
ATTR_ALCOHOL_FACTOR: Final = "alcohol_factor"
ATTR_VIRGIN: Final = "virgin"
ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"

"""Async client for the CocktailBerry v2 REST API (FastAPI, served under /api)."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class CocktailBerryError(Exception):
    """Generic API error."""


class CocktailBerryConnectionError(CocktailBerryError):
    """Machine not reachable."""


class CocktailBerryAuthError(CocktailBerryError):
    """Wrong or missing maker password (403) or locked out (429)."""


class CocktailBerryRequestError(CocktailBerryError):
    """The API refused the request (e.g. cocktail not possible, machine busy)."""


class CocktailBerryClient:
    """Thin wrapper around the endpoints the integration needs."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        maker_password: str | None = None,
        timeout: float = 10,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}/api"
        self._password = maker_password or None
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @property
    def base_url(self) -> str:
        return self._base

    def _headers(self, protected: bool) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if protected and self._password:
            headers["x-maker-key"] = str(self._password)
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        protected: bool = False,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        url = f"{self._base}{path}"
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers(protected),
                params=params,
                json=json,
                timeout=self._timeout,
            ) as resp:
                data: Any
                try:
                    data = await resp.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    data = None
                if resp.status in (401, 403, 429):
                    raise CocktailBerryAuthError(_detail(data) or f"HTTP {resp.status}")
                if resp.status >= 400:
                    raise CocktailBerryRequestError(_detail(data) or f"HTTP {resp.status}")
                return data
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as err:
            raise CocktailBerryConnectionError(f"Cannot reach {url}: {err}") from err

    # --- read endpoints (unprotected) ---------------------------------------------------

    async def get_info(self) -> dict[str, Any]:
        """Return python_version, platform, project_name, version, startup_time."""
        return await self._request("GET", "/info")

    async def get_status(self) -> dict[str, Any]:
        """Return progress, message, status, hand_adds of the current preparation."""
        return await self._request("GET", "/cocktails/prepare/status")

    async def get_bottles(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/bottles")

    async def get_cocktails(self, only_possible: bool = True, max_hand_add: int = 3) -> list[dict[str, Any]]:
        return await self._request(
            "GET",
            "/cocktails",
            params={"only_possible": str(only_possible).lower(), "max_hand_add": max_hand_add, "scale": "true"},
        )

    # --- write endpoints (maker protected) ----------------------------------------------

    async def prepare_cocktail(
        self,
        cocktail_id: int,
        volume: int,
        alcohol_factor: float = 1.0,
        is_virgin: bool = False,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/cocktails/prepare/{cocktail_id}",
            protected=True,
            json={"volume": volume, "alcohol_factor": alcohol_factor, "is_virgin": is_virgin},
        )

    async def stop_preparation(self) -> dict[str, Any]:
        return await self._request("POST", "/cocktails/prepare/stop", protected=True)


def _detail(data: Any) -> str | None:
    if isinstance(data, dict):
        detail = data.get("detail") or data.get("message")
        if isinstance(detail, str):
            return detail
        if detail is not None:
            return str(detail)
    return None

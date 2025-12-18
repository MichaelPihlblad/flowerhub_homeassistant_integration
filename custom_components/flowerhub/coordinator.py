from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
try:  # Prefer explicit exception types from the client when available
    # Names below reflect common patterns; imports are guarded for safety
    from flowerhub_portal_api_client import (  # type: ignore
        AuthenticationError as FHAuthenticationError,  # noqa: F401
    )
except Exception:  # pragma: no cover - optional
    FHAuthenticationError = None  # type: ignore

for _name in (
    "AuthError",
    "TokenExpiredError",
    "TokenRefreshError",
    "InvalidTokenError",
    "UnauthorizedError",
    "ForbiddenError",
):
    try:
        globals()[f"FH{_name}"] = getattr(
            __import__("flowerhub_portal_api_client", fromlist=[_name]), _name
        )
    except Exception:  # pragma: no cover - optional
        globals()[f"FH{_name}"] = None


LOGGER = logging.getLogger(__name__)


class FlowerhubDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, update_interval, username: str | None = None, password: str | None = None):
        super().__init__(
            hass,
            LOGGER,
            name="flowerhub",
            update_method=self._async_update,
            update_interval=update_interval,
        )
        self.client = client
        self._username = username
        self._password = password
        self._first_update = True
        explicit_types = [
            FHAuthenticationError,
            globals().get("FHAuthError"),
            globals().get("FHTokenExpiredError"),
            globals().get("FHTokenRefreshError"),
            globals().get("FHInvalidTokenError"),
            globals().get("FHUnauthorizedError"),
            globals().get("FHForbiddenError"),
        ]
        self._auth_exception_types: tuple[type[Exception], ...] = tuple(
            t for t in explicit_types if isinstance(t, type)
        )
        if not self._auth_exception_types:
            self._auth_exception_types = self._detect_auth_exceptions()

        # If the client supports an auth error callback, hook it to schedule a reauth
        try:
            if hasattr(self.client, "set_auth_error_callback") and callable(getattr(self.client, "set_auth_error_callback")):
                self.client.set_auth_error_callback(self._on_auth_error)
            elif hasattr(self.client, "on_auth_error"):
                # Some clients expose a property callback
                setattr(self.client, "on_auth_error", self._on_auth_error)
        except Exception:  # pragma: no cover - best-effort wiring
            pass

    async def _async_update(self) -> dict[str, Any]:
        try:
            if self._first_update:
                LOGGER.debug("Flowerhub coordinator running initial readout sequence")
                await self.client.async_readout_sequence()
                self._first_update = False
            else:
                LOGGER.debug("Flowerhub coordinator fetching asset data")
                await self.client.async_fetch_asset()
        except Exception as err:
            # Try to detect auth-related failures and recover automatically
            if self._is_auth_error(err):
                LOGGER.warning("Flowerhub auth error detected; attempting re-auth")
                try:
                    await self._reauth_and_prime()
                    LOGGER.info("Flowerhub re-authentication succeeded; data primed")
                except Exception as reauth_err:
                    raise UpdateFailed(f"Re-authentication failed: {reauth_err}") from reauth_err
            else:
                raise UpdateFailed(err) from err

        status = self.client.flowerhub_status
        asset_info = self.client.asset_info
        return {
            "status": status.status if status else None,
            "message": status.message if status else None,
            "last_updated": status.updated_at.isoformat()
            if status and status.updated_at
            else None,
            "inverter_name": asset_info.get("inverter", {}).get("name")
            if asset_info
            else None,
            "battery_name": asset_info.get("battery", {}).get("name")
            if asset_info
            else None,
            "power_capacity": asset_info.get("inverter", {}).get("powerCapacity")
            if asset_info
            else None,
            "energy_capacity": asset_info.get("battery", {}).get("energyCapacity")
            if asset_info
            else None,
            "fuse_size": asset_info.get("fuseSize") if asset_info else None,
            "is_installed": asset_info.get("isInstalled") if asset_info else None,
        }

    def _is_auth_error(self, err: Exception) -> bool:
        try:
            if self._auth_exception_types and isinstance(err, self._auth_exception_types):
                return True
        except Exception:
            pass
        text = str(err).lower()
        if any(code in text for code in ("401", "403", "unauthorized", "forbidden", "token", "expired")):
            return True
        name = err.__class__.__name__.lower()
        return "auth" in name or "token" in name

    def _detect_auth_exceptions(self) -> tuple[type[Exception], ...]:
        candidates = (
            "AuthenticationError",
            "AuthError",
            "TokenExpiredError",
            "TokenRefreshError",
            "InvalidTokenError",
            "UnauthorizedError",
            "ForbiddenError",
        )
        types: list[type[Exception]] = []
        try:
            import importlib

            mod = importlib.import_module("flowerhub_portal_api_client")
            for name in candidates:
                t = getattr(mod, name, None)
                if isinstance(t, type) and issubclass(t, Exception):
                    types.append(t)
        except Exception:
            pass
        return tuple(types)

    async def _reauth_and_prime(self) -> None:
        if not self._username or not self._password:
            # Cannot reauth without credentials
            raise RuntimeError("Missing credentials for re-authentication")
        # Perform full login and initial readout to restore state
        LOGGER.debug("Flowerhub performing re-login for coordinator recovery")
        await self.client.async_login(self._username, self._password)
        await self.client.async_readout_sequence()

    def _on_auth_error(self) -> None:
        # Schedule a background reauth; the next refresh will pick up data
        async def _do():
            try:
                await self._reauth_and_prime()
            except Exception as err:  # pragma: no cover
                LOGGER.warning("Auth callback reauth failed: %s", err)
            else:
                LOGGER.info("Flowerhub auth callback reauth succeeded")

        self.hass.async_create_task(_do())

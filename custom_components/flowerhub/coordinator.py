from __future__ import annotations

import logging
from time import monotonic
from typing import Any

from flowerhub_portal_api_client import AsyncFlowerhubClient
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
)
from homeassistant.helpers.issue_registry import (
    async_create_issue as ir_async_create_issue,
)
from homeassistant.helpers.issue_registry import (
    async_delete_issue as ir_async_delete_issue,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

try:  # Prefer explicit exception types from the client when available
    # Names below reflect common patterns; imports are guarded for safety
    from flowerhub_portal_api_client import (
        AuthenticationError as FHAuthenticationError,  # type: ignore
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


def _validate_asset_fetch_result(result: Any, context: str = "result") -> bool:
    """Validate that result matches AssetFetchResult TypedDict structure.

    Returns True if valid, raises UpdateFailed with details if invalid.
    """
    if not isinstance(result, dict):
        LOGGER.error(
            "Invalid %s type: expected dict (AssetFetchResult), got %s. "
            "This may indicate a library version mismatch.",
            context,
            type(result).__name__,
        )
        raise UpdateFailed(f"Library returned unexpected type: {type(result).__name__}")

    # Validate required keys from AssetFetchResult TypedDict
    required_keys = {"status_code", "asset_info", "flowerhub_status", "error"}
    missing_keys = required_keys - set(result.keys())

    if missing_keys:
        LOGGER.error(
            "Invalid %s structure: missing required keys %s. "
            "Present keys: %s. This may indicate a library version mismatch.",
            context,
            missing_keys,
            list(result.keys()),
        )
        raise UpdateFailed(f"Library response missing required fields: {missing_keys}")

    # Validate types of key fields
    if result.get("status_code") is not None and not isinstance(
        result["status_code"], int
    ):
        LOGGER.warning(
            "Invalid status_code type in %s: expected int, got %s",
            context,
            type(result["status_code"]).__name__,
        )

    return True


class FlowerhubDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass,
        client,
        update_interval,
        entry_id: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        super().__init__(
            hass,
            LOGGER,
            name="flowerhub",
            update_method=self._async_update,
            update_interval=update_interval,
        )
        self.client: AsyncFlowerhubClient = client
        self._username = username
        self._password = password
        self._first_update = True
        self._entry_id = entry_id or "default"
        self._consecutive_failures = 0
        self._repair_threshold = 3
        # Track last successful update time (monotonic seconds)
        self._last_success_monotonic: float | None = None
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
            callback = getattr(self.client, "set_auth_error_callback", None)
            if callable(callback):
                callback(self._on_auth_error)
            elif hasattr(self.client, "on_auth_error"):
                # Some clients expose a property callback
                setattr(self.client, "on_auth_error", self._on_auth_error)
        except Exception:  # pragma: no cover - best-effort wiring
            pass

    async def _async_update(self) -> dict[str, Any]:
        try:
            if self._first_update:
                LOGGER.debug("Flowerhub coordinator running initial readout sequence")
                readout = await self.client.async_readout_sequence()
                LOGGER.debug("Readout response: %s", readout)

                # Validate readout results - library returns TypedDict
                has_asset_info = bool(getattr(self.client, "asset_info", None))
                if not readout or not readout.get("asset_id"):
                    if not has_asset_info:
                        LOGGER.error(
                            "Initial readout failed: no asset_id returned. "
                            "Response type: %s",
                            type(readout).__name__,
                        )
                        raise UpdateFailed("Readout did not return a valid asset_id")

                # Check asset_resp TypedDict result from library (v0.4.0+)
                if readout and readout.get("asset_resp") is not None:
                    asset_result = readout.get("asset_resp")

                    if asset_result is None:
                        raise UpdateFailed("asset_resp missing from readout")

                    # Validate AssetFetchResult TypedDict structure
                    _validate_asset_fetch_result(asset_result, "asset_resp")

                    status_code = asset_result.get("status_code")
                    error = asset_result.get("error")

                    if status_code and status_code >= 400:
                        LOGGER.error(
                            "API returned error status %d during initial readout: %s",
                            status_code,
                            error or "no error details",
                        )
                        msg = "Asset fetch failed during readout"
                        if status_code:
                            msg += f" (HTTP {status_code})"
                        if error:
                            msg += f": {error}"
                        raise UpdateFailed(msg)

                    LOGGER.debug(
                        "Initial readout successful, status code: %d", status_code or 0
                    )
                self._first_update = False
            else:
                LOGGER.debug("Flowerhub coordinator fetching asset data")
                # async_fetch_asset returns AssetFetchResult TypedDict (v0.4.0+)
                result = await self.client.async_fetch_asset()

                if result is None:
                    raise UpdateFailed("Asset fetch returned no data")

                # Validate AssetFetchResult TypedDict structure
                _validate_asset_fetch_result(result, "async_fetch_asset result")

                status_code = result.get("status_code")
                error = result.get("error")
                has_asset_info = bool(getattr(self.client, "asset_info", None))

                if status_code and status_code >= 400:
                    LOGGER.error(
                        "API returned error status %d: %s",
                        status_code,
                        error or "no error details",
                    )
                    msg = f"Asset fetch failed (HTTP {status_code})"
                    if error:
                        msg += f": {error}"
                    raise UpdateFailed(msg)

                if not status_code and not has_asset_info:
                    LOGGER.warning(
                        "Asset fetch missing status_code with no cached asset_info. "
                        "Keys: %s",
                        list(result.keys()),
                    )
                    raise UpdateFailed(
                        "Asset fetch returned no status and client has no cached data"
                    )

                LOGGER.debug(
                    "Asset fetch successful, status code: %d", status_code or 0
                )
        except Exception as err:
            # Try to detect auth-related failures and recover automatically
            if self._is_auth_error(err):
                LOGGER.warning(
                    "Authentication error detected (type: %s): %s - attempting re-auth",
                    type(err).__name__,
                    err,
                )
                try:
                    await self._reauth_and_prime()
                    LOGGER.info(
                        "Automatic re-authentication successful; client state restored"
                    )
                except Exception as reauth_err:
                    LOGGER.error(
                        "Re-authentication failed: %s (%s)",
                        reauth_err,
                        type(reauth_err).__name__,
                    )
                    # Only prompt user if the failure is an auth error; otherwise
                    # treat as server error to avoid unnecessary credential prompts
                    if self._is_auth_error(reauth_err):
                        # Signal Home Assistant to start a reauth flow
                        raise ConfigEntryAuthFailed(
                            f"Re-authentication failed: {reauth_err}"
                        ) from reauth_err
                    # Non-auth reauth failures are treated as transient
                    self._consecutive_failures += 1
                    self._maybe_raise_server_issue(reauth_err)
                    raise UpdateFailed(reauth_err) from reauth_err
            else:
                LOGGER.error(
                    "Update failed with %s: %s", type(err).__name__, err, exc_info=True
                )
                # Track non-auth failures and raise/refresh repairs issue as needed
                self._consecutive_failures += 1
                self._maybe_raise_server_issue(err)
                raise UpdateFailed(err) from err

        status = self.client.flowerhub_status
        asset_info = self.client.asset_info or {}

        # Require flowerHubStatus.status to be present and not None or empty
        if not status:
            LOGGER.error("Client flowerhub_status is None after successful fetch")
            raise UpdateFailed("Flowerhub status object missing in client")

        if not status.status:
            LOGGER.error(
                "Flowerhub status.status field is empty. Status object: %s",
                status.__dict__ if hasattr(status, "__dict__") else status,
            )
            raise UpdateFailed("Flowerhub status field is empty in response data")
        inverter = asset_info.get("inverter", {}) or {}
        battery = asset_info.get("battery", {}) or {}
        # Any success clears server failure tracking and issue
        if self._consecutive_failures:
            self._clear_server_issue()
            self._consecutive_failures = 0
        # Mark last successful update timestamp
        self._last_success_monotonic = monotonic()
        return {
            # Status info
            "status": status.status if status else None,
            "message": status.message if status else None,
            "last_updated": status.updated_at.isoformat()
            if status and status.updated_at
            else None,
            # Core asset details (mirrors client.asset_info)
            "inverter": inverter or None,
            "battery": battery or None,
            "fuse_size": asset_info.get("fuseSize"),
            "is_installed": asset_info.get("isInstalled"),
            # Convenience flattened fields derived from inverter/battery
            "inverter_name": inverter.get("name"),
            "inverter_manufacturer": inverter.get("manufacturerName"),
            "inverter_battery_stacks_supported": inverter.get(
                "numberOfBatteryStacksSupported"
            ),
            "power_capacity": inverter.get("powerCapacity"),
            "battery_name": battery.get("name"),
            "battery_manufacturer": battery.get("manufacturerName"),
            "battery_max_modules": battery.get("maxNumberOfBatteryModules"),
            "battery_power_capacity": battery.get("powerCapacity"),
            "energy_capacity": battery.get("energyCapacity"),
        }

    def _is_auth_error(self, err: Exception) -> bool:
        try:
            if self._auth_exception_types and isinstance(
                err, self._auth_exception_types
            ):
                return True
        except Exception:  # pragma: no cover - fallback if isinstance fails
            pass

        # Detect HTTP-style auth failures (401/403) when a status is present
        status = None
        for attr in ("status", "status_code", "code"):
            value = getattr(err, attr, None)
            if isinstance(value, int):
                status = value
                break
        if status is None:
            try:
                from aiohttp import ClientResponseError  # type: ignore

                if isinstance(err, ClientResponseError):
                    status = err.status
            except Exception:  # pragma: no cover - aiohttp may not be available
                pass
        if status is not None:
            if status in (401, 403):
                return True
            if status >= 500:
                return False  # server errors are not auth failures

        text = str(err).lower()
        if any(
            code in text
            for code in ("401", "403", "unauthorized", "forbidden", "token", "expired")
        ):
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
        except Exception:  # pragma: no cover - fallback if module import fails
            pass
        return tuple(types)

    def _server_issue_id(self) -> str:
        return f"server_update_failures_{self._entry_id}"

    def _maybe_raise_server_issue(self, err: Exception) -> None:
        # Only raise a repairs issue for non-auth failures after threshold
        if self._consecutive_failures < self._repair_threshold:
            return
        ir_async_create_issue(
            hass=self.hass,
            domain=DOMAIN,
            issue_id=self._server_issue_id(),
            is_fixable=False,
            is_persistent=True,
            severity=IssueSeverity.ERROR,
            translation_key="server_update_failures",
            translation_placeholders={
                "count": str(self._consecutive_failures),
                "last_error": str(err),
            },
        )

    def _clear_server_issue(self) -> None:
        ir_async_delete_issue(
            hass=self.hass, domain=DOMAIN, issue_id=self._server_issue_id()
        )

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

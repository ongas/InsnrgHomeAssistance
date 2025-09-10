"""The InsnrgPool integration."""
import asyncio
from datetime import timedelta
import logging
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .call_api import InsnrgPool
from .exceptions import InsnrgPoolError
from .const import ATTRIBUTION, DOMAIN

PLATFORMS = [
    Platform.SELECT,
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Insnrg Pool from a config entry."""
    coordinator = InsnrgPoolDataUpdateCoordinator(hass, entry)

    # Perform initial login and data fetch.
    # This will raise ConfigEntryAuthFailed if credentials are invalid.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class InsnrgPoolEntity(CoordinatorEntity):
    """Implements a common class for Insnrg Pool entities."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, description: EntityDescription) -> None:
        """Initialize insnrg pool entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"InsnrgPool {description.name}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}"


class InsnrgPoolDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold Insnrg Pool data."""

    def __init__(self, hass, entry: ConfigEntry):
        """Initialize."""
        self.insnrg_pool = InsnrgPool(
            aiohttp_client.async_get_clientsession(hass),
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )
        self.hass = hass
        self.entry = entry
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=5)
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with async_timeout.timeout(60):
                # First, ensure we are logged in.
                # test_insnrg_pool_credentials now just calls async_login
                if not self.insnrg_pool._id_token:
                    auth_ok = await self.insnrg_pool.test_insnrg_pool_credentials()
                    if not auth_ok:
                        # This will trigger a re-auth flow
                        raise ConfigEntryAuthFailed("Invalid credentials")
                
                # Then, fetch the data
                return await self.insnrg_pool.get_insnrg_pool_data()

        except InsnrgPoolError as error:
            _LOGGER.error("Insnrg Pool query did not complete")
            raise UpdateFailed(error) from error
        except Exception as error:
            _LOGGER.error("Unexpected error updating Insnrg Pool data")
            raise UpdateFailed(error) from error
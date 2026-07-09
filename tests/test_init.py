from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.insnrg import (
    DOMAIN,
    InsnrgPoolDataUpdateCoordinator,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.insnrg.exceptions import InsnrgPoolError


def _entry():
    entry = MagicMock()
    entry.entry_id = "entry-1"
    entry.data = {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "secret"}
    return entry


@pytest.mark.asyncio
async def test_async_setup_entry_success(hass):
    entry = _entry()
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with patch("custom_components.insnrg.aiohttp_client.async_get_clientsession", return_value=MagicMock()), patch(
        "custom_components.insnrg.InsnrgPool"
    ) as pool_cls, patch(
        "custom_components.insnrg.InsnrgPoolDataUpdateCoordinator"
    ) as coordinator_cls:
        pool = pool_cls.return_value
        pool.test_insnrg_pool_credentials = AsyncMock(return_value=True)

        coordinator = coordinator_cls.return_value
        coordinator.async_config_entry_first_refresh = AsyncMock()

        ok = await async_setup_entry(hass, entry)

    assert ok is True
    assert hass.data[DOMAIN][entry.entry_id] is coordinator
    hass.config_entries.async_forward_entry_setups.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_setup_entry_invalid_auth(hass):
    entry = _entry()
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with patch("custom_components.insnrg.aiohttp_client.async_get_clientsession", return_value=MagicMock()), patch(
        "custom_components.insnrg.InsnrgPool"
    ) as pool_cls:
        pool = pool_cls.return_value
        pool.test_insnrg_pool_credentials = AsyncMock(return_value=False)

        ok = await async_setup_entry(hass, entry)

    assert ok is False
    hass.config_entries.async_forward_entry_setups.assert_not_awaited()


@pytest.mark.asyncio
async def test_async_unload_entry_removes_data(hass):
    entry = _entry()
    hass.data[DOMAIN] = {entry.entry_id: MagicMock()}
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    ok = await async_unload_entry(hass, entry)

    assert ok is True
    assert entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_coordinator_update_data_error_raises_updatefailed(hass):
    entry = _entry()

    with patch("custom_components.insnrg.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        coordinator = InsnrgPoolDataUpdateCoordinator(hass, entry)

    coordinator.insnrg_pool.get_insnrg_pool_data = AsyncMock(
        side_effect=InsnrgPoolError(500, "Server error")
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

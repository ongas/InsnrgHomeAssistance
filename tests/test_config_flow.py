from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from custom_components.insnrg.config_flow import InsnrgPoolConfigFlow


@pytest.mark.asyncio
async def test_config_flow_shows_form_without_input():
    flow = InsnrgPoolConfigFlow()
    result = await flow.async_step_user()

    assert result["type"] == "form"
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_config_flow_creates_entry_on_valid_credentials():
    flow = InsnrgPoolConfigFlow()
    flow.hass = MagicMock()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

    with patch("custom_components.insnrg.config_flow.aiohttp_client.async_get_clientsession", return_value=MagicMock()), patch(
        "custom_components.insnrg.config_flow.InsnrgPool"
    ) as pool_cls:
        pool = pool_cls.return_value
        pool.test_insnrg_pool_credentials = AsyncMock(return_value=True)

        result = await flow.async_step_user(
            {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "secret"}
        )

    assert result == {"type": "create_entry"}
    flow.async_create_entry.assert_called_once()


@pytest.mark.asyncio
async def test_config_flow_returns_invalid_auth_error():
    flow = InsnrgPoolConfigFlow()
    flow.hass = MagicMock()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()

    with patch("custom_components.insnrg.config_flow.aiohttp_client.async_get_clientsession", return_value=MagicMock()), patch(
        "custom_components.insnrg.config_flow.InsnrgPool"
    ) as pool_cls:
        pool = pool_cls.return_value
        pool.test_insnrg_pool_credentials = AsyncMock(return_value=False)

        result = await flow.async_step_user(
            {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "secret"}
        )

    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_auth"

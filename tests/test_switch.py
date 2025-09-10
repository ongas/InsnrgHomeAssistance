from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import CONF_EMAIL
from homeassistant.core import HomeAssistant

from custom_components.insnrg.const import DOMAIN
from custom_components.insnrg.switch import InsnrgPoolSwitch, async_setup_entry


@pytest.fixture
def mock_coordinator():
    """Mock the DataUpdateCoordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "SPA": {"name": "Spa", "switchStatus": "OFF"},
        "VF_SETTING_SET_HEATER_MODE": {"name": "Heater", "switchStatus": "OFF"},
    }
    coordinator.insnrg_pool = AsyncMock()
    # Add the async_request_refresh mock to the coordinator
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Mock the ConfigEntry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {CONF_EMAIL: "test@example.com"}
    return entry


async def test_async_setup_entry(hass: HomeAssistant, mock_coordinator, mock_config_entry):
    """Test the switch setup entry."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    async_add_entities = MagicMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    assert async_add_entities.call_count == 1
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 2
    assert isinstance(entities[0], InsnrgPoolSwitch)
    assert entities[0].name == "InsnrgPool Heater Switch"
    assert isinstance(entities[1], InsnrgPoolSwitch)
    assert entities[1].name == "InsnrgPool Spa Switch"


async def test_switch_turn_on(hass: HomeAssistant, mock_coordinator):
    """Test turning the switch on with the refactored implementation."""
    description = SwitchEntityDescription(key="SPA", name="Spa Switch")
    # Note the new, simpler signature from the refactored code
    switch = InsnrgPoolSwitch(mock_coordinator, description, "SPA")
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()

    # Initial state is off
    assert not switch.is_on

    # Mock API call success
    mock_coordinator.insnrg_pool.turn_the_switch = AsyncMock(return_value=True)

    await switch.async_turn_on()

    # 1. Optimistic update happened
    assert switch.is_on
    # 2. API call was made
    mock_coordinator.insnrg_pool.turn_the_switch.assert_called_once_with("ON", "SPA")
    # 3. Coordinator refresh was requested
    mock_coordinator.async_request_refresh.assert_called_once()


async def test_switch_turn_off_api_fail(hass: HomeAssistant, mock_coordinator):
    """Test turning the switch off with an API failure on the refactored code."""
    # Set initial state to ON
    mock_coordinator.data["SPA"]["switchStatus"] = "ON"

    description = SwitchEntityDescription(key="SPA", name="Spa Switch")
    switch = InsnrgPoolSwitch(mock_coordinator, description, "SPA")
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()

    assert switch.is_on

    # Mock API call failure
    mock_coordinator.insnrg_pool.turn_the_switch = AsyncMock(return_value=False)

    await switch.async_turn_off()

    # The refactored code reverts the state immediately if the API call fails.
    # Assert that the final state is ON.
    assert switch.is_on

    # Check that the API call was made
    mock_coordinator.insnrg_pool.turn_the_switch.assert_called_once_with("OFF", "SPA")

    # Check that state was written multiple times (optimistic OFF, then revert to ON)
    assert switch.async_write_ha_state.call_count >= 2
    
    # Check that a refresh was still requested
    mock_coordinator.async_request_refresh.assert_called_once()

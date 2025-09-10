from unittest.mock import AsyncMock, MagicMock, patch

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
    # Use MagicMock instead of AsyncMock for non-awaited callbacks
    async_add_entities = MagicMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    assert async_add_entities.call_count == 1
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 2
    assert isinstance(entities[0], InsnrgPoolSwitch)
    # Fix: Assert the full, correct name
    assert entities[0].name == "InsnrgPool Heater Switch"
    assert isinstance(entities[1], InsnrgPoolSwitch)
    # Fix: Assert the full, correct name
    assert entities[1].name == "InsnrgPool Spa Switch"


@patch("custom_components.insnrg.switch.PollingMixin._async_poll_for_state_change", new_callable=AsyncMock)
@patch("custom_components.insnrg.switch.PollingMixin._async_animate_icon", new_callable=AsyncMock)
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_switch_turn_on(mock_sleep, mock_animate, mock_poll, hass: HomeAssistant, mock_coordinator):
    """Test turning the switch on."""
    description = SwitchEntityDescription(key="SPA", name="Spa Switch")
    switch = InsnrgPoolSwitch(mock_coordinator, "test@example.com", description, "SPA", hass)
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()

    # Initial state is off
    assert not switch.is_on

    # Mock API call success
    mock_coordinator.insnrg_pool.turn_the_switch = AsyncMock(return_value=True)
    # Mock polling success
    mock_poll.return_value = True

    await switch.async_turn_on()

    # 1. Optimistic update
    assert switch.is_on
    # 2. API call is made
    mock_coordinator.insnrg_pool.turn_the_switch.assert_called_once_with("ON", "SPA")
    # 3. Polling is initiated
    mock_poll.assert_called_once()
    # 4. Animation is started
    mock_animate.assert_called_once()


@patch("custom_components.insnrg.switch.PollingMixin._async_poll_for_state_change", new_callable=AsyncMock)
@patch("custom_components.insnrg.switch.PollingMixin._async_animate_icon", new_callable=AsyncMock)
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_switch_turn_off_api_fail(mock_sleep, mock_animate, mock_poll, hass: HomeAssistant, mock_coordinator):
    """Test turning the switch off with an API failure and state reversion."""
    # Set initial state to ON
    mock_coordinator.data["SPA"]["switchStatus"] = "ON"

    description = SwitchEntityDescription(key="SPA", name="Spa Switch")
    switch = InsnrgPoolSwitch(mock_coordinator, "test@example.com", description, "SPA", hass)
    switch.hass = hass
    switch.async_write_ha_state = MagicMock()

    assert switch.is_on

    # Mock API call failure
    mock_coordinator.insnrg_pool.turn_the_switch = AsyncMock(return_value=False)

    await switch.async_turn_off()

    # The switch should be ON at the end, because the API call failed
    # and the state should have been reverted by the `else` block.
    assert switch.is_on

    # Check that the API call was made
    mock_coordinator.insnrg_pool.turn_the_switch.assert_called_once_with("OFF", "SPA")

    # Check that polling was NOT initiated on API failure
    mock_poll.assert_not_called()

    # Check that state was written multiple times (optimistic OFF, then revert to ON)
    assert switch.async_write_ha_state.call_count >= 2
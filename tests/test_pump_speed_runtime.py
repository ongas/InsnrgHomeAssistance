from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.select import SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.insnrg.select import InsnrgPoolSelect
from custom_components.insnrg.sensor import (
    InsnrgPumpSpeedStatusSensor,
    PUMP_SPEED_STATUS_DESCRIPTION,
)


@pytest.mark.asyncio
async def test_real_state_machine_reports_unavailable_select_and_status(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    hass.loop = __import__("asyncio").get_running_loop()
    update_data = {}
    fail_update = False

    async def fetch_data():
        if fail_update:
            raise UpdateFailed("offline")
        return update_data

    coordinator = DataUpdateCoordinator(
        hass, MagicMock(), name="insnrg", update_method=fetch_data
    )
    await coordinator.async_refresh()
    entry = MagicMock(data={"email": "user", "password": "password"})
    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        select = InsnrgPoolSelect(
            coordinator, hass, entry,
            SelectEntityDescription(key="PUMP_SPEED", name="Pump Speed"),
        )
    status = InsnrgPumpSpeedStatusSensor(coordinator, PUMP_SPEED_STATUS_DESCRIPTION)
    select.hass = status.hass = hass
    select.entity_id = "select.insnrg_pump_speed"
    status.entity_id = "sensor.insnrg_pump_speed_status"
    coordinator.async_add_listener(select._handle_coordinator_update)
    coordinator.async_add_listener(status._handle_coordinator_update)

    select.async_write_ha_state()
    status.async_write_ha_state()
    assert hass.states.get(select.entity_id).state == "unavailable"
    assert hass.states.get(status.entity_id).state == "Insnrg is not currently reporting pump-speed data"

    update_data["PUMP_SPEED"] = {
        "name": "Pump Speed", "deviceId": "PUMP_SPEED",
        "modeList": ["Default", "1"], "modeValue": "1",
    }
    await coordinator.async_refresh()
    assert hass.states.get(select.entity_id).state == "1"
    assert hass.states.get(status.entity_id).state == "Pump speed data available"

    fail_update = True
    await coordinator.async_refresh()
    assert hass.states.get(status.entity_id).state == "Unable to refresh Insnrg data"
    await hass.async_stop()

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from custom_components.insnrg.const import DOMAIN, TEMP_SENSOR_KEY


def _entry():
    entry = MagicMock()
    entry.entry_id = "entry-1"
    entry.data = {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "secret"}
    return entry


@pytest.mark.asyncio
async def test_select_setup_creates_expected_entities(hass):
    from custom_components.insnrg import select

    entry = _entry()
    coordinator = MagicMock()
    coordinator.data = {
        "SPA": {"name": "Spa", "deviceId": "SPA", "switchStatus": "OFF", "toggleStatus": ""},
        "VF_CONTACT_1": {
            "name": "VF Contact - Heat Pump",
            "deviceId": "VF_CONTACT_1",
            "switchStatus": "ON",
            "toggleStatus": "OFF",
        },
    }
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    add_entities = MagicMock()

    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        await select.async_setup_entry(hass, entry, add_entities)

    entities = add_entities.call_args[0][0]
    assert len(entities) == 2


@pytest.mark.asyncio
async def test_climate_setup_creates_entities_for_spa_and_pool(hass):
    from custom_components.insnrg import climate

    entry = _entry()
    coordinator = MagicMock()
    coordinator.data = {
        "SPA_CONTROL": {
            "name": "Spa thermostat",
            "deviceId": "SPA_CONTROL",
            "thermostatStatus": {"value": 30, "valueMin": 10, "valueMax": 40},
            "temperatureSensorStatus": {"value": 27},
        },
        "POOL_CONTROL": {
            "name": "Water Thermostat",
            "deviceId": "POOL_CONTROL",
            "thermostatStatus": {"value": 28, "valueMin": 10, "valueMax": 40},
            "temperatureSensorStatus": {"value": 26},
        },
    }
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    add_entities = MagicMock()

    with patch("custom_components.insnrg.climate.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        await climate.async_setup_entry(hass, entry, add_entities)

    entities = add_entities.call_args[0][0]
    assert len(entities) == 2


@pytest.mark.asyncio
async def test_number_setup_creates_entities_for_ph_and_orp(hass):
    from custom_components.insnrg import number

    entry = _entry()
    coordinator = MagicMock()
    coordinator.data = {
        "PH": {"name": "pH", "deviceId": "PH", "thermostatStatus": {"setPoint": 7.4, "valueMin": 7.0, "valueMax": 7.8}},
        "ORP": {
            "name": "ORP",
            "deviceId": "ORP",
            "thermostatStatus": {"setPoint": 650, "valueMin": 550, "valueMax": 750},
        },
    }
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    add_entities = MagicMock()

    with patch("custom_components.insnrg.number.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        await number.async_setup_entry(hass, entry, add_entities)

    entities = add_entities.call_args[0][0]
    assert len(entities) == 2


@pytest.mark.asyncio
async def test_sensor_setup_creates_pool_temp_and_ph_sensor(hass):
    from custom_components.insnrg import sensor

    entry = _entry()
    coordinator = MagicMock()
    coordinator.data = {
        TEMP_SENSOR_KEY: {"name": "Pool Temp", "temperatureSensorStatus": {"value": 25}},
        "PH": {"name": "pH", "temperatureSensorStatus": {"value": 7.3}},
    }
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    add_entities = MagicMock()

    await sensor.async_setup_entry(hass, entry, add_entities)

    entities = add_entities.call_args[0][0]
    assert len(entities) == 2


@pytest.mark.asyncio
async def test_switch_setup_creates_entities_for_switch_and_toggle_devices(hass):
    from custom_components.insnrg import switch

    entry = _entry()
    coordinator = MagicMock()
    coordinator.data = {
        "MODE": {"name": "Filter Pump", "switchStatus": "OFF", "toggleStatus": "OFF"},
        "VF_CONTACT_1": {"name": "VF Contact", "switchStatus": "", "toggleStatus": "ON"},
    }
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    add_entities = MagicMock()

    await switch.async_setup_entry(hass, entry, add_entities)

    entities = add_entities.call_args[0][0]
    assert len(entities) == 2

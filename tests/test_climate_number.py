from unittest.mock import MagicMock, patch

from homeassistant.components.climate import ClimateEntityDescription
from homeassistant.components.number import NumberEntityDescription
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from custom_components.insnrg.climate import InsnrgPoolClimate
from custom_components.insnrg.number import InsnrgPoolNumber


def _entry():
    entry = MagicMock()
    entry.data = {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"}
    return entry


def test_climate_target_temperature_prefers_gg_pool_set_temperature(hass):
    coordinator = MagicMock()
    coordinator.data = {
        "POOL_CONTROL": {
            "name": "Water Thermostat",
            "deviceId": "POOL_CONTROL",
            "thermostatStatus": {
                "ggPoolSetTemperature": 30,
                "value": 28,
                "valueMax": 40,
                "valueMin": 10,
            },
            "temperatureSensorStatus": {"value": 26.5},
        }
    }
    description = ClimateEntityDescription(key="POOL_CONTROL", name="Water Thermostat")

    with patch("custom_components.insnrg.climate.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        entity = InsnrgPoolClimate(coordinator, hass, _entry(), description)

    assert entity.target_temperature == 30
    assert entity.current_temperature == 26.5
    assert entity.max_temp == 40
    assert entity.min_temp == 10


def test_number_entity_reports_slider_bounds_and_steps(hass):
    coordinator = MagicMock()
    coordinator.data = {
        "PH": {
            "name": "pH Sensor",
            "deviceId": "PH",
            "thermostatStatus": {
                "setPoint": 7.4,
                "valueMax": 7.8,
                "valueMin": 7.0,
            },
        },
        "ORP": {
            "name": "ORP Sensor",
            "deviceId": "ORP",
            "thermostatStatus": {
                "setPoint": 650,
                "valueMax": 750,
                "valueMin": 550,
            },
        },
    }

    with patch("custom_components.insnrg.number.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        ph_entity = InsnrgPoolNumber(
            coordinator,
            hass,
            _entry(),
            NumberEntityDescription(key="PH", name="Set PH Point"),
        )
        orp_entity = InsnrgPoolNumber(
            coordinator,
            hass,
            _entry(),
            NumberEntityDescription(key="ORP", name="Set ORP Point"),
        )

    assert ph_entity.mode == "slider"
    assert ph_entity.native_value == 7.4
    assert ph_entity.native_step == 0.1
    assert ph_entity.native_min_value == 7.0
    assert ph_entity.native_max_value == 7.8

    assert orp_entity.native_value == 650
    assert orp_entity.native_step == 10

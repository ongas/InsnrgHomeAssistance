from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.select import SelectEntityDescription
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from custom_components.insnrg.select import InsnrgPoolSelect


def _entry():
    entry = MagicMock()
    entry.data = {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"}
    return entry


@pytest.mark.parametrize(
    ("device_id", "switch_status", "toggle_status", "expected"),
    [
        ("VF_CONTACT_1", "ON", "OFF", "ON"),
        ("VF_CONTACT_1", "OFF", "ON", "OFF"),
        ("VF_CONTACT_1", "", "ON", "TIMER"),
        ("VF_CONTACT_1", "", "OFF", "OFF"),
        ("MODE", "ON", "ON", "TIMER"),
    ],
)
def test_select_current_option_prefers_switch_status(hass, device_id, switch_status, toggle_status, expected):
    coordinator = MagicMock()
    coordinator.data = {
        device_id: {
            "name": "VF Contact - Heat Pump",
            "deviceId": device_id,
            "switchStatus": switch_status,
            "toggleStatus": toggle_status,
        }
    }
    description = SelectEntityDescription(key=device_id, name="VF Contact - Heat Pump")

    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        entity = InsnrgPoolSelect(coordinator, hass, _entry(), description)

    assert entity.current_option == expected

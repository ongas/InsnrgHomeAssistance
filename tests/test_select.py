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
    ("switch_status", "toggle_status", "expected"),
    [
        ("ON", "OFF", "ON"),
        ("OFF", "ON", "OFF"),
        ("", "ON", "TIMER"),
        ("", "OFF", "OFF"),
    ],
)
def test_select_current_option_prefers_switch_status(hass, switch_status, toggle_status, expected):
    coordinator = MagicMock()
    coordinator.data = {
        "VF_CONTACT_1": {
            "name": "VF Contact - Heat Pump",
            "deviceId": "VF_CONTACT_1",
            "switchStatus": switch_status,
            "toggleStatus": toggle_status,
        }
    }
    description = SelectEntityDescription(key="VF_CONTACT_1", name="VF Contact - Heat Pump")

    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        entity = InsnrgPoolSelect(coordinator, hass, _entry(), description)

    assert entity.current_option == expected

from unittest.mock import AsyncMock, MagicMock

import pytest
import json
from pathlib import Path

from custom_components.insnrg.call_api import CMD_URL, LOGIN_URL, InsnrgPool


def _response(status, payload):
    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=payload)
    return resp


@pytest.mark.asyncio
async def test_get_insnrg_pool_data_maps_power_and_toggle_statuses():
    login_payload = {
        "auth": {"idToken": "token123"},
        "user": {"userId": "user-1"},
    }
    getall_payload = [
        {
            "name": "VF Contact - Heat Pump",
            "deviceId": "VF_CONTACT_1",
            "type": ["SWITCH"],
            "properties": [
                {"namespace": "Alexa.PowerController", "value": "ON"},
                {"namespace": "Alexa.ToggleController", "value": "OFF"},
            ],
        },
        {
            "name": "Spa Light",
            "deviceId": "OUTLET_HUB_4",
            "type": ["LIGHT"],
            "options": ["BLUE", "WHITE"],
            "properties": [
                {"namespace": "Alexa.PowerController", "value": "OFF"},
                {"namespace": "Alexa.ModeController", "value": "BLUE"},
            ],
        },
    ]

    session = MagicMock()
    session.post = AsyncMock(
        side_effect=[
            _response(200, login_payload),
            _response(200, getall_payload),
        ]
    )

    api = InsnrgPool(session, "user@example.com", "secret")
    data = await api.get_insnrg_pool_data()

    assert data["VF_CONTACT_1"]["switchStatus"] == "ON"
    assert data["VF_CONTACT_1"]["toggleStatus"] == "OFF"
    assert data["LIGHT_MODE"]["modeList"] == ["BLUE", "WHITE"]
    assert data["OUTLET_HUB_4"]["modeList"] == ["BLUE", "WHITE"]

    assert session.post.await_count == 2
    session.post.assert_any_await(LOGIN_URL, json={"userName": "user@example.com", "password": "secret"})
    session.post.assert_any_await(
        CMD_URL,
        headers={"Authorization": "token123"},
        json={"cmd": "getall", "userId": "user-1"},
    )


@pytest.mark.asyncio
async def test_get_insnrg_pool_data_defaults_when_namespaces_missing():
    login_payload = {
        "auth": {"idToken": "token123"},
        "user": {"userId": "user-1"},
    }
    getall_payload = [
        {
            "name": "Timer",
            "deviceId": "TIMER_1_STATUS",
            "type": ["SWITCH"],
            "properties": [],
        }
    ]

    session = MagicMock()
    session.post = AsyncMock(
        side_effect=[
            _response(200, login_payload),
            _response(200, getall_payload),
        ]
    )

    api = InsnrgPool(session, "user@example.com", "secret")
    data = await api.get_insnrg_pool_data()

    assert data["TIMER_1_STATUS"]["switchStatus"] == ""
    assert data["TIMER_1_STATUS"]["toggleStatus"] == ""
    assert data["TIMER_1_STATUS"]["modeValue"] == ""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "method_args"),
    [
        ("turn_the_switch", ("ON", "VF_CONTACT_1")),
        ("set_thermostat_temp", (28, "POOL_CONTROL")),
        ("set_chemistry", (7.4, "PH")),
    ],
)
async def test_write_methods_return_false_on_non_200(method_name, method_args):
    login_payload = {
        "auth": {"idToken": "token123"},
        "user": {"userId": "user-1"},
    }

    session = MagicMock()
    session.post = AsyncMock(
        side_effect=[
            _response(200, login_payload),
            _response(500, {"error": "boom"}),
        ]
    )

    api = InsnrgPool(session, "user@example.com", "secret")
    method = getattr(api, method_name)

    ok = await method(*method_args)

    assert ok is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "method_args"),
    [
        ("turn_the_switch", ("ON", "VF_CONTACT_1")),
        ("set_thermostat_temp", (28, "POOL_CONTROL")),
        ("set_chemistry", (7.4, "PH")),
    ],
)
async def test_write_methods_return_false_on_exception(method_name, method_args):
    session = MagicMock()
    session.post = AsyncMock(side_effect=RuntimeError("network down"))

    api = InsnrgPool(session, "user@example.com", "secret")
    method = getattr(api, method_name)

    ok = await method(*method_args)

    assert ok is False


@pytest.mark.asyncio
async def test_get_insnrg_pool_data_with_realistic_fixture_payload():
    fixture_path = Path(__file__).parent / "fixtures" / "getall_sample.json"
    getall_payload = json.loads(fixture_path.read_text())
    login_payload = {
        "auth": {"idToken": "token123"},
        "user": {"userId": "user-1"},
    }

    session = MagicMock()
    session.post = AsyncMock(
        side_effect=[
            _response(200, login_payload),
            _response(200, getall_payload),
        ]
    )

    api = InsnrgPool(session, "user@example.com", "secret")
    data = await api.get_insnrg_pool_data()

    assert data["VF_CONTACT_1"]["switchStatus"] == "ON"
    assert data["VF_CONTACT_1"]["toggleStatus"] == "OFF"
    assert data["POOL_CONTROL"]["temperatureSensorStatus"]["value"] == 8.5

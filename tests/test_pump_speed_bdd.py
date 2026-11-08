import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from homeassistant.components.select import SelectEntityDescription
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from custom_components.insnrg.select import InsnrgPoolSelect

scenarios("features/pump_speed.feature")


@pytest.fixture
def pump_context():
    return {}


@given("select platform starts before pump speed is reported")
def select_platform_without_pump(pump_context):
    from custom_components.insnrg.select import async_setup_entry

    coordinator = MagicMock()
    coordinator.data = {}
    listeners = []
    coordinator.async_add_listener = MagicMock(side_effect=lambda callback: (listeners.append(callback) or (lambda: listeners.remove(callback))))
    entry = MagicMock(data={CONF_EMAIL: "user", CONF_PASSWORD: "password"})
    unload_callbacks = []
    entry.async_on_unload = MagicMock(side_effect=unload_callbacks.append)
    added = []
    hass = MagicMock()
    from custom_components.insnrg.const import DOMAIN
    hass.data = {DOMAIN: {entry.entry_id: coordinator}}
    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        asyncio.run(async_setup_entry(hass, entry, lambda entities, update: added.extend(entities)))
    from custom_components.insnrg.sensor import async_setup_entry as setup_sensors
    sensors = []
    asyncio.run(setup_sensors(hass, entry, lambda entities, update: sensors.extend(entities)))
    pump_context.update(coordinator=coordinator, entry=entry, listeners=listeners, unload_callbacks=unload_callbacks, added=added, sensors=sensors)


@when("the pump speed data remains absent")
def absent_pump(pump_context):
    pass


@then("one unavailable pump speed select and readable status report absent data")
def absent_pump_entity(pump_context):
    entities = [entity for entity in pump_context["added"] if entity.entity_description.key == "PUMP_SPEED"]
    assert len(entities) == 1
    entity = entities[0]
    assert entity.available is False
    assert entity.current_option is None
    assert entity.options == []
    assert len(pump_context["sensors"]) == 1
    assert pump_context["sensors"][0].native_value == "Insnrg is not currently reporting pump-speed data"


@when(parsers.parse('discovery reports pump speed presets "{presets}" and current value "{current}"'))
def report_late_pump(pump_context, presets, current):
    pump_context["coordinator"].data["PUMP_SPEED"] = {
        "name": "Pump Speed", "deviceId": "PUMP_SPEED", "modeList": presets.split(","), "modeValue": current,
    }
    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        for listener in list(pump_context["listeners"]):
            listener()


@when(parsers.parse('discovery reports pump speed presets "{presets}" and current value "{current}" repeatedly'))
def report_late_pump_repeated(pump_context, presets, current):
    report_late_pump(pump_context, presets, current)
    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        for listener in list(pump_context["listeners"]):
            listener()


@then("exactly one pump speed select is added with reported options and state")
def one_late_pump_select(pump_context):
    entities = [entity for entity in pump_context["added"] if entity.entity_description.key == "PUMP_SPEED"]
    assert len(entities) == 1
    assert entities[0].available is True
    assert entities[0].options == ["Default", "1", "2"]
    assert entities[0].current_option == "1"


@then("pump speed status reports available data")
def status_available(pump_context):
    assert len(pump_context["sensors"]) == 1
    assert pump_context["sensors"][0].native_value == "Pump speed data available"


@when("the coordinator refresh fails")
def fail_coordinator_refresh(pump_context):
    pump_context["coordinator"].last_update_success = False


@then("pump speed status reports an update failure")
def status_refresh_failed(pump_context):
    assert pump_context["sensors"][0].native_value == "Unable to refresh Insnrg data"


@when("the select platform unloads before pump speed discovery")
def unload_select_platform(pump_context):
    for callback in pump_context["unload_callbacks"]:
        callback()
    pump_context["coordinator"].data["PUMP_SPEED"] = {
        "name": "Pump Speed", "deviceId": "PUMP_SPEED", "modeList": ["Default", "1"], "modeValue": "1",
    }
    for listener in list(pump_context["listeners"]):
        listener()


@then("later pump discovery adds no pump speed select")
def no_select_after_unload(pump_context):
    assert len([entity for entity in pump_context["added"] if entity.entity_description.key == "PUMP_SPEED"]) == 1


@then("the stable pump speed select was created without a late discovery listener")
def stable_entity_no_listener(pump_context):
    assert len([entity for entity in pump_context["added"] if entity.entity_description.key == "PUMP_SPEED"]) == 1
    assert pump_context["listeners"] == []


@given(parsers.parse('a discovered pump speed device with reported presets "{presets}" and current value "{current}"'))
def discovered_pump(pump_context, presets, current):
    mode_list = presets.split(",")
    coordinator = MagicMock()
    coordinator.data = {"PUMP_SPEED": {"name": "Pump Speed", "deviceId": "PUMP_SPEED", "modeList": mode_list, "modeValue": current}}
    entry = MagicMock(data={CONF_EMAIL: "user", CONF_PASSWORD: "password"})
    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        entity = InsnrgPoolSelect(coordinator, MagicMock(), entry, SelectEntityDescription(key="PUMP_SPEED", name="Pump Speed"))
    pump_context.update(coordinator=coordinator, entity=entity, mode_list=mode_list, current=current)


@given(parsers.parse('pump speed data is keyed as pump speed but reports device identifier "{device_id}"'))
def mismatched_pump_device(pump_context, device_id):
    coordinator = MagicMock()
    coordinator.data = {"PUMP_SPEED": {
        "name": "Pump Speed", "deviceId": device_id,
        "switchStatus": "OFF", "toggleStatus": "OFF",
    }}
    entry = MagicMock(data={CONF_EMAIL: "user", CONF_PASSWORD: "password"})
    with patch("custom_components.insnrg.select.aiohttp_client.async_get_clientsession", return_value=MagicMock()):
        entity = InsnrgPoolSelect(coordinator, MagicMock(), entry, SelectEntityDescription(key="PUMP_SPEED", name="Pump Speed"))
    entity.insnrg_pool.set_pump_value = AsyncMock()
    entity.insnrg_pool.turn_the_switch = AsyncMock(return_value=False)
    entity.async_write_ha_state = MagicMock()
    pump_context.update(entity=entity, coordinator=coordinator)


@when(parsers.parse('I select pump speed "{option}"'))
def choose_mismatched_pump(pump_context, option):
    asyncio.run(pump_context["entity"].async_select_option(option))


@then("the pump speed selector remains unavailable without guessed options or state")
def mismatched_pump_has_no_state(pump_context):
    entity = pump_context["entity"]
    assert entity.available is False
    assert entity.options == []
    assert entity.current_option is None


@then("no pump or switch command is sent")
def mismatched_no_commands(pump_context):
    entity = pump_context["entity"]
    entity.insnrg_pool.set_pump_value.assert_not_awaited()
    entity.insnrg_pool.turn_the_switch.assert_not_awaited()


@when("the pump speed select is initialized")
def initialized():
    pass


@then("its options are the reported presets")
def reported_options(pump_context):
    assert pump_context["entity"].options == pump_context["mode_list"]


@then(parsers.parse('its current option is "{expected}"'))
def current_option(pump_context, expected):
    assert pump_context["entity"].current_option == expected


@when(parsers.parse('discovery reports pump speed "{option}"'))
def discovery_updates(pump_context, option):
    pump_context["coordinator"].data["PUMP_SPEED"]["modeValue"] = option


@when(parsers.parse('I select pump speed "{option}" and polling confirms it'))
def choose_confirmed(pump_context, option):
    entity = pump_context["entity"]
    entity.async_write_ha_state = MagicMock()
    entity._attr_icon = None
    pump_context["coordinator"].async_request_refresh = AsyncMock()
    clock = [0]
    entity.hass.loop.time = lambda: clock[0]
    sleeps = [0]

    async def advance_until_discovery(seconds):
        sleeps[0] += 1
        if sleeps[0] == 2:
            pump_context["coordinator"].data["PUMP_SPEED"]["modeValue"] = option
            clock[0] += 1

    entity.insnrg_pool.set_pump_value = AsyncMock(return_value=True)
    with patch("custom_components.insnrg.select.asyncio.sleep", new=AsyncMock()) as sleep, \
         patch.object(entity, "_async_animate_icon", new=AsyncMock()):
        sleep.side_effect = advance_until_discovery
        asyncio.run(entity.async_select_option(option))
    pump_context.update(option=option, set_pump=entity.insnrg_pool.set_pump_value)


@then("the pump value command is sent for the discovered device")
def exact_command(pump_context):
    pump_context["set_pump"].assert_awaited_once_with("2", "PUMP_SPEED")
    pool = pump_context["entity"].insnrg_pool
    pool._session = SimpleNamespace(post=AsyncMock(side_effect=[
        SimpleNamespace(status=200, json=AsyncMock(return_value={
            "user": {"userId": "user-1"}, "auth": {"idToken": "token"}
        })),
        SimpleNamespace(status=200),
    ]))
    assert asyncio.run(type(pool).set_pump_value(pool, "2", "PUMP_SPEED")) is True
    command_call = pool._session.post.await_args_list[1]
    assert command_call.args[0].endswith("/api/cmd")
    assert command_call.kwargs["json"] == {
        "cmd": "setPumpValue", "pumpValue": "2", "deviceId": "PUMP_SPEED", "userId": "user-1"
    }


@then(parsers.parse('the confirmed current option is "{expected}"'))
def confirmed_option(pump_context, expected):
    pump_context["coordinator"].async_request_refresh.assert_awaited()
    assert pump_context["entity"].current_option == expected


@when(parsers.parse('I select pump speed "{option}" and the command fails'))
def choose_failed(pump_context, option):
    entity = pump_context["entity"]
    entity.async_write_ha_state = MagicMock()
    entity.insnrg_pool.set_pump_value = AsyncMock(return_value=False)
    with patch("custom_components.insnrg.select.asyncio.sleep", new=AsyncMock()), \
         patch.object(entity, "_async_animate_icon", new=AsyncMock()):
        asyncio.run(entity.async_select_option(option))
    pump_context["set_pump"] = entity.insnrg_pool.set_pump_value


@then(parsers.parse('the current option remains "{expected}"'))
def failed_state(pump_context, expected):
    pump_context["set_pump"].assert_awaited_once_with("2", "PUMP_SPEED")
    assert pump_context["entity"].current_option == expected


@when(parsers.parse('I select pump speed "{option}" and discovery does not confirm it'))
def choose_unconfirmed(pump_context, option):
    entity = pump_context["entity"]
    entity.async_write_ha_state = MagicMock()
    entity._attr_icon = None
    pump_context["coordinator"].async_request_refresh = AsyncMock()
    clock = [0]
    entity.hass.loop.time = lambda: clock[0]
    sleeps = [0]

    async def advance_to_timeout(seconds):
        sleeps[0] += 1
        if sleeps[0] == 2:
            clock[0] += 301

    entity.insnrg_pool.set_pump_value = AsyncMock(return_value=True)
    with patch("custom_components.insnrg.select.asyncio.sleep", new=AsyncMock()) as sleep, \
         patch.object(entity, "_async_animate_icon", new=AsyncMock()):
        sleep.side_effect = advance_to_timeout
        asyncio.run(entity.async_select_option(option))
    pump_context["set_pump"] = entity.insnrg_pool.set_pump_value


@when("the pump speed device disappears")
def device_disappears(pump_context):
    pump_context["coordinator"].data.pop("PUMP_SPEED")
    pump_context["entity"].async_write_ha_state = MagicMock()


@then("its current option is unavailable")
def unavailable_current_option(pump_context):
    assert pump_context["entity"].current_option is None
    assert pump_context["entity"].available is False


@then("no pump speed command is sent")
def no_command_on_missing_device(pump_context):
    entity = pump_context["entity"]
    entity.insnrg_pool.set_pump_value = AsyncMock()
    entity.insnrg_pool.turn_the_switch = AsyncMock()
    asyncio.run(entity.async_select_option("2"))
    entity.insnrg_pool.set_pump_value.assert_not_awaited()


@then("no switch command is sent")
def no_switch_command_on_missing_device(pump_context):
    pump_context["entity"].insnrg_pool.turn_the_switch.assert_not_awaited()

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.insnrg.polling_mixin import PollingMixin


class _DoneTask:
    def __init__(self):
        self.cancel_called = False

    def cancel(self):
        self.cancel_called = True

    def __await__(self):
        async def _done():
            return None

        return _done().__await__()


@pytest.mark.asyncio
async def test_polling_mixin_timeout_returns_false_and_cleans_up_icon():
    mixin = PollingMixin()
    entity = MagicMock()
    entity.entity_id = "switch.test"
    entity._attr_icon = None
    entity.async_write_ha_state = MagicMock()
    entity.coordinator.async_request_refresh = AsyncMock()

    loop = MagicMock()
    loop.time = MagicMock(side_effect=[0, 301])
    entity.hass.loop = loop

    animation_task = _DoneTask()

    success = await mixin._async_poll_for_state_change(
        entity,
        original_icon_from_entity="mdi:orig",
        target_value="ON",
        current_value_getter=lambda: "OFF",
        entity_type="switchStatus",
        animation_task=animation_task,
    )

    assert success is False
    assert animation_task.cancel_called is True
    assert entity._attr_icon == "mdi:orig"
    entity.coordinator.async_request_refresh.assert_not_awaited()

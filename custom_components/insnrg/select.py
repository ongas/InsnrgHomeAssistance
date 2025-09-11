from __future__ import annotations
import logging

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import InsnrgPoolEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
KEYS_TO_CHECK = [
    "SPA",
    "MODE",
    "TIMERS",
    "OUTLET_1",
    "OUTLET_2",
    "OUTLET_3",
    "OUTLET_HUB_3",
    "OUTLET_HUB_4",
    "OUTLET_HUB_5",
    "OUTLET_HUB_6",
    "VALVE_1",
    "VALVE_2",
    "VALVE_3",
    "VALVE_HUB_1",
    "VALVE_HUB_2",
    "VALVE_HUB_3",
    "VALVE_HUB_4",
    "LIGHT_MODE",
    "TIMER_1_STATUS",
    "TIMER_2_STATUS",
    "TIMER_3_STATUS",
    "TIMER_4_STATUS",
    "TIMER_1_CHL",
    "TIMER_2_CHL",
    "TIMER_3_CHL",
    "TIMER_4_CHL",
    "VF_CONTACT_1",
    "VF_CONTACT_HUB_1",
    "VF_CONTACT_HUB_2",
    "VF_CONTACT_HUB_3"
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer select setup to the shared select module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    select_descriptions = []
    for key in KEYS_TO_CHECK:
        if key in coordinator.data:
            select_descriptions.append(
                SelectEntityDescription(
                    key=key,
                    name=coordinator.data[key]["name"],
                )
            )
    entities = [
        InsnrgPoolSelect(coordinator, description)
        for description in select_descriptions
    ]
    async_add_entities(entities)


class InsnrgPoolSelect(InsnrgPoolEntity, SelectEntity):
    """Select representing Insnrg Pool data."""

    def __init__(self, coordinator, description):
        """Initialize Insnrg Pool select."""
        super().__init__(coordinator, description)
        self._update_state_from_coordinator()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state_from_coordinator()
        super()._handle_coordinator_update()

    def _update_state_from_coordinator(self):
        """Helper to get the current option from coordinator data."""
        device_data = self.coordinator.data.get(self.entity_description.key, {})
        if device_data.get("deviceId") == "LIGHT_MODE":
            self._attr_current_option = device_data.get("modeValue")
        elif device_data.get('toggleStatus') == "ON":
            self._attr_current_option = "TIMER"
        elif device_data.get('switchStatus') == "ON":
            self._attr_current_option = "ON"
        else:
            self._attr_current_option = "OFF"

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        device_data = self.coordinator.data.get(self.entity_description.key, {})
        device_id = device_data.get("deviceId")
        
        timerDevices = [
            "TIMER_1_STATUS", "TIMER_2_STATUS", "TIMER_3_STATUS", "TIMER_4_STATUS",
            "TIMER_1_CHL", "TIMER_2_CHL", "TIMER_3_CHL", "TIMER_4_CHL"
        ]
        
        if device_id == "LIGHT_MODE":
            return device_data.get("modeList", [])
        elif device_id == "SPA" or device_id == "TIMERS" or device_id in timerDevices:
            return ["ON", "OFF"]
        else:
            return ["ON", "OFF", "TIMER"]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Optimistic update
        self._attr_current_option = option
        self.async_write_ha_state()

        device_data = self.coordinator.data[self.entity_description.key]
        device_id = device_data["deviceId"]
        
        # Call the API. Errors are logged within the API module.
        if device_id == "LIGHT_MODE":
            support_cmd = device_data["supportCmd"]
            await self.coordinator.insnrg_pool.change_light_mode(option, support_cmd)
        else:
            await self.coordinator.insnrg_pool.turn_the_switch(option, device_id)

        # Request a refresh to get the latest state from the device.
        await self.coordinator.async_request_refresh()

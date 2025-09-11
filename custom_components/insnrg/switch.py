"""Switch platform for the Insnrg Pool integration."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import InsnrgPoolEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer switch setup to the shared switch module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    # These are the device IDs that are switches
    switch_devices = ["VF_SETTING_SET_HEATER_MODE", "SPA"]

    for device_id in switch_devices:
        if device_id in coordinator.data:
            device = coordinator.data[device_id]
            description = SwitchEntityDescription(
                key=device_id,
                name=f'{device["name"]} Switch',
            )
            entities.append(InsnrgPoolSwitch(coordinator, description, device_id))

    async_add_entities(entities)


class InsnrgPoolSwitch(InsnrgPoolEntity, SwitchEntity):
    """Switch representing Insnrg Pool data."""

    def __init__(self, coordinator, description, device_id):
        """Initialize Insnrg Pool switch."""
        super().__init__(coordinator, description)
        self._device_id = device_id
        self._update_state_from_coordinator()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state_from_coordinator()
        super()._handle_coordinator_update()

    def _update_state_from_coordinator(self) -> None:
        """Update the state of the switch from the coordinator data."""
        self._attr_is_on = (
            self.coordinator.data.get(self._device_id, {}).get("switchStatus") == "ON"
        )

    async def _turn_on_off(self, mode: str):
        """Shared function to turn the switch on or off."""
        # Optimistic update
        self._attr_is_on = mode == "ON"
        self.async_write_ha_state()

        # Call the API. Errors are logged within the API module.
        await self.coordinator.insnrg_pool.turn_the_switch(
            mode, self._device_id
        )
        
        # Request a refresh to get the latest state from the device.
        # The UI will show the optimistic state until this refresh completes.
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._turn_on_off("ON")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._turn_on_off("OFF")
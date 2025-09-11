from __future__ import annotations
import logging

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import InsnrgPoolEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
KEYS_TO_CHECK = ["PH", "ORP"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer number setup to the shared number module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    number_descriptions = []
    for key in KEYS_TO_CHECK:
        if key in coordinator.data:
            name = coordinator.data[key]['name']
            if coordinator.data[key].get("thermostatStatus", {}).get("valueMax", 0) > 0:
                name = f"Set {key} Point"
            number_descriptions.append(NumberEntityDescription(
                key=key,
                name=name,
            ))
    entities = [
        InsnrgPoolNumber(coordinator, description)
        for description in number_descriptions
    ]
    async_add_entities(entities)


class InsnrgPoolNumber(InsnrgPoolEntity, NumberEntity):
    """Number entity representing Insnrg Pool data."""
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, description):
        """Initialize Insnrg Pool number."""
        super().__init__(coordinator, description)
        self._update_state_from_coordinator()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state_from_coordinator()
        super()._handle_coordinator_update()

    def _get_thermostat_status(self) -> dict:
        """Get the thermostat status dictionary from the coordinator data."""
        return self.coordinator.data.get(self.entity_description.key, {}).get(
            "thermostatStatus", {}
        )

    def _update_state_from_coordinator(self) -> None:
        """Update the state of the number entity from coordinator data."""
        thermostat_status = self._get_thermostat_status()
        self._attr_native_value = thermostat_status.get("setPoint")
        self._attr_native_max_value = thermostat_status.get("valueMax")
        self._attr_native_min_value = thermostat_status.get("valueMin")

    @property
    def native_step(self) -> float:
        """Return the step size."""
        if self.entity_description.key == "ORP":
            return 10
        else:
            return 0.1

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # Optimistic update
        self._attr_native_value = value
        self.async_write_ha_state()

        device_id = self.coordinator.data[self.entity_description.key]["deviceId"]
        
        # Call the API. Errors are logged within the API module.
        await self.coordinator.insnrg_pool.set_chemistry(value, device_id)

        # Request a refresh to get the latest state from the device.
        await self.coordinator.async_request_refresh()

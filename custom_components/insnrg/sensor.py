"""Sensor platform for the Insnrg Pool sensor."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import InsnrgPoolEntity
from .const import DOMAIN

KEYS_TO_CHECK = ["PH", "ORP"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer sensor setup to the shared sensor module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    sensor_descriptions = []
    for key in KEYS_TO_CHECK:
        if key in coordinator.data:
            sensor_descriptions.append(SensorEntityDescription(
                key=key,
                name=coordinator.data[key]['name'],
                icon="mdi:coolant-temperature",
            ))
    entities = [
        InsnrgPoolSensor(coordinator, description)
        for description in sensor_descriptions
    ]
    async_add_entities(entities)


class InsnrgPoolSensor(InsnrgPoolEntity, SensorEntity):
    """Sensor representing Insnrg Pool data."""

    def __init__(self, coordinator, description: SensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)
        self._update_state_from_coordinator()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state_from_coordinator()
        super()._handle_coordinator_update()

    def _update_state_from_coordinator(self) -> None:
        """Update the state of the sensor from coordinator data."""
        device_data = self.coordinator.data.get(self.entity_description.key, {})
        self._attr_native_value = device_data.get("temperatureSensorStatus", {}).get("value")
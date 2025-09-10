"""Sensor platform for the Insnrg Pool sensor."""
from __future__ import annotations
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
)
from homeassistant.core import HomeAssistant
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
    sersor_descriptions = []
    for key in KEYS_TO_CHECK:
        if key in coordinator.data:
            sersor_descriptions.append(SensorEntityDescription(
                key=key,
                name=coordinator.data[key]['name'],
                icon="mdi:coolant-temperature",
            ))
    entities = [
        InsnrgPoolSensor(coordinator, config_entry.data[CONF_EMAIL], description)
        for description in sersor_descriptions
    ]
    async_add_entities(entities, False)

class InsnrgPoolSensor(InsnrgPoolEntity, SensorEntity):
    """Sensor representing Insnrg Pool data."""
    @property
    def native_value(self):
        """State of the sensor."""
        return self.coordinator.data[self.entity_description.key]["temperatureSensorStatus"]["value"]

"""Sensor platform for the Insnrg Pool sensor."""
from __future__ import annotations
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import InsnrgPoolEntity
from .const import DOMAIN, TEMP_SENSOR_KEY
KEYS_TO_CHECK = ["PH", "ORP", TEMP_SENSOR_KEY]

TEMP_SENSOR_DESCRIPTION = SensorEntityDescription(
    key=TEMP_SENSOR_KEY,
    name="Pool Temperature",
    icon="mdi:pool-thermometer",
)

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
            if key == TEMP_SENSOR_KEY:
                sersor_descriptions.append(TEMP_SENSOR_DESCRIPTION)
            else:
                sersor_descriptions.append(SensorEntityDescription(
                    key=key,
                    name=coordinator.data[key]['name'],
                    icon="mdi:coolant-temperature",
                ))
    entities = [
        InsnrgPoolSensor(coordinator, config_entry.data[CONF_EMAIL], description)
        for description in sersor_descriptions if description.key != TEMP_SENSOR_KEY
    ]

    temp_entities = [
        InsnrgPoolTempSensor(coordinator, config_entry.data[CONF_EMAIL], description)
        for description in sersor_descriptions if description.key == TEMP_SENSOR_KEY
    ]

    async_add_entities(entities + temp_entities, False)

class InsnrgPoolSensor(InsnrgPoolEntity, SensorEntity):
    """Sensor representing Insnrg Pool data."""
    @property
    def native_value(self):
        """State of the sensor."""
        return self.coordinator.data[self.entity_description.key][
            "temperatureSensorStatus"].get("value")

class InsnrgPoolTempSensor(InsnrgPoolEntity, SensorEntity):
    """Sensor representing Insnrg Pool Temperature data."""

    @property
    def native_value(self):
        """State of the sensor."""
        return self.coordinator.data[self.entity_description.key]["temperatureSensorStatus"].get("value")

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

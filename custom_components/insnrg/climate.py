from __future__ import annotations
import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import InsnrgPoolEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
KEYS_TO_CHECK = ["SPA_CONTROL", "POOL_CONTROL"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer climate setup to the shared climate module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    climate_descriptions = []
    for key in KEYS_TO_CHECK:
        if key in coordinator.data:
            climate_descriptions.append(
                ClimateEntityDescription(
                    key=key,
                    name=coordinator.data[key]["name"],
                )
            )
    entities = [
        InsnrgPoolClimate(coordinator, description) for description in climate_descriptions
    ]
    async_add_entities(entities)


class InsnrgPoolClimate(InsnrgPoolEntity, ClimateEntity):
    """Climate entity representing Insnrg Pool data."""

    _attr_hvac_modes = [None]
    _attr_hvac_mode = None
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, description):
        """Initialize Insnrg Pool climate."""
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
        """Update the state of the climate entity from coordinator data."""
        thermostat_status = self._get_thermostat_status()
        self._attr_target_temperature = thermostat_status.get(
            "ggPoolSetTemperature"
        ) or thermostat_status.get("value")
        
        temp_sensor_status = self.coordinator.data.get(self.entity_description.key, {}).get("temperatureSensorStatus", {})
        self._attr_current_temperature = temp_sensor_status.get("value")

        self._attr_max_temp = thermostat_status.get("valueMax")
        self._attr_min_temp = thermostat_status.get("valueMin")

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        # This logic seems odd for a climate entity, but preserving it from original
        if self.entity_description.key == "PH":
            return 0.1
        elif self.entity_description.key == "ORP":
            return 10
        else:
            return 0.5

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp_value = kwargs.get("temperature")
        if temp_value is None:
            return

        # Optimistic update
        original_temp = self._attr_target_temperature
        self._attr_target_temperature = temp_value
        self.async_write_ha_state()

        deviceId = self.coordinator.data[self.entity_description.key]["deviceId"]
        success = await self.coordinator.insnrg_pool.set_thermostat_temp(
            temp_value, deviceId
        )

        if not success:
            self._attr_target_temperature = original_temp
            self.async_write_ha_state()
            _LOGGER.error(f"Failed to set temperature for {self.entity_id}.")

        await self.coordinator.async_request_refresh()
"""Switch platform for the Insnrg Pool integration."""
from __future__ import annotations

import asyncio
import logging
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import InsnrgPoolEntity
from .const import DOMAIN
from .polling_mixin import PollingMixin, STARTER_ICON
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer switch setup to the shared switch module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    # Dynamically discover all devices that support switching
    # by checking for non-empty switchStatus property
    for device_id, device_data in coordinator.data.items():
        if isinstance(device_data, dict) and device_data.get("switchStatus"):
            description = SwitchEntityDescription(
                key=device_id,
                name=f'{device_data["name"]} Switch',
            )
            new_switch = InsnrgPoolSwitch(
                coordinator,
                config_entry.data[CONF_EMAIL],
                description,
                device_id,
                hass,
            )
            entities.append(new_switch)
            _LOGGER.debug("Created switch entity: %s (%s)", new_switch.entity_id, new_switch.name)

    _LOGGER.info(f"Insnrg switch setup: created {len(entities)} switch entities")
    async_add_entities(entities, True)


class InsnrgPoolSwitch(InsnrgPoolEntity, SwitchEntity, PollingMixin):
    """Switch representing Insnrg Pool data."""

    def __init__(self, coordinator, email, description, device_id, hass):
        """Initialize Insnrg Pool switch."""
        super().__init__(coordinator, email, description)
        self._device_id = device_id
        self.hass = hass # Required for polling mixin
        # Initialize _attr_is_on based on current coordinator data
        self._attr_is_on = self.coordinator.data[self._device_id].get("switchStatus") == "ON"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        # Always return _attr_is_on for optimistic updates
        return self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        # Optimistic update
        self._attr_is_on = True
        self.async_write_ha_state()
        original_icon = getattr(self, '_attr_icon', None) # Capture original icon
        self._attr_icon = STARTER_ICON # Set starter icon
        self.async_write_ha_state()

        api_call_task = asyncio.create_task(
            self.coordinator.insnrg_pool.turn_the_switch("ON", self._device_id)
        )
        
        await asyncio.sleep(1.0) # Delay for 1 second before starting clock animation

        animation_task = asyncio.create_task(self._async_animate_icon(self, original_icon))
        success = await api_call_task # Wait for the API call to complete

        if success:
            # Pass a lambda that checks the actual coordinator data
            poll_success = await self._async_poll_for_state_change(
                self,
                original_icon,
                "ON",
                lambda: self.coordinator.data[self._device_id].get("switchStatus"),
                entity_type="switchStatus",
                animation_task=animation_task,
            )
            if not poll_success:
                # Revert if polling failed, get actual state from coordinator
                self._attr_is_on = self.coordinator.data[self._device_id].get("switchStatus") == "ON"
                self.async_write_ha_state()
        else:
            _LOGGER.error(
                "Failed to turn ON %s.", self.entity_id
            )
            # Revert if command failed, get actual state from coordinator
            self._attr_is_on = self.coordinator.data[self._device_id].get("switchStatus") == "ON"
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        # Optimistic update
        self._attr_is_on = False
        self.async_write_ha_state()
        original_icon = getattr(self, '_attr_icon', None) # Capture original icon
        self._attr_icon = STARTER_ICON # Set starter icon
        self.async_write_ha_state()

        api_call_task = asyncio.create_task(
            self.coordinator.insnrg_pool.turn_the_switch("OFF", self._device_id)
        )
        
        await asyncio.sleep(1.0) # Delay for 1 second before starting clock animation

        animation_task = asyncio.create_task(self._async_animate_icon(self, original_icon))
        success = await api_call_task # Wait for the API call to complete

        if success:
            # Pass a lambda that checks the actual coordinator data
            poll_success = await self._async_poll_for_state_change(
                self,
                original_icon,
                "OFF",
                lambda: self.coordinator.data[self._device_id].get("switchStatus"),
                entity_type="switchStatus",
                animation_task=animation_task,
            )
            if not poll_success:
                # Revert if polling failed, get actual state from coordinator
                self._attr_is_on = self.coordinator.data[self._device_id].get("switchStatus") == "ON"
                self.async_write_ha_state()
        else:
            _LOGGER.error(
                "Failed to turn OFF %s.", self.entity_id
            )
            # Revert if command failed, get actual state from coordinator
            self._attr_is_on = self.coordinator.data[self._device_id].get("switchStatus") == "ON"
            self.async_write_ha_state()

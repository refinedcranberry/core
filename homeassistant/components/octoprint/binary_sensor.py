"""Support for monitoring OctoPrint binary sensors."""
from abc import abstractmethod
import logging
from typing import Optional

from pyoctoprintapi import OctoprintPrinterInfo

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN as COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the available OctoPrint binary sensors."""
    coordinator = hass.data[COMPONENT_DOMAIN][config_entry.entry_id]["coordinator"]

    entities = [
        OctoPrintPrintingBinarySensor(coordinator, config_entry.unique_id),
        OctoPrintPrintingErrorBinarySensor(coordinator, config_entry.unique_id),
    ]

    async_add_entities(entities)


class OctoPrintBinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    """Representation an OctoPrint binary sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        sensor_type: str,
        device_id: str,
    ) -> None:
        """Initialize a new OctoPrint sensor."""
        super().__init__(coordinator)
        self._name = f"Octoprint {sensor_type}"
        self.sensor_type = sensor_type
        self._device_id = device_id

    @property
    def device_info(self):
        """Device info."""
        return {
            "identifiers": {(COMPONENT_DOMAIN, self._device_id)},
            "manufacturer": "Octoprint",
            "name": "Octoprint",
        }

    @property
    def unique_id(self):
        """Return a unique id."""
        return f"{self.sensor_type}-{self._device_id}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if binary sensor is on."""
        printer = self.coordinator.data["printer"]
        if not printer:
            return None

        return bool(self._get_flag_state(printer))

    @abstractmethod
    def _get_flag_state(self, printer_info: OctoprintPrinterInfo) -> Optional[bool]:
        """Return the value of the sensor flag."""


class OctoPrintPrintingBinarySensor(OctoPrintBinarySensorBase):
    """Representation an OctoPrint binary sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize a new OctoPrint sensor."""
        super().__init__(coordinator, "Printing", device_id)

    def _get_flag_state(self, printer_info: OctoprintPrinterInfo) -> Optional[bool]:
        return bool(printer_info.state.flags.printing)


class OctoPrintPrintingErrorBinarySensor(OctoPrintBinarySensorBase):
    """Representation an OctoPrint binary sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize a new OctoPrint sensor."""
        super().__init__(coordinator, "Printing Error", device_id)

    def _get_flag_state(self, printer_info: OctoprintPrinterInfo) -> Optional[bool]:
        return bool(printer_info.state.flags.error)

from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorEntityDescription

from custom_components.insnrg.const import TEMP_SENSOR_KEY
from custom_components.insnrg.sensor import InsnrgPoolSensor, InsnrgPoolTempSensor


def test_sensor_native_value_reads_temperature_sensor_status():
    coordinator = MagicMock()
    coordinator.data = {
        "PH": {"temperatureSensorStatus": {"value": 7.2}},
    }
    description = SensorEntityDescription(key="PH", name="pH Sensor")

    sensor = InsnrgPoolSensor(coordinator, "test@example.com", description)

    assert sensor.native_value == 7.2


def test_temp_sensor_native_value_and_unit():
    coordinator = MagicMock()
    coordinator.data = {
        TEMP_SENSOR_KEY: {"temperatureSensorStatus": {"value": 26.5}},
    }
    description = SensorEntityDescription(key=TEMP_SENSOR_KEY, name="Pool Temperature")

    sensor = InsnrgPoolTempSensor(coordinator, "test@example.com", description)

    assert sensor.native_value == 26.5
    assert sensor.native_unit_of_measurement == "°C"

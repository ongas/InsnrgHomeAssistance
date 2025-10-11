"""Fixtures for tests."""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def hass():
    """Mock HomeAssistant instance."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    return mock_hass

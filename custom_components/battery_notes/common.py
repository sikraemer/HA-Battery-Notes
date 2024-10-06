"""Common functions for battery_notes."""

from homeassistant.helpers.device_registry import DeviceEntry


def validate_is_float(num):
    """Validate value is a float."""
    if num:
        try:
            float(num)
            return True
        except ValueError:
            return False
    return False


def validate_is_binary(val):
    """Validate value is a a binary value."""
    return val is not None and (val == "on" or val == "off")


def validate_state_is_compatible(state):
    """Validates that the state is either float or binary"""
    return validate_is_float(state) or validate_is_binary(state)


def get_device_model_id(device_entry: DeviceEntry) -> str | None:
    """Get the device model if available."""
    return device_entry.model_id if hasattr(device_entry, "model_id") else None

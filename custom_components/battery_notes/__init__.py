"""Custom integration to integrate BatteryNotes with Home Assistant.

For more details about this integration, please refer to
https://github.com/andrew-codechimp/ha-battery-notes
"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.homeassistant import exposed_entities
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from .const import CONF_DEVICE_ID

_LOGGER = logging.getLogger(__name__)


@callback
def async_add_to_device(
    hass: HomeAssistant, entry: ConfigEntry, entity_id: str
) -> str | None:
    """Add our config entry to the device."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    device_id = None


    device_id = entry.data.get(CONF_DEVICE_ID)

    # if (
    #     not (battery_note := entity_registry.async_get(entity_id))
    #     or not (device_id := battery_note.device_id)
    #     or not (device_registry.async_get(device_id))
    # ):
    #     return device_id

    device_registry.async_update_device(device_id, add_config_entry_id=entry.entry_id)

    return device_id


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    entity_id = entry.entry_id

    # try:
    #     entity_id = er.async_validate_entity_id(registry, entry.options[CONF_ENTITY_ID])
    # except vol.Invalid:
    #     # The entity is identified by an unknown entity registry ID
    #     _LOGGER.error(
    #         "Failed to setup battery note for unknown entity %s",
    #         entry.options[CONF_ENTITY_ID],
    #     )
    #     return False

    async def async_registry_updated(event: Event) -> None:
        """Handle entity registry update."""
        data = event.data
        if data["action"] == "remove":
            await hass.config_entries.async_remove(entry.entry_id)

        if data["action"] != "update":
            return

        if "entity_id" in data["changes"]:
            # Entity_id changed, reload the config entry
            await hass.config_entries.async_reload(entry.entry_id)

        if device_id and "device_id" in data["changes"]:
            # If the tracked switch is no longer in the device, remove our config entry
            # from the device
            if (
                not (entity_entry := registry.async_get(data[CONF_ENTITY_ID]))
                or not device_registry.async_get(device_id)
                or entity_entry.device_id == device_id
            ):
                # No need to do any cleanup
                return

            device_registry.async_update_device(
                device_id, remove_config_entry_id=entry.entry_id
            )

    entry.async_on_unload(
        async_track_entity_registry_updated_event(
            hass, entity_id, async_registry_updated
        )
    )

    device_id = async_add_to_device(hass, entry, entity_id)

    await hass.config_entries.async_forward_entry_setups(
        entry, (Platform.SENSOR,)
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry, (Platform.SENSOR,)
    )


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Unload a config entry.

    This will unhide the wrapped entity and restore assistant expose settings.
    """
    registry = er.async_get(hass)
    try:
        switch_entity_id = er.async_validate_entity_id(
            registry, entry.entry_id
        )
    except vol.Invalid:
        # The source entity has been removed from the entity registry
        return

    if not (battery_note_entity_entry := registry.async_get(switch_entity_id)):
        return


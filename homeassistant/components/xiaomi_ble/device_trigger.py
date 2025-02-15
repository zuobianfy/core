"""Provides device triggers for Xiaomi BLE."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_EVENT,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import (
    BUTTON_PRESS,
    BUTTON_PRESS_DOUBLE_LONG,
    CONF_SUBTYPE,
    DOMAIN,
    EVENT_CLASS,
    EVENT_CLASS_BUTTON,
    EVENT_CLASS_MOTION,
    EVENT_TYPE,
    MOTION_DEVICE,
    XIAOMI_BLE_EVENT,
)

TRIGGERS_BY_TYPE = {
    BUTTON_PRESS: ["press"],
    BUTTON_PRESS_DOUBLE_LONG: ["press", "double_press", "long_press"],
    MOTION_DEVICE: ["motion_detected"],
}


@dataclass
class TriggerModelData:
    """Data class for trigger model data."""

    schema: vol.Schema
    event_class: str
    triggers: list[str]


TRIGGER_MODEL_DATA = {
    BUTTON_PRESS: TriggerModelData(
        schema=DEVICE_TRIGGER_BASE_SCHEMA.extend(
            {
                vol.Required(CONF_TYPE): vol.In([EVENT_CLASS_BUTTON]),
                vol.Required(CONF_SUBTYPE): vol.In(TRIGGERS_BY_TYPE[BUTTON_PRESS]),
            }
        ),
        event_class=EVENT_CLASS_BUTTON,
        triggers=TRIGGERS_BY_TYPE[BUTTON_PRESS],
    ),
    BUTTON_PRESS_DOUBLE_LONG: TriggerModelData(
        schema=DEVICE_TRIGGER_BASE_SCHEMA.extend(
            {
                vol.Required(CONF_TYPE): vol.In([EVENT_CLASS_BUTTON]),
                vol.Required(CONF_SUBTYPE): vol.In(
                    TRIGGERS_BY_TYPE[BUTTON_PRESS_DOUBLE_LONG]
                ),
            }
        ),
        event_class=EVENT_CLASS_BUTTON,
        triggers=TRIGGERS_BY_TYPE[BUTTON_PRESS_DOUBLE_LONG],
    ),
    MOTION_DEVICE: TriggerModelData(
        schema=DEVICE_TRIGGER_BASE_SCHEMA.extend(
            {
                vol.Required(CONF_TYPE): vol.In([EVENT_CLASS_MOTION]),
                vol.Required(CONF_SUBTYPE): vol.In(TRIGGERS_BY_TYPE[MOTION_DEVICE]),
            }
        ),
        event_class=EVENT_CLASS_MOTION,
        triggers=TRIGGERS_BY_TYPE[MOTION_DEVICE],
    ),
}


MODEL_DATA = {
    "JTYJGD03MI": TRIGGER_MODEL_DATA[BUTTON_PRESS],
    "MS1BB(MI)": TRIGGER_MODEL_DATA[BUTTON_PRESS],
    "RTCGQ02LM": TRIGGER_MODEL_DATA[BUTTON_PRESS],
    "SJWS01LM": TRIGGER_MODEL_DATA[BUTTON_PRESS],
    "K9B-1BTN": TRIGGER_MODEL_DATA[BUTTON_PRESS_DOUBLE_LONG],
    "K9B-2BTN": TRIGGER_MODEL_DATA[BUTTON_PRESS_DOUBLE_LONG],
    "K9B-3BTN": TRIGGER_MODEL_DATA[BUTTON_PRESS_DOUBLE_LONG],
    "K9BB-1BTN": TRIGGER_MODEL_DATA[BUTTON_PRESS_DOUBLE_LONG],
    "YLAI003": TRIGGER_MODEL_DATA[BUTTON_PRESS_DOUBLE_LONG],
    "XMWXKG01LM": TRIGGER_MODEL_DATA[BUTTON_PRESS_DOUBLE_LONG],
    "XMWXKG01YL": TRIGGER_MODEL_DATA[BUTTON_PRESS_DOUBLE_LONG],
    "MUE4094RT": TRIGGER_MODEL_DATA[MOTION_DEVICE],
}


async def async_validate_trigger_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate trigger config."""
    device_id = config[CONF_DEVICE_ID]
    if model_data := _async_trigger_model_data(hass, device_id):
        return model_data.schema(config)  # type: ignore[no-any-return]
    return config


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List a list of triggers for Xiaomi BLE devices."""

    # Check if device is a model supporting device triggers.
    if not (model_data := _async_trigger_model_data(hass, device_id)):
        return []

    event_type = model_data.event_class
    event_subtypes = model_data.triggers
    return [
        {
            # Required fields of TRIGGER_BASE_SCHEMA
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            # Required fields of TRIGGER_SCHEMA
            CONF_TYPE: event_type,
            CONF_SUBTYPE: event_subtype,
        }
        for event_subtype in event_subtypes
    ]


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    return await event_trigger.async_attach_trigger(
        hass,
        event_trigger.TRIGGER_SCHEMA(
            {
                event_trigger.CONF_PLATFORM: CONF_EVENT,
                event_trigger.CONF_EVENT_TYPE: XIAOMI_BLE_EVENT,
                event_trigger.CONF_EVENT_DATA: {
                    CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                    EVENT_CLASS: config[CONF_TYPE],
                    EVENT_TYPE: config[CONF_SUBTYPE],
                },
            }
        ),
        action,
        trigger_info,
        platform_type="device",
    )


def _async_trigger_model_data(
    hass: HomeAssistant, device_id: str
) -> TriggerModelData | None:
    """Get available triggers for a given model."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device and device.model and (model_data := MODEL_DATA.get(device.model)):
        return model_data
    return None

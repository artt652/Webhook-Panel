from .config_flow import WebhookPanelConfigFlow
from .options_flow import WebhookPanelOptionsFlowHandler

async def async_setup_entry(hass, entry):
    from .panel import async_setup_panel
    await async_setup_panel(hass, entry)
    return True

async def async_unload_entry(hass, entry):
    # можно добавить логику для удаления файлов
    return True

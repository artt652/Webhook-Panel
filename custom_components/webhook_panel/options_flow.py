import voluptuous as vol
from homeassistant import config_entries

DOMAIN = "webhook_panel"


class WebhookPanelOptionsFlowHandler(config_entries.OptionsFlow):

    async def async_step_init(self, user_input=None):
        entry = self.config_entry

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    "columns",
                    default=entry.data.get("columns", 3),
                ): vol.Coerce(int),
                vol.Required(
                    "rows",
                    default=entry.data.get("rows", 2),
                ): vol.Coerce(int),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
import os
import json
import logging
from homeassistant.components import frontend
from .const import PANEL_URL, WWW_DIR
from .automation_reader import (
    read_automations_yaml,
    read_storage_automations,
    extract_webhooks,
)

_LOGGER = logging.getLogger(__name__)

INDEX_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"/>
<meta http-equiv="Pragma" content="no-cache"/>
<meta http-equiv="Expires" content="0"/>
<title>Webhook Panel</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {
  margin: 0;
  background: #0f172a;
  color: #e5e7eb;
  font-family: system-ui, sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 85vh;
}
.card {
  background: #020617;
  padding: 24px;
  border-radius: 16px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 10px 30px rgba(0,0,0,.5);
}
h1 {
  font-size: 1.2rem;
  margin-top: 0;
  margin-bottom: 16px;
  text-align: center;
}
.grid {
  display: grid;
  gap: 12px;
}
button {
  padding: 16px;
  font-size: 1rem;
  border-radius: 14px;
  border: none;
  background: #22c55e;
  color: #022c22;
  cursor: pointer;
  transition: transform 0.1s ease;
}
button:hover {
  transform: scale(1.05);
}
.status {
  font-size: 0.85rem;
  opacity: 0.8;
  margin-top: 10px;
}
</style>
</head>
<body>
<div class="card">
<h1>Webhook Panel</h1>
<div id="grid" class="grid"></div>
<div id="status" class="status"></div>
</div>

<script src="config.js?__VERSION__"></script>
<script>
const grid = document.getElementById("grid");
const status = document.getElementById("status");

const columns = APP_CONFIG.layout.columns || 3;
const rows = APP_CONFIG.layout.rows || 2;

const totalButtons = APP_CONFIG.buttons.length;
const realRows = Math.min(rows, Math.ceil(totalButtons / columns));

grid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
grid.style.gridTemplateRows = `repeat(${realRows}, auto)`;

APP_CONFIG.buttons.forEach(btn => {
  const b = document.createElement("button");
  b.textContent = btn.label;
  b.onclick = async () => {
    status.textContent = "Отправка...";
    try {
      const res = await fetch(btn.webhook, { method: "POST" });
      if (!res.ok) throw new Error(res.status);
      status.textContent = `Webhook "${btn.label}" отправлен`;
    } catch (e) {
      status.textContent = "Ошибка: " + e.message;
    }
  };
  grid.appendChild(b);
});
</script>
</body>
</html>
"""


async def async_setup_panel(hass, entry):

    www = hass.config.path(WWW_DIR)
    os.makedirs(www, exist_ok=True)

    def regenerate(options=None):
        """Создать config.js и index.html."""
        _LOGGER.info("Webhook Panel: regenerating config")

        # читаем все автоматизации
        automations_yaml = read_automations_yaml(hass.config.path("automations.yaml"))
        automations_storage = read_storage_automations(hass)
        automations = automations_yaml + automations_storage
        webhooks = extract_webhooks(automations)
        _LOGGER.info("Webhook Panel: found %d webhook buttons", len(webhooks))

        # layout
        layout = options or entry.options or entry.data
        columns = layout.get("columns", 3)
        rows = layout.get("rows", 2)

        # --- config.js ---
        config = {
            "layout": {"columns": columns, "rows": rows},
            "buttons": [{"label": w["name"], "webhook": f"/api/webhook/{w['id']}"} for w in webhooks],
        }
        config_path = os.path.join(www, "config.js")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("window.APP_CONFIG = ")
            json.dump(config, f, ensure_ascii=False, indent=2)
            f.write(";")

        # --- index.html с версией ---
        version = int(os.path.getmtime(config_path))
        index_path = os.path.join(www, "index.html")
        html = INDEX_HTML.replace("__VERSION__", str(version))
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)

    # listener для обновления options
    async def _update_listener(hass, updated_entry):
        """Перегенерация при изменении Options."""
        await hass.async_add_executor_job(lambda: regenerate(updated_entry.options))

    entry.add_update_listener(_update_listener)
    
    # первый запуск
    await hass.async_add_executor_job(regenerate)

    # live reload при перезагрузке автоматизаций
    entry.async_on_unload(
        hass.bus.async_listen(
            "automation_reloaded",
            lambda e: hass.async_add_executor_job(regenerate),
        )
    )

    # регистрация панели
#    try:
#        frontend.async_register_built_in_panel(
#            hass,
#            component_name="panel_iframe",
#            sidebar_title=entry.data.get("title", "Webhook Panel"),
#            sidebar_icon="mdi:gesture-tap-button",
#            frontend_url_path=PANEL_URL,
#            config={"url": f"/local/{PANEL_URL}/index.html"},
#        )
#    except ValueError:
#        _LOGGER.info("Webhook Panel: панель уже зарегистрирована")

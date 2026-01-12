import os
import glob
import yaml
import json
import logging

_LOGGER = logging.getLogger(__name__)

def load_yaml(path):
    """Загрузить YAML файл"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def read_automations_yaml(path):
    """Прочитать automations.yaml и все include"""
    result = []

    if not os.path.exists(path):
        return result

    data = load_yaml(path)
    if data is None:
        return result

    # список автоматизаций
    if isinstance(data, list):
        result.extend(data)

    # словарь с !include / !include_dir_merge_list
    elif isinstance(data, dict):
        for k, v in data.items():
            if k == "!include":
                include_path = os.path.join(os.path.dirname(path), v)
                result.extend(read_automations_yaml(include_path))

            elif k == "!include_dir_merge_list":
                folder = os.path.join(os.path.dirname(path), v)
                for file in sorted(glob.glob(folder + "/*.yaml")):
                    result.extend(read_automations_yaml(file))

    return result

def read_storage_automations(hass):
    """Прочитать автоматизации из UI .storage/automations"""
    path = hass.config.path(".storage/automations")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("data", [])

def extract_webhooks(automations):
    """Из списка автоматизаций вытащить webhook-триггеры"""
    webhooks = []

    for a in automations:
        # пропускаем выключенные автоматизации
        if not a.get("enabled", True):
            continue

        triggers = a.get("triggers") or a.get("trigger") or []
        if isinstance(triggers, dict):
            triggers = [triggers]

        for t in triggers:
            # поддержка YAML UI-mode: trigger может быть "trigger" вместо "platform"
            if t.get("platform") == "webhook" or t.get("trigger") == "webhook":
                webhook_id = t.get("webhook_id")
                if webhook_id:
                    webhooks.append({
                        "id": webhook_id,
                        "name": a.get("alias", webhook_id)
                    })

    return webhooks
import json
from pathlib import Path

DEFAULTS_FILE = Path(__file__).resolve().parent / "defaults.json"

def load_defaults():
    if DEFAULTS_FILE.exists():
        with open(DEFAULTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_defaults(data):
    with open(DEFAULTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_defaults(partial_dict):
    """
    Update only the keys provided in parital_dict, preseving all other keys in defaults.json
    """
    data = load_defaults()
    data.update(partial_dict)
    save_defaults(data)

def get_message_templates():
    d = load_defaults()
    return {
        "congrats": d.get("template_congrats", ""),
        "encourage": d.get("template_encourage", "")
    }

def save_message_templates(congrats, encourage):
    d = load_defaults()
    d["template_congrats"] = congrats
    d["template_encourage"] = encourage
    save_defaults(d)

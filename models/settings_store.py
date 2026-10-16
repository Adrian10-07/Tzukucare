import json
import os
import config


def load_settings() -> dict:
    """Lee settings.json; si no existe o está dañado, usa los valores por defecto."""
    settings = dict(config.SETTINGS_DEFAULT)
    try:
        with open(config.SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            settings.update({k: v for k, v in data.items() if k in settings})
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"No se pudo leer {config.SETTINGS_PATH}: {e}. Se usan valores por defecto.")
    return sanitize(settings)


def save_settings(settings: dict):
    """Guarda la configuración de forma atómica (evita archivos corruptos si se corta la luz)."""
    tmp = config.SETTINGS_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(sanitize(settings), f, ensure_ascii=False, indent=2)
        os.replace(tmp, config.SETTINGS_PATH)
        return True
    except Exception as e:
        print(f"No se pudo guardar la configuración: {e}")
        return False


def sanitize(settings: dict) -> dict:
    s = dict(config.SETTINGS_DEFAULT)
    s.update(settings or {})
    s["ladridos"] = min(10, max(1, int(s["ladridos"])))
    s["sensibilidad"] = min(90, max(10, int(s["sensibilidad"])))
    if s["alcance"] not in config.ALCANCES:
        s["alcance"] = "sin_limite"
    if s["umbral_calibrado_db"] is not None:
        s["umbral_calibrado_db"] = float(s["umbral_calibrado_db"])
    if s["alcance"] == "calibrado" and s["umbral_calibrado_db"] is None:
        s["alcance"] = "sin_limite"
    alertas = [a for a in s["alertas_extra"] if a in config.ALERTAS_EXTRA]
    s["alertas_extra"] = list(dict.fromkeys(alertas))[:config.MAX_ALERTAS_EXTRA]
    return s


def umbral_db(settings: dict):
    """Devuelve el umbral de volumen (dBFS) del alcance elegido, o None si no hay límite."""
    if settings["alcance"] == "calibrado":
        return settings["umbral_calibrado_db"]
    return config.ALCANCES[settings["alcance"]][1]

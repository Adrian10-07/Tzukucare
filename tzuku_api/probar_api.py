import sys
import json

from . import cargar_config, faltantes
from .cliente import TzukuApiClient, TzukuApiError


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    config = cargar_config()
    if faltantes(config):
        print(f"Faltan datos (llénalos en Configuración → pestaña API): {', '.join(faltantes(config))}")
        return 1
    with open(sys.argv[1], "rb") as f:
        wav = f.read()

    cliente = TzukuApiClient(config["base_url"], config["email"], config["password"],
                             timeout=config["timeout_http_seg"])
    try:
        print("Iniciando sesión...")
        cliente.login()
        print(f"Subiendo {len(wav) // 1024} KB y esperando resultado (~12 s para 15 s de audio)...")
        resultado = cliente.analizar(wav, config["pet_id"], config["collar_id"],
                                     consultar_cada=config["consultar_cada_seg"],
                                     espera_maxima=config["espera_maxima_seg"])
    except (TzukuApiError, OSError, ValueError) as e:
        print(f"Error: {e}")
        return 1
    if resultado is None:
        print("No llegó resultado a tiempo.")
        return 1
    print(json.dumps(resultado.get("payload", resultado), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

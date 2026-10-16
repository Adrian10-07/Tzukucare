import os

#RUTAS DE ARCHIVOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "lite-model_yamnet_classification_tflite_1.tflite")
ONNX_MODEL_PATH = os.path.join(BASE_DIR, "yamnet_classification.onnx")  # Solo si TFLite no carga (p. ej. Windows)
CLASS_MAP_PATH = os.path.join(BASE_DIR, "yamnet_class_map.csv")
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "firebase_credentials.json")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")  # Configuración guardada por el usuario

#PARÁMETROS DE AUDIO
SAMPLE_RATE_IN = 48000   # Frecuencia nativa del micrófono
SAMPLE_RATE_OUT = 16000  # Frecuencia requerida por YAMNet
CHUNK_SIZE = 46800       # Muestras por iteración (~0.975s a 48kHz)
CHANNELS = 1

#RENDIMIENTO (Raspberry Pi 4: 4 núcleos)
TFLITE_NUM_THREADS = 3   # Deja un núcleo libre para la interfaz y la captura

#ALCANCE DE DETECCIÓN (umbral de volumen en dBFS, medido en ventanas de 100 ms)
# Los valores dependen de la ganancia del micrófono; ajústalos o usa "Calibrar".
VENTANA_NIVEL_SEG = 0.1
ALCANCES = {
    "sin_limite": ("Sin límite", None),
    "lejos":      ("Lejos",      -45.0),
    "media":      ("Media",      -35.0),
    "cerca":      ("Cerca",      -25.0),
    "calibrado":  ("Calibrado",  None),   # usa el valor guardado en settings
}
CALIBRACION_SEG = 5          # Segundos que escucha la calibración
CALIBRACION_MARGEN_DB = 3.0  # El umbral queda 3 dB por debajo del ladrido medido

#CLASES DE LADRIDO (YAMNet)
CLASES_LADRIDO = ["Bark", "Bow-wow"]

#ALERTAS EXTRA: clave -> (nombre visible, clases YAMNet, nivel)
ALERTAS_EXTRA = {
    "disparo":   ("Disparos",                  ["Gunshot, gunfire", "Machine gun", "Cap gun"], "Crítico"),
    "cristal":   ("Cristal roto",              ["Glass", "Shatter"], "Crítico"),
    "humo":      ("Alarma de humo / incendio", ["Smoke detector, smoke alarm", "Fire alarm"], "Crítico"),
    "sirena":    ("Sirena / alerta sísmica",   ["Civil defense siren", "Siren"], "Crítico"),
    "explosion": ("Explosión",                 ["Explosion", "Boom"], "Crítico"),
    "gritos":    ("Gritos",                    ["Screaming", "Yell"], "Advertencia"),
    "bebe":      ("Llanto de bebé",            ["Baby cry, infant cry"], "Advertencia"),
    "coche":     ("Alarma de coche",           ["Car alarm"], "Advertencia"),
}
MAX_ALERTAS_EXTRA = 4
UMBRAL_ALERTAS_EXTRA = 0.50   # Confianza mínima por clase
ENFRIAMIENTO_ALERTA_SEG = 60  # No repetir la misma alerta antes de este tiempo

#VALORES POR DEFECTO DE LA CONFIGURACIÓN
SETTINGS_DEFAULT = {
    "ladridos": 3,
    "sensibilidad": 40,         # %
    "alcance": "sin_limite",
    "umbral_calibrado_db": None,
    "alertas_extra": [],
}

#TEMAS Y CANALES FIREBASE
FCM_TOPIC = "alertas_tzukucare"
FIRESTORE_COLLECTION = "alertas_tzukucare"

#PALETA VISUAL
TURQUESA = "#2EC4B6"
TURQUESA_OSC = "#168F89"
CELESTE = "#8ECAE6"
CELESTE_CLARO = "#E0F4FB"
FONDO_ARRIBA = "#CFF0F7"
FONDO_ABAJO = "#F6FCFE"
AMARILLO = "#FFD97D"
AMARILLO_SUAVE = "#FFF3C9"
TEXTO = "#1F3A4D"
TEXTO_SUAVE = "#6B8798"
ALERTA = "#EF6B6B"
ALERTA_SUAVE = "#FFE6E6"

# Estilo visual por estado: (fondo píldora, texto, fondo perrito, borde tarjeta)
ESTILOS_ESTADO = {
    "REPOSO":                (TURQUESA,  "#FFFFFF", CELESTE_CLARO,  "#BFE6F2"),
    "ESCUCHA ACTIVA":        (AMARILLO,  TEXTO,     AMARILLO_SUAVE, AMARILLO),
    "¡¡ ALARMA ACTIVADA !!": (ALERTA,    "#FFFFFF", ALERTA_SUAVE,   ALERTA),
}
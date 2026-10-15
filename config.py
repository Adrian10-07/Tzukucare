import os

#RUTAS DE ARCHIVOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "lite-model_yamnet_classification_tflite_1.tflite")
CLASS_MAP_PATH = os.path.join(BASE_DIR, "yamnet_class_map.csv")
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "firebase_credentials.json")

#PARÁMETROS DE AUDIO
SAMPLE_RATE_IN = 48000   # Frecuencia nativa del micrófono
SAMPLE_RATE_OUT = 16000  # Frecuencia requerida por YAMNet
CHUNK_SIZE = 46800       # Muestras por iteración (~0.975s a 48kHz)
CHANNELS = 1

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
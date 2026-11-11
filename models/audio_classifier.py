import numpy as np
from scipy.signal import resample_poly

import csv
import config

# Motor de inferencia: TFLite (Raspberry Pi) y, si no se puede cargar, ONNX Runtime
tflite = None
ort = None
try:
    import tensorflow.lite as tflite
except Exception:
    try:
        import tflite_runtime.interpreter as tflite
    except Exception as e_tflite:
        try:
            import onnxruntime as ort
        except Exception as e_onnx:
            raise ImportError(f"No se pudo inicializar TFLite ({e_tflite}) ni ONNX Runtime ({e_onnx})")

try:
    import yamnet as yamnet_model
except Exception:
    yamnet_model = None  # yamnet.py importa TensorFlow; sin él se lee el CSV directamente


def _leer_clases(class_map_csv):
    if yamnet_model is not None:
        return list(yamnet_model.class_names(class_map_csv))
    with open(class_map_csv, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # encabezado
        return [row[2] for row in reader]


def nivel_dbfs(audio_float: np.ndarray, sample_rate: int) -> float:
    """Nivel máximo (dBFS) en ventanas cortas. Un ladrido corto no se diluye en el bloque de ~1 s."""
    # 1. Divide el audio en fragmentos más pequeños (definidos en config.VENTANA_NIVEL_SEG)
    n = max(1, int(sample_rate * config.VENTANA_NIVEL_SEG))
    usable = (len(audio_float) // n) * n
    if usable == 0:
        frames = audio_float.reshape(1, -1)
    else:
        frames = audio_float[:usable].reshape(-1, n)
    # 2. Calcula el valor RMS (raíz cuadrada de la media de los cuadrados) para cada fragmento
    rms = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1))
    # 3. Convierte el valor RMS más alto a la escala logarítmica de decibelios (dBFS)
    return float(20.0 * np.log10(max(float(rms.max()), 1e-10)))


class AudioClassifier:
    def __init__(self, umbral_confianza: float = 0.40):
        if tflite is not None:
            self.backend = "tflite"
            try:
                self.interpreter = tflite.Interpreter(model_path=config.MODEL_PATH,
                                                      num_threads=config.TFLITE_NUM_THREADS)
            except TypeError:
                # Versiones antiguas de TFLite no aceptan num_threads
                self.interpreter = tflite.Interpreter(model_path=config.MODEL_PATH)
            self.interpreter.allocate_tensors()
            self.inputs = self.interpreter.get_input_details()
            self.outputs = self.interpreter.get_output_details()
        else:
            self.backend = "onnx"
            opciones = ort.SessionOptions()
            opciones.intra_op_num_threads = config.TFLITE_NUM_THREADS
            self.session = ort.InferenceSession(config.ONNX_MODEL_PATH, sess_options=opciones,
                                                providers=["CPUExecutionProvider"])
            self.onnx_input = self.session.get_inputs()[0].name
        print(f"Motor de inferencia: {self.backend}")
        self.yamnet_classes = _leer_clases(config.CLASS_MAP_PATH)
        self.umbral_confianza = umbral_confianza  # Ej. 0.40 = 40%
        self.umbral_db = None                     # None = sin límite de alcance

        self.idx_ladrido = self._indices(config.CLASES_LADRIDO)
        self.idx_alertas = {clave: self._indices(clases)
                            for clave, (_, clases, _) in config.ALERTAS_EXTRA.items()}

    def _indices(self, nombres):
        idx = []
        for nombre in nombres:
            if nombre in self.yamnet_classes:
                idx.append(self.yamnet_classes.index(nombre))
            else:
                print(f"Aviso: la clase '{nombre}' no existe en {config.CLASS_MAP_PATH}")
        return idx

    def _infer(self, audio_array: np.ndarray) -> np.ndarray:
        if self.backend == "tflite":
            self.interpreter.set_tensor(self.inputs[0]['index'], audio_array)
            self.interpreter.invoke()
            return self.interpreter.get_tensor(self.outputs[0]['index'])
        return self.session.run(None, {self.onnx_input: audio_array})[0]

    def set_umbral_confianza(self, nuevo_umbral: float):
        """Actualiza el nivel mínimo de certeza que debe tener el modelo."""
        self.umbral_confianza = nuevo_umbral

    def set_umbral_db(self, nuevo_umbral_db):
        """Volumen mínimo (dBFS) para analizar el audio. None desactiva el límite de alcance."""
        self.umbral_db = nuevo_umbral_db

    def process_and_classify(self, raw_audio_data: bytes) -> dict:
        audio_hd = np.frombuffer(raw_audio_data, dtype=np.int16)
        audio_float = audio_hd.astype(np.float32) / 32768.0
        nivel = nivel_dbfs(audio_float, config.SAMPLE_RATE_IN)

        resultado = {
            "top_class": "Silencio",
            "top_score": 0.0,
            "score_ladrido": 0.0,
            "es_ladrido": False,
            "nivel_db": nivel,
            "alertas": {},       # clave -> (clase, puntuación) de las alertas extra detectadas
        }

        # Puerta de volumen: si el sonido llega demasiado bajo (lejos), no se analiza
        if self.umbral_db is not None and nivel < self.umbral_db:
            return resultado

        audio_16k = resample_poly(audio_float, up=1, down=3)
        audio_array = audio_16k.astype(np.float32)

        scores = self._infer(audio_array)
        prediction = np.mean(scores, axis=0)

        top_i = int(np.argmax(prediction))
        resultado["top_class"] = self.yamnet_classes[top_i]
        resultado["top_score"] = float(prediction[top_i])

        # La sensibilidad se compara con la puntuación de Bark / Bow-wow, no con la clase principal
        if self.idx_ladrido:
            score_ladrido = float(max(prediction[i] for i in self.idx_ladrido))
            resultado["score_ladrido"] = score_ladrido
            resultado["es_ladrido"] = score_ladrido >= self.umbral_confianza

        for clave, indices in self.idx_alertas.items():
            if not indices:
                continue
            mejor = max(indices, key=lambda i: prediction[i])
            if prediction[mejor] >= config.UMBRAL_ALERTAS_EXTRA:
                resultado["alertas"][clave] = (self.yamnet_classes[mejor], float(prediction[mejor]))

        return resultado

#Funcionamiento: Si configuras umbral_db en, por ejemplo, -35 dBFS, y el micrófono graba un ruido ambiente suave que mide -48 dBFS, la condición nivel < self.umbral_db se cumple (-48 es menor que -35).
#El resultado: El código se detiene inmediatamente y devuelve "Silencio". Evita realizar el remuestreo (resample_poly) y se salta por completo la inferencia del modelo de IA (self._infer), ahorrando valioso procesamiento en la Raspberry Pi. Solo si el volumen supera ese umbral, el audio avanza para ver si es un ladrido o una alerta.
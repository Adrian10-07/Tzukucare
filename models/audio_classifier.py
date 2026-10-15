import re
import numpy as np
from scipy.signal import resample_poly

try:
    import tensorflow.lite as tflite
except Exception:
    try:
        import tflite_runtime.interpreter as tflite
    except Exception as e:
        raise ImportError(f"No se pudo inicializar TFLite: {e}")

import yamnet as yamnet_model
import config

class AudioClassifier:
    def __init__(self, umbral_confianza: float = 0.40):
        self.interpreter = tflite.Interpreter(model_path=config.MODEL_PATH)
        self.interpreter.allocate_tensors()
        self.inputs = self.interpreter.get_input_details()
        self.outputs = self.interpreter.get_output_details()
        self.yamnet_classes = yamnet_model.class_names(config.CLASS_MAP_PATH)
        self.umbral_confianza = umbral_confianza  # Ej. 0.40 = 40%

    def set_umbral_confianza(self, nuevo_umbral: float):
        """Actualiza el nivel mínimo de certeza que debe tener el modelo."""
        self.umbral_confianza = nuevo_umbral

    def process_and_classify(self, raw_audio_data: bytes):
        audio_hd = np.frombuffer(raw_audio_data, dtype=np.int16)
        audio_float = audio_hd.astype(np.float32) / 32768.0

        audio_16k = resample_poly(audio_float, up=1, down=3)
        audio_array = audio_16k.astype(np.float32)

        self.interpreter.set_tensor(self.inputs[0]['index'], audio_array)
        self.interpreter.invoke()
        scores = self.interpreter.get_tensor(self.outputs[0]['index'])
        prediction = np.mean(scores, axis=0)

        top5_i = np.argsort(prediction)[::-1][:5]
        top_class = self.yamnet_classes[top5_i[0]]
        top_score = float(prediction[top5_i[0]])

        resultado = ''.join(' {:12s}: {:.3f}'.format(self.yamnet_classes[i], prediction[i]) for i in top5_i)
        
        # Comprobar si coincide con Bark / Bow-wow
        detecta_clase_ladrido = bool(re.search('Bark', resultado) or re.search('Bow-wow', resultado))

        # Solo valida el ladrido si SUPERA la sensibilidad configurada por el usuario
        es_ladrido = detecta_clase_ladrido and (top_score >= self.umbral_confianza)

        return top_class, top_score, es_ladrido
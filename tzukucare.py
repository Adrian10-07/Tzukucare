import sys, os, time, uuid, re, wave
import numpy as np
import pyaudio

# Carga ligera de TFLite con respaldo
import tensorflow.lite as tflite

import yamnet as yamnet_model

# Carga de modelo y clases con rutas relativas
interpreter = tflite.Interpreter(model_path="./lite-model_yamnet_classification_tflite_1.tflite")
interpreter.allocate_tensors()
inputs = interpreter.get_input_details()
outputs = interpreter.get_output_details()

yamnet_classes = yamnet_model.class_names('./yamnet_class_map.csv')

#Parámetros de audio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 15600  #Captura ~0.975s de audio por iteración

bark = 'Bark'
bow = 'Bow-wow'

def monitoreo():
    p = pyaudio.PyAudio()

    #Nombres de archivos únicos
    iduu = str(uuid.uuid4())[:8]
    nombre_txt = f"experimento-texto-{nombrePrueba}-{int(time.time())}-{iduu}.txt"
    nombre_wav = f"experimento-audio-{nombrePrueba}-{int(time.time())}-{iduu}.wav"

    #Apertura de archivos para escritura progresiva en disco
    f_txt = open(nombre_txt, 'w', encoding='utf-8')
    wf = wave.open(nombre_wav, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)

    #Función auxiliar para inicializar/reconectar micrófono
    def abrir_stream():
        return p.open(format=FORMAT,
                      channels=CHANNELS,
                      rate=RATE,
                      input=True,
                      frames_per_buffer=CHUNK)

    stream = abrir_stream()

    okgoogle = 0
    ladridosTotalDespuesDeEscucha = 0
    ladridosSeguidos = 0
    pausasTODO = 0
    pausaAUX = 0  

    cuantoTiempo = time.time() + duracion

    print("=" * 65)
    print(" >>> INICIANDO MONITOREO OPTIMIZADO PARA RASPBERRY PI <<<")
    print(f" Configuración: Duración={duracion//60}m | Escucha={numeroDeLadridosParaActivarEscucha} | Alarma={numeroDeLadridosParaActivarAlarma}")
    print("=" * 65)

    try:
        while time.time() <= cuantoTiempo:
            #"PREVENCIÓN DESCONEXIÓN"Captura segura de audio
            try:
                dataParaClasificar = stream.read(CHUNK, exception_on_overflow=False)
            except Exception as e:
                print(f"\n[ALERTA AUDIO] Error de lectura, reconectando micrófono... ({e})")
                time.sleep(1)
                try:
                    stream.close()
                    stream = abrir_stream()
                except Exception:
                    pass
                continue

            # [PREVENCIÓN RAM] Guardado directo a disco sin mantener variables pesadas en RAM
            wf.writeframes(dataParaClasificar)

            # [REDUCCIÓN CPU] Conversión directa con NumPy
            audio_array = np.frombuffer(dataParaClasificar, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Inferencia
            interpreter.set_tensor(inputs[0]['index'], np.reshape(audio_array, [1, -1]))
            interpreter.invoke()
            scores = interpreter.get_tensor(outputs[0]['index'])
            prediction = np.mean(scores, axis=0)

            top5_i = np.argsort(prediction)[::-1][:5]
            resultadoPrediccion = ''.join('  {:12s}: {:.3f}'.format(yamnet_classes[i], prediction[i]) for i in top5_i)

            # Formato de salida
            top_class = yamnet_classes[top5_i[0]]
            top_score = prediction[top5_i[0]]
            hora_actual = time.strftime("%H:%M:%S", time.localtime())

            print(f"[{hora_actual}] Detectado: {top_class:18s} | Confianza: {top_score:.2f}", end="")

            es_ladrido = re.search(bark, resultadoPrediccion) or re.search(bow, resultadoPrediccion)

            if not es_ladrido and okgoogle == 1:
                pausaAUX += 1

            if es_ladrido and okgoogle == 1:
                ladridosTotalDespuesDeEscucha += 1
                pausasTODO = 0
                print(f" --> [LADRIDO EN ESCUCHA: {ladridosTotalDespuesDeEscucha}/{numeroDeLadridosParaActivarAlarma}]", end="")

            if not es_ladrido:
                ladridosSeguidos = 0
                pausasTODO += 1
                if pausasTODO == 15:
                    ladridosTotalDespuesDeEscucha = 0
                    ladridosSeguidos = 0
                    okgoogle = 0
                    pausasTODO = 0
                    print(" --> [RESET POR INACTIVIDAD]", end="")

            # Escrito continuo de registros de texto
            f_txt.write(f"{time.time()} {resultadoPrediccion}\n")

            if ladridosTotalDespuesDeEscucha == int(numeroDeLadridosParaActivarAlarma):
                f_txt.write(f"{time.time()} ALARMA ACTIVADA!\n")
                print("\n\n" + "!" * 55)
                print("  ALARMA ACTIVADA - UMBRAL ALCANZADO !")
                print("!" * 55 + "\n")
                ladridosTotalDespuesDeEscucha = 0
                ladridosSeguidos = 0
                okgoogle = 0
                pausaAUX = 0
                pausasTODO = 0

            if es_ladrido and okgoogle == 0:
                pausasTODO = 0
                ladridosSeguidos += 1
                print(f" --> [LADRIDO CONSECUTIVO: {ladridosSeguidos}/{numeroDeLadridosParaActivarEscucha}]", end="")

            if ladridosSeguidos == int(numeroDeLadridosParaActivarEscucha):
                okgoogle = 1
                print(" --> [ESCUCHA ACTIVA INICIADA]", end="")

            if pausaAUX >= int(pausasPermitidas):
                print(" --> [ESCUCHA DESACTIVADA POR PAUSA]", end="")
                ladridosTotalDespuesDeEscucha = 0
                pausaAUX = 0
                ladridosSeguidos = 0
                okgoogle = 0
                pausasTODO = 0  

            print()
            f_txt.flush()  # Fuerza la escritura a disco inmediatamente

    except KeyboardInterrupt:
        print("\nMonitoreo detenido manualmente por el usuario.")

    finally:
        f_txt.close()
        wf.close()
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        p.terminate()

        print("=" * 10)
        print(f"PROCESO FINALIZADO CON ÉXITO.\n Archivos guardados:\n - Texto: {nombre_txt}\n - Audio: {nombre_wav}")
        print("=" * 10)

if __name__ == '__main__':
    numeroDeLadridosParaActivarAlarma = sys.argv[1]
    numeroDeLadridosParaActivarEscucha = sys.argv[2]
    duracion = int(sys.argv[3]) * 60
    pausasPermitidas = sys.argv[4]
    nombrePrueba = sys.argv[5]
    monitoreo()
"""Hilo que mantiene el registro del dispositivo en Firestore y su código de vinculación."""
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

from PyQt5.QtCore import QThread, pyqtSignal

from . import (COLECCION_DISPOSITIVOS, COLECCION_CODIGOS, VIGENCIA_CODIGO_SEG,
               REFRESCO_SEG, ESQUEMA_QR)


class SyncService(QThread):
    """Corre aparte para que la red nunca congele la interfaz ni el micrófono.

    Firestore:
      dispositivos/{id}              nombre, codigo, codigo_expira, admin_uid, miembros_uids,
                                     tzuku_pet_id, tzuku_collar_id, ultimo_latido
      dispositivos/{id}/miembros/{uid}   uid, email, nombre, unido_en, codigo
      codigos_vinculacion/{codigo}   dispositivo_id, expira
    La app es la que agrega y quita miembros; la Pi solo publica el código y lee el estado.
    """
    log_signal = pyqtSignal(str)
    estado_signal = pyqtSignal(dict)        # para la pestaña "Vincular"
    mascota_signal = pyqtSignal(str, str)   # pet_id, collar_id que puso el admin en la app

    def __init__(self, firebase_service, identidad: dict):
        super().__init__()
        self.firebase = firebase_service
        self.dispositivo_id = identidad["id"]
        self.nombre = identidad.get("nombre") or "TzukuCare"
        self._despertar = threading.Event()
        self._activo = True
        self._forzar_codigo = False
        self._quitar_todos = False
        self._mascota = None
        self.estado = {"conectado": False, "codigo": None, "expira": None,
                       "miembros": [], "admin": None, "nombre": self.nombre,
                       "dispositivo_id": self.dispositivo_id}

    # ---------- API para la interfaz (cualquier hilo) ----------
    def qr_texto(self) -> str:
        codigo = self.estado.get("codigo") or ""
        return f"{ESQUEMA_QR}?d={self.dispositivo_id}&c={codigo}"

    def nuevo_codigo(self):
        self._forzar_codigo = True
        self._despertar.set()

    def quitar_todos(self):
        """Desvincula a todos los usuarios (por ejemplo, si el equipo cambia de dueño)."""
        self._quitar_todos = True
        self._despertar.set()

    def crear_panel(self):
        from .panel import PanelVincular
        return PanelVincular(self)

    def stop(self):
        self._activo = False
        self._despertar.set()
        self.wait(3000)

    # ---------- Hilo ----------
    def run(self):
        db = getattr(self.firebase, "db", None)
        if not getattr(self.firebase, "is_connected", False) or db is None:
            self.log_signal.emit("Sincronización: Firebase no está conectado, no se puede vincular la app.")
            self.estado_signal.emit(dict(self.estado))
            return

        self._db = db
        self.log_signal.emit(f"Sincronización activa (dispositivo {self.dispositivo_id})")
        while self._activo:
            try:
                self._ciclo()
                self.estado["conectado"] = True
            except Exception as e:  # sin red, permisos, etc.: se reintenta en el siguiente ciclo
                self.estado["conectado"] = False
                self.log_signal.emit(f"Sincronización: {e}")
            self.estado_signal.emit(dict(self.estado))
            self._despertar.wait(REFRESCO_SEG)
            self._despertar.clear()

    def _ciclo(self):
        from firebase_admin import firestore

        ref = self._db.collection(COLECCION_DISPOSITIVOS).document(self.dispositivo_id)
        snap = ref.get()
        if not snap.exists:
            ref.set({
                "nombre": self.nombre,
                "codigo": None,
                "codigo_expira": None,
                "admin_uid": None,
                "miembros_uids": [],
                "tzuku_pet_id": "",
                "tzuku_collar_id": "",
                "creado": firestore.SERVER_TIMESTAMP,
            })
            snap = ref.get()
        datos = snap.to_dict() or {}

        if self._quitar_todos:
            self._quitar_todos = False
            self._desvincular_todos(ref, datos)
            datos = ref.get().to_dict() or {}

        # Código de vinculación: se renueva al vencer o cuando se pide desde el panel
        expira = datos.get("codigo_expira")
        ahora = datetime.now(timezone.utc)
        if self._forzar_codigo or not datos.get("codigo") or not expira or expira <= ahora + timedelta(seconds=REFRESCO_SEG):
            self._forzar_codigo = False
            datos["codigo"], datos["codigo_expira"] = self._renovar_codigo(ref, datos.get("codigo"))

        ref.update({"ultimo_latido": firestore.SERVER_TIMESTAMP})

        # Miembros (orden de antigüedad = orden de miembros_uids)
        uids = list(datos.get("miembros_uids") or [])
        miembros = []
        if uids:
            docs = {d.id: d.to_dict() or {} for d in ref.collection("miembros").stream()}
            for uid in uids:
                m = docs.get(uid, {})
                miembros.append({"uid": uid, "email": m.get("email", ""), "nombre": m.get("nombre", ""),
                                 "admin": uid == datos.get("admin_uid")})

        self.nombre = datos.get("nombre") or self.nombre
        self.estado.update({
            "codigo": datos["codigo"],
            "expira": datos["codigo_expira"],
            "miembros": miembros,
            "admin": next((m for m in miembros if m["admin"]), None),
            "nombre": self.nombre,
        })

        mascota = (str(datos.get("tzuku_pet_id") or ""), str(datos.get("tzuku_collar_id") or ""))
        if mascota != self._mascota:
            if self._mascota is not None or any(mascota):
                self.mascota_signal.emit(*mascota)
            self._mascota = mascota

    def _renovar_codigo(self, ref, anterior):
        codigos = self._db.collection(COLECCION_CODIGOS)
        expira = datetime.now(timezone.utc) + timedelta(seconds=VIGENCIA_CODIGO_SEG)
        for _ in range(10):  # evita chocar con el código vigente de otro dispositivo
            codigo = f"{secrets.randbelow(1_000_000):06d}"
            otro = codigos.document(codigo).get()
            libre = not otro.exists or (otro.to_dict() or {}).get("expira") is None \
                or otro.to_dict()["expira"] <= datetime.now(timezone.utc)
            if libre and codigo != anterior:
                break
        codigos.document(codigo).set({"dispositivo_id": self.dispositivo_id, "expira": expira})
        ref.update({"codigo": codigo, "codigo_expira": expira})
        if anterior and anterior != codigo:
            try:
                codigos.document(anterior).delete()
            except Exception:
                pass
        return codigo, expira

    def _desvincular_todos(self, ref, datos):
        for d in ref.collection("miembros").stream():
            d.reference.delete()
        ref.update({"miembros_uids": [], "admin_uid": None})
        self._forzar_codigo = True  # quien tenía el código anterior ya no puede volver a entrar
        self.log_signal.emit("Sincronización: se desvincularon todos los usuarios.")

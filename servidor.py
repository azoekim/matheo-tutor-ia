"""
=============================================================================
FASE 3 y 5: EL SERVIDOR WEB Y EN LA NUBE (servidor.py)
=============================================================================
Incluye además el Webhook (/api/whatsapp/webhook) para que cuando tú le
escribas al número externo del bot en WhatsApp (+1 415 523 8886), el bot
reciba tu mensaje, consulte a Matheo IA y te responda por WhatsApp.
=============================================================================
"""

import html
import json
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from memoria import cargar_memoria, guardar_memoria, MEMORIA_INICIAL
from cerebro_tutor import consultar_ia, TEMARIO_POR_NIVEL
from whatsapp_recordatorios import (
    enviar_recordatorio_numero_externo,
    construir_mensaje_recordatorio,
    verificar_y_enviar_recordatorio_diario
)

CARPETA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_STATIC = os.path.join(CARPETA_ACTUAL, "static")
ARCHIVO_ENV = os.path.join(CARPETA_ACTUAL, ".api_key.txt")


def obtener_api_key_guardada():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY").strip()
    if os.path.exists(ARCHIVO_ENV):
        with open(ARCHIVO_ENV, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def guardar_api_key_local(llave):
    with open(ARCHIVO_ENV, "w", encoding="utf-8") as f:
        f.write(llave.strip())


class ManejadorTutorIA(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _enviar_json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _leer_cuerpo_peticion(self):
        longitud = int(self.headers.get("Content-Length", 0))
        if longitud == 0:
            return ""
        return self.rfile.read(longitud).decode("utf-8", errors="ignore")

    def _responder_twiml_whatsapp(self, mensaje_entrante):
        llave = obtener_api_key_guardada()
        resultado = consultar_ia(mensaje_entrante or "Hola Matheo", api_key=llave)
        texto_respuesta = html.escape(resultado.get("mensaje", "¡Hola! Soy Matheo IA."))

        twiml = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Message>{texto_respuesta}</Message></Response>'
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(twiml)))
        self.end_headers()
        self.wfile.write(twiml)

    def do_GET(self):
        parsed = urlparse(self.path)
        ruta = parsed.path
        query_params = parse_qs(parsed.query)

        # Si Twilio llama por GET a /api/whatsapp/webhook o con parámetros Body/From
        if ruta == "/api/whatsapp/webhook" or "Body" in query_params or "WaId" in query_params:
            mensaje_entrante = (query_params.get("Body", [""])[0] or "").strip()
            self._responder_twiml_whatsapp(mensaje_entrante)
            return

        if ruta == "/api/estado":
            datos = cargar_memoria()
            tiene_key = bool(obtener_api_key_guardada())
            self._enviar_json({
                "datos_alumno": datos,
                "tiene_api_key": tiene_key,
                "temario": TEMARIO_POR_NIVEL
            })
            return

        if ruta == "/" or ruta == "/index.html":
            self.path = "/static/index.html"
        elif not ruta.startswith("/static/"):
            posible = os.path.join(CARPETA_STATIC, ruta.lstrip("/"))
            if os.path.exists(posible):
                self.path = "/static/" + ruta.lstrip("/")

        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        parsed = urlparse(self.path)
        ruta = parsed.path
        cuerpo_raw = self._leer_cuerpo_peticion()

        # Webhook oficial de Twilio WhatsApp: funciona tanto si puso /api/whatsapp/webhook
        # como si pegó la URL raíz https://matheo-tutor-ia.onrender.com/
        if ruta == "/api/whatsapp/webhook" or "From=whatsapp" in cuerpo_raw or "Body=" in cuerpo_raw or "SmsSid=" in cuerpo_raw:
            form = parse_qs(cuerpo_raw)
            mensaje_entrante = (form.get("Body", [""])[0] or "").strip()
            self._responder_twiml_whatsapp(mensaje_entrante)
            return

        body = json.loads(cuerpo_raw) if cuerpo_raw else {}

        if ruta == "/api/chat":
            mensaje = (body.get("mensaje") or "").strip()
            api_key_usuario = (body.get("api_key") or "").strip()
            if api_key_usuario:
                guardar_api_key_local(api_key_usuario)

            llave = api_key_usuario or obtener_api_key_guardada()
            resultado = consultar_ia(mensaje, api_key=llave)
            self._enviar_json(resultado)
            return

        if ruta == "/api/config":
            datos = cargar_memoria()
            if "api_key" in body and body["api_key"].strip():
                guardar_api_key_local(body["api_key"].strip())
            if "nombre" in body and body["nombre"].strip():
                datos["nombre"] = body["nombre"].strip()
            guardar_memoria(datos)
            self._enviar_json({
                "ok": True,
                "datos_alumno": datos,
                "tiene_api_key": bool(obtener_api_key_guardada())
            })
            return

        if ruta == "/api/whatsapp":
            datos = cargar_memoria()
            cfg = datos.get("config_whatsapp", {})
            cfg["activo"] = bool(body.get("activo", cfg.get("activo", True)))
            cfg["proveedor"] = (body.get("proveedor") or cfg.get("proveedor", "twilio")).strip()
            cfg["telefono"] = (body.get("telefono") or cfg.get("telefono", "")).strip()
            cfg["twilio_sid"] = (body.get("twilio_sid") or cfg.get("twilio_sid", "")).strip()
            cfg["twilio_token"] = (body.get("twilio_token") or cfg.get("twilio_token", "")).strip()
            cfg["hora_recordatorio"] = (body.get("hora_recordatorio") or cfg.get("hora_recordatorio", "18:00")).strip()
            datos["config_whatsapp"] = cfg
            guardar_memoria(datos)

            if body.get("probar_ahora"):
                texto = construir_mensaje_recordatorio(datos)
                res = enviar_recordatorio_numero_externo(cfg, texto)
                self._enviar_json({"ok": res.get("ok", False), "detalle": res.get("detalle", ""), "datos_alumno": datos})
                return

            self._enviar_json({
                "ok": True,
                "detalle": "✅ Configuración del número externo de WhatsApp guardada.",
                "datos_alumno": datos
            })
            return

        if ruta == "/api/reiniciar":
            copia_limpia = json.loads(json.dumps(MEMORIA_INICIAL))
            guardar_memoria(copia_limpia)
            self._enviar_json({"ok": True, "datos_alumno": copia_limpia})
            return

        if ruta == "/api/sincronizar":
            datos_actuales = cargar_memoria()
            respaldo = body.get("datos_alumno")
            # Si el servidor gratuito de Render se reinició y perdió la memoria local,
            # restauramos automáticamente el respaldo del dispositivo del alumno
            if isinstance(respaldo, dict):
                xp_servidor = datos_actuales.get("puntos_xp", 0)
                hist_servidor = len(datos_actuales.get("historial_chat", []))
                xp_respaldo = respaldo.get("puntos_xp", 0)
                hist_respaldo = len(respaldo.get("historial_chat", []))
                if xp_respaldo > xp_servidor or (xp_servidor == 0 and hist_servidor <= 2 and hist_respaldo > hist_servidor):
                    for k, v in respaldo.items():
                        if k in datos_actuales:
                            datos_actuales[k] = v
                    guardar_memoria(datos_actuales)
            self._enviar_json({"ok": True, "datos_alumno": datos_actuales})
            return

        self._enviar_json({"error": "Ruta no encontrada"}, 404)


def reloj_recordatorios_en_segundo_plano():
    while True:
        try:
            verificar_y_enviar_recordatorio_diario()
        except Exception:
            pass
        time.sleep(60)


if __name__ == "__main__":
    os.chdir(CARPETA_ACTUAL)
    hilo_reloj = threading.Thread(target=reloj_recordatorios_en_segundo_plano, daemon=True)
    hilo_reloj.start()

    puerto = int(os.environ.get("PORT", 8000))
    servidor = HTTPServer(("0.0.0.0", puerto), ManejadorTutorIA)
    print(f"============================================================")
    print(f"🎓 TUTOR DE MATEMÁTICAS IA ('Matheo') ACTIVO")
    print(f"🌐 Abre en tu navegador: http://localhost:{puerto}")
    print(f"============================================================")
    servidor.serve_forever()

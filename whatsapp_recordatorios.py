"""
=============================================================================
FASE 4: RECORDATORIOS POR WHATSAPP CON NÚMERO EXTERNO OFICIAL
(whatsapp_recordatorios.py)
=============================================================================
¿Por qué es más seguro usar un Número Externo Oficial?
En lugar de vincular tu cuenta personal con un código QR, las empresas y
desarrolladores usan un NÚMERO DE TELÉFONO EXTERNO de WhatsApp Business:

OPCIÓN A: Twilio WhatsApp Sandbox (Número externo: +1 415 523 8886)
- Twilio te da su número oficial verificado de WhatsApp (+1 415 523 8886).
- Tú le escribes a ese número desde tu móvil como a cualquier otro contacto.
- El bot nunca entra en tu cuenta de WhatsApp; solo te envía mensajes desde
  el número +1 415 523 8886.

OPCIÓN B: Meta WhatsApp Cloud API (Número externo gratuito de Meta/Facebook)
- Meta te regala un número de teléfono externo de prueba para que le escribas
  y te envíe recordatorios gratis.
=============================================================================
"""

import base64
import json
import urllib.parse
import urllib.request
import urllib.error
from datetime import date, datetime
from memoria import cargar_memoria, guardar_memoria


def enviar_whatsapp_twilio(account_sid, auth_token, numero_destino, texto_mensaje, numero_bot="whatsapp:+4915888620339"):
    """
    Envía un WhatsApp desde el número externo oficial de Twilio (+1 415 523 8886)
    hacia tu móvil. Tu cuenta de WhatsApp está 100% separada y segura.
    """
    sid = (account_sid or "").strip()
    token = (auth_token or "").strip()
    destino = (numero_destino or "").strip().replace(" ", "").replace("-", "")

    if not sid or not token or not destino:
        return {
            "ok": False,
            "detalle": "Faltan tus datos de Twilio (Account SID, Auth Token o tu número de teléfono con prefijo, ej. +34...)."
        }

    if not destino.startswith("+"):
        destino = "+" + destino
    if not destino.startswith("whatsapp:"):
        destino = f"whatsapp:{destino}"

    if not numero_bot.startswith("whatsapp:"):
        numero_bot = f"whatsapp:{numero_bot}"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    datos_form = urllib.parse.urlencode({
        "From": numero_bot,
        "To": destino,
        "Body": texto_mensaje
    }).encode("utf-8")

    credenciales = base64.b64encode(f"{sid}:{token}".encode("utf-8")).decode("ascii")

    try:
        req = urllib.request.Request(
            url,
            data=datos_form,
            headers={
                "Authorization": f"Basic {credenciales}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "MatheoTutorIA/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            respuesta = json.loads(resp.read().decode("utf-8"))
            return {
                "ok": True,
                "detalle": f"✅ ¡WhatsApp enviado desde el número del bot (+1 415 523 8886) a tu móvil ({destino})!",
                "sid": respuesta.get("sid")
            }
    except urllib.error.HTTPError as e:
        err_txt = e.read().decode("utf-8", errors="ignore")
        return {
            "ok": False,
            "detalle": f"Error de Twilio ({e.code}): Verifica tu Account SID, Auth Token y que hayas enviado el mensaje 'join ...' al +1 415 523 8886. ({err_txt[:140]})"
        }
    except Exception as e:
        return {
            "ok": False,
            "detalle": f"No se pudo conectar con Twilio: {str(e)}"
        }


def enviar_whatsapp_meta(phone_number_id, access_token, numero_destino, texto_mensaje):
    """
    Envía un WhatsApp desde el número externo gratuito de Meta Cloud API.
    """
    pid = (phone_number_id or "").strip()
    token = (access_token or "").strip()
    destino = (numero_destino or "").strip().replace(" ", "").replace("-", "").replace("+", "")

    if not pid or not token or not destino:
        return {
            "ok": False,
            "detalle": "Faltan datos de Meta Cloud API (Phone Number ID, Token o tu teléfono)."
        }

    url = f"https://graph.facebook.com/v20.0/{pid}/messages"
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "to": destino,
        "type": "text",
        "text": {"body": texto_mensaje}
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {
                "ok": True,
                "detalle": f"✅ ¡WhatsApp enviado desde el número oficial de Meta a tu móvil (+{destino})!"
            }
    except urllib.error.HTTPError as e:
        err_txt = e.read().decode("utf-8", errors="ignore")
        return {
            "ok": False,
            "detalle": f"Error de Meta API ({e.code}): {err_txt[:150]}"
        }
    except Exception as e:
        return {
            "ok": False,
            "detalle": f"Error conectando con Meta API: {str(e)}"
        }


def enviar_recordatorio_numero_externo(cfg, texto_mensaje):
    """
    Envía el WhatsApp desde el número externo configurado (Twilio o Meta).
    """
    proveedor = cfg.get("proveedor", "twilio")
    telefono = cfg.get("telefono", "")

    if proveedor == "meta":
        return enviar_whatsapp_meta(
            cfg.get("meta_phone_id", ""),
            cfg.get("meta_token", ""),
            telefono,
            texto_mensaje
        )
    else:
        return enviar_whatsapp_twilio(
            cfg.get("twilio_sid", ""),
            cfg.get("twilio_token", ""),
            telefono,
            texto_mensaje
        )


def construir_mensaje_recordatorio(datos_alumno):
    """
    Crea un mensaje personalizado de WhatsApp según tu nivel, racha y reto pendiente.
    """
    nombre = datos_alumno.get("nombre", "Victor")
    nivel = datos_alumno.get("nivel_actual", 1)
    racha = datos_alumno.get("racha_dias", 0)
    reto = datos_alumno.get("reto_activo")

    mensaje = f"📐 *¡Hola {nombre}! Soy Matheo, tu Tutor de Matemáticas IA*\n\n"
    if racha > 0:
        mensaje += f"🔥 Llevas una racha de *{racha} días seguidos* (Nivel {nivel}). ¡No dejes que se apague hoy!\n\n"
    else:
        mensaje += f"🚀 Hoy es un gran día para avanzar en el *Nivel {nivel}*.\n\n"

    if reto:
        mensaje += f"🎯 *Tienes este reto pendiente:*\n{reto}\n\n"

    mensaje += "💬 _Puedes responder directamente a este número de WhatsApp con tu solución o pidiéndome una pista._"
    return mensaje


def verificar_y_enviar_recordatorio_diario():
    """
    Revisa cada minuto si ya llegó la hora de estudio y el alumno aún no ha practicado hoy.
    """
    datos = cargar_memoria()
    cfg = datos.get("config_whatsapp", {})

    if not cfg.get("activo"):
        return {"enviado": False, "motivo": "Recordatorios desactivados"}

    hoy_str = date.today().isoformat()

    if datos.get("ultima_fecha_estudio") == hoy_str:
        return {"enviado": False, "motivo": "El alumno ya estudió hoy"}

    if cfg.get("ultimo_recordatorio_enviado") == hoy_str:
        return {"enviado": False, "motivo": "Ya se envió el recordatorio de hoy"}

    hora_actual = datetime.now().strftime("%H:%M")
    hora_objetivo = cfg.get("hora_recordatorio", "18:00")

    if hora_actual >= hora_objetivo:
        texto = construir_mensaje_recordatorio(datos)
        resultado = enviar_recordatorio_numero_externo(cfg, texto)
        if resultado.get("ok"):
            datos["config_whatsapp"]["ultimo_recordatorio_enviado"] = hoy_str
            guardar_memoria(datos)
            return {"enviado": True, "motivo": resultado["detalle"]}
        return {"enviado": False, "motivo": resultado.get("detalle", "Error")}

    return {"enviado": False, "motivo": f"Aún no es la hora programada ({hora_objetivo})"}

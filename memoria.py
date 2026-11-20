"""
=============================================================================
FASE 2: LA MEMORIA DE LA IA (memoria.py)
=============================================================================
¿Por qué necesitamos este archivo?
Por defecto, las IAs como Gemini o ChatGPT tienen "amnesia": cada vez que
les hablas desde cero, no recuerdan quién eres, qué nivel de matemáticas tienes
ni en qué te equivocaste ayer.

Este archivo crea y gestiona una "Ficha del Alumno" guardada en un archivo
llamado 'datos_alumno.json'. Así la IA siempre te recuerda.
=============================================================================
"""

import json
import os
from datetime import date, datetime

ARCHIVO_MEMORIA = os.path.join(os.path.dirname(__file__), "datos_alumno.json")

# Esta es la plantilla inicial para un alumno que empieza desde cero
MEMORIA_INICIAL = {
    "nombre": "Victor",
    "prueba_nivel_completada": False,
    "pregunta_diagnostico_actual": 0,  # Va de 1 a 5 durante la prueba inicial
    "nivel_actual": 1,                 # Nivel del 1 al 10
    "titulo_nivel": "Nivel 1: Fundamentos y Diagnóstico Inicial",
    "puntos_xp": 0,                    # Puntos de experiencia (subes de nivel cada 100 XP)
    "racha_dias": 0,                   # Cuántos días seguidos has practicado
    "ultima_fecha_estudio": None,      # Para saber si hoy ya estudiaste o hay que recordártelo
    "retos_resueltos": 0,
    "temas_dominados": [],             # Ej: ["Sumas y restas", "Fracciones básicas"]
    "temas_por_mejorar": [],           # Ej: ["Ecuaciones de primer grado", "Regla de los signos"]
    "ultimo_consejo": "¡Bienvenido! Empecemos con una breve prueba de 5 preguntas para descubrir tu nivel.",
    "reto_activo": None,               # Guarda el reto que tienes pendiente de resolver ahora mismo
    "config_whatsapp": {
        "activo": True,
        "metodo": "ntfy",              # 'ntfy' (100% automático sin registro) o 'whatsapp' (CallMeBot)
        "canal_ntfy": "matheo-tutor-victor-2026",
        "telefono": "",                # Ej: "+34600000000"
        "apikey_callmebot": "",        # Llave gratuita de CallMeBot para WhatsApp
        "hora_recordatorio": "18:00",  # Hora a la que quieres que te avise si no has estudiado
        "ultimo_recordatorio_enviado": None
    },
    "historial_chat": []               # Guarda los últimos mensajes para que el chat tenga continuidad
}


def cargar_memoria():
    """
    Lee el archivo 'datos_alumno.json'.
    Si todavía no existe (porque es la primera vez que abres la app),
    lo crea automáticamente con los datos iniciales.
    """
    if not os.path.exists(ARCHIVO_MEMORIA):
        guardar_memoria(MEMORIA_INICIAL)
        return json.loads(json.dumps(MEMORIA_INICIAL))

    try:
        with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            for clave, valor in MEMORIA_INICIAL.items():
                if clave not in datos:
                    datos[clave] = valor
            if "config_whatsapp" in datos and isinstance(datos["config_whatsapp"], dict):
                for k, v in MEMORIA_INICIAL["config_whatsapp"].items():
                    if k not in datos["config_whatsapp"]:
                        datos["config_whatsapp"][k] = v
            return datos
    except Exception:
        return json.loads(json.dumps(MEMORIA_INICIAL))


def guardar_memoria(datos):
    """
    Guarda los cambios en 'datos_alumno.json' para que no se borren
    aunque apagues el ordenador o cierres el navegador.
    """
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)


def registrar_actividad_diaria(datos):
    """
    Actualiza tu racha de días estudiando.
    """
    hoy = date.today().isoformat()
    ultima = datos.get("ultima_fecha_estudio")

    if ultima == hoy:
        return datos

    if ultima:
        try:
            fecha_anterior = date.fromisoformat(ultima)
            diferencia_dias = (date.today() - fecha_anterior).days
            if diferencia_dias == 1:
                datos["racha_dias"] = datos.get("racha_dias", 0) + 1
            elif diferencia_dias > 1:
                datos["racha_dias"] = 1
        except ValueError:
            datos["racha_dias"] = 1
    else:
        datos["racha_dias"] = 1

    datos["ultima_fecha_estudio"] = hoy
    return datos


def agregar_mensaje_historial(datos, rol, texto):
    """
    Guarda lo que tú dices ('usuario') y lo que responde la IA ('tutor').
    """
    datos["historial_chat"].append({
        "rol": rol,
        "texto": texto,
        "hora": datetime.now().strftime("%H:%M")
    })
    if len(datos["historial_chat"]) > 20:
        datos["historial_chat"] = datos["historial_chat"][-20:]
    return datos

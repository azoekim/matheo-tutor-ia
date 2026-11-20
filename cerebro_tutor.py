"""
=============================================================================
FASE 1: EL CEREBRO Y LAS REGLAS DEL TUTOR (cerebro_tutor.py)
=============================================================================
¿Qué hace este archivo?
1. Define la PERSONALIDAD y REGLAS PEDAGÓGICAS de la IA (el "System Prompt").
2. Le inyecta la MEMORIA del alumno para que sepa tu nivel y tus fallos.
3. Conecta con el cerebro de IA:
   - PRIORIDAD 1: Google Gemini 2.5 Flash (con tu API Key gratuita de Google AI Studio).
   - PRIORIDAD 2: Motor Pedagógico Matemático Integrado (funciona al instante
     incluso antes de que pegues tu API Key, con la prueba de nivel de 5 preguntas,
     retos progresivos por niveles, pistas socráticas y corrección paso a paso).
=============================================================================
"""

import json
import os
import re
import urllib.request
import urllib.error
from memoria import cargar_memoria, guardar_memoria, registrar_actividad_diaria, agregar_mensaje_historial

# Plan de estudios progresivo del Nivel 1 al 10
TEMARIO_POR_NIVEL = {
    1: "Nivel 1: Aritmética básica, operaciones combinadas, jerarquía (PEMDAS) y fracciones simples",
    2: "Nivel 2: Fracciones avanzadas, porcentajes, potencias, raíces y proporcionalidad",
    3: "Nivel 3: Introducción al Álgebra, lenguaje algebraico y ecuaciones de primer grado",
    4: "Nivel 4: Sistemas de ecuaciones lineales (sustitución, igualación, reducción) y problemas reales",
    5: "Nivel 5: Ecuaciones de segundo grado (fórmula cuadrática), polinomios y factorización",
    6: "Nivel 6: Funciones (lineales, cuadráticas), geometría analítica y trigonometría básica",
    7: "Nivel 7: Trigonometría avanzada, logaritmos, exponenciales y sucesiones",
    8: "Nivel 8: Introducción al Cálculo (límites, concepto de derivada y reglas de derivación)",
    9: "Nivel 9: Aplicaciones de las derivadas, optimización e introducción a las integrales",
    10: "Nivel 10: Álgebra lineal (matrices, determinantes), probabilidad y estadística avanzada"
}

# Banco diagnóstico de 5 preguntas progresivas para detectar el nivel desde cero
PRUEBA_DIAGNOSTICO = [
    {
        "num": 1,
        "tema": "Jerarquía de operaciones (Nivel 1-2)",
        "enunciado": "Resuelve la siguiente operación combinada respetando la jerarquía de operaciones:\n\n$$3 + 4 \\times 2 - \\frac{6}{3}$$",
        "respuestas_validas": ["9", "9.0", "nueve"],
        "pista": "Recuerda la regla **PEMDAS**: primero haz la multiplicación ($4 \\times 2$) y la división ($\\frac{6}{3}$), y por último las sumas y restas de izquierda a derecha.",
        "explicacion": "$4 \\times 2 = 8$ y $\\frac{6}{3} = 2$. Entonces nos queda $3 + 8 - 2 = 9$."
    },
    {
        "num": 2,
        "tema": "Ecuaciones de primer grado (Nivel 3)",
        "enunciado": "Despeja el valor de $x$ en esta ecuación de primer grado:\n\n$$2x - 5 = 11$$",
        "respuestas_validas": ["8", "x=8", "x = 8"],
        "pista": "Pasa primero el $-5$ al lado derecho sumando ($11 + 5$), y luego divide entre $2$.",
        "explicacion": "Sumamos $5$ a ambos lados: $2x = 16$. Dividimos entre $2$: $x = \\frac{16}{2} = 8$."
    },
    {
        "num": 3,
        "tema": "Ecuaciones de segundo grado (Nivel 4-5)",
        "enunciado": "Encuentra las soluciones positivas de la ecuación cuadrática:\n\n$$x^2 - 5x + 6 = 0$$\n*(Puedes escribir las dos soluciones separadas por coma, por ejemplo: 2 y 3)*",
        "respuestas_validas": ["2 y 3", "2, 3", "3 y 2", "3, 2", "2,3", "3,2", "x=2 y x=3", "2", "3"],
        "pista": "Busca dos números que **multiplicados den $+6$** y **sumados den $+5$** (o usa la fórmula $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$).",
        "explicacion": "Factorizando $(x - 2)(x - 3) = 0$, las raíces son $x_1 = 2$ y $x_2 = 3$."
    },
    {
        "num": 4,
        "tema": "Logaritmos y Exponenciales (Nivel 6-7)",
        "enunciado": "¿Cuál es el valor de $x$ en la siguiente expresión logarítmica?\n\n$$\\log_2(x) = 4$$",
        "respuestas_validas": ["16", "x=16", "x = 16"],
        "pista": "Recuerda la definición de logaritmo: $\\log_b(x) = y$ significa que $b^y = x$. Aquí la base es $2$ y el exponente es $4$.",
        "explicacion": "Por definición, $\\log_2(x) = 4 \\iff 2^4 = x$, por tanto $x = 16$."
    },
    {
        "num": 5,
        "tema": "Introducción al Cálculo - Derivadas (Nivel 8-10)",
        "enunciado": "Calcula la derivada $f'(x)$ de la función:\n\n$$f(x) = 3x^2 + 5x - 7$$",
        "respuestas_validas": ["6x+5", "6x + 5", "f'(x)=6x+5", "6x+5"],
        "pista": "Usa la regla de la potencia: la derivada de $a \\cdot x^n$ es $a \\cdot n \\cdot x^{n-1}$, y la derivada de una constante ($-7$) es $0$.",
        "explicacion": "La derivada de $3x^2$ es $3 \\cdot 2x = 6x$, la de $5x$ es $5$, y la de $-7$ es $0$. Resultado: $f'(x) = 6x + 5$."
    }
]

# Banco de retos progresivos por nivel (del 1 al 10)
RETOS_POR_NIVEL = {
    1: {
        "enunciado": "Calcula el resultado de: $$15 - 3 \\times (2 + 2) + \\frac{10}{2}$$",
        "respuestas": ["8", "8.0"],
        "pista": "Empieza siempre por el paréntesis $(2 + 2)$, luego haz la multiplicación por $3$ y la división $\\frac{10}{2}$.",
        "explicacion": "$(2+2)=4 \\rightarrow 3 \\times 4 = 12$. Además $\\frac{10}{2}=5$. Queda $15 - 12 + 5 = 8$.",
        "tema": "Jerarquía de operaciones PEMDAS"
    },
    2: {
        "enunciado": "Calcula la suma de fracciones simplificada: $$\\frac{3}{4} + \\frac{1}{2}$$ *(Escribe el resultado como fracción, ej: 5/4, o decimal 1.25)*",
        "respuestas": ["5/4", "1.25", "1,25"],
        "pista": "Convierte $\\frac{1}{2}$ a cuartos multiplicando numerador y denominador por $2$: $\\frac{1}{2} = \\frac{2}{4}$.",
        "explicacion": "$\\frac{3}{4} + \\frac{2}{4} = \\frac{5}{4} = 1.25$.",
        "tema": "Suma de fracciones con distinto denominador"
    },
    3: {
        "enunciado": "Resuelve la ecuación de primer grado: $$3(x - 2) = 15$$",
        "respuestas": ["7", "x=7", "x = 7"],
        "pista": "Puedes dividir ambos lados entre $3$ primero ($x - 2 = 5$) o expandir el paréntesis ($3x - 6 = 15$).",
        "explicacion": "$3x - 6 = 15 \\rightarrow 3x = 21 \\rightarrow x = 7$.",
        "tema": "Ecuaciones lineales con paréntesis"
    },
    4: {
        "enunciado": "En el sistema de ecuaciones:\n$$\\begin{cases} x + y = 10 \\\\ x - y = 4 \\end{cases}$$\n¿Cuánto vale $x$?",
        "respuestas": ["7", "x=7", "x = 7"],
        "pista": "Usa el **método de reducción**: suma las dos ecuaciones hacia abajo para que $+y$ y $-y$ se cancelen ($2x = 14$).",
        "explicacion": "Sumando ambas ecuaciones: $(x+x) + (y-y) = 10+4 \\rightarrow 2x = 14 \\rightarrow x = 7$ (e $y = 3$).",
        "tema": "Sistemas de ecuaciones lineales"
    },
    5: {
        "enunciado": "Halla la solución positiva de la ecuación de segundo grado: $$x^2 - 9 = 0$$",
        "respuestas": ["3", "x=3", "x = 3", "3 y -3", "-3 y 3"],
        "pista": "Despeja $x^2 = 9$ y aplica la raíz cuadrada a ambos lados: $x = \\pm\\sqrt{9}$.",
        "explicacion": "$x^2 = 9 \\rightarrow x = \\pm 3$. La solución positiva es $x = 3$.",
        "tema": "Ecuaciones cuadráticas incompletas"
    },
    6: {
        "enunciado": "Si una recta tiene ecuación $y = 4x - 3$, ¿cuál es su **pendiente** $m$?",
        "respuestas": ["4", "m=4", "m = 4"],
        "pista": "En la ecuación explícita de la recta $y = mx + n$, la pendiente $m$ es el número que multiplica a la $x$.",
        "explicacion": "Comparando $y = 4x - 3$ con $y = mx + n$, la pendiente es $m = 4$.",
        "tema": "Funciones lineales y geometría analítica"
    },
    7: {
        "enunciado": "Resuelve la ecuación exponencial: $$3^{x+1} = 27$$",
        "respuestas": ["2", "x=2", "x = 2"],
        "pista": "Escribe $27$ como una potencia de base $3$ ($27 = 3^3$) e iguala los exponentes.",
        "explicacion": "$3^{x+1} = 3^3 \\rightarrow x + 1 = 3 \\rightarrow x = 2$.",
        "tema": "Ecuaciones exponenciales"
    },
    8: {
        "enunciado": "Calcula el límite: $$\\lim_{x \\to 2} (x^2 + 3x - 1)$$",
        "respuestas": ["9", "9.0"],
        "pista": "Como es un polinomio continuo, solo tienes que sustituir $x = 2$ directamente en la expresión.",
        "explicacion": "Sustituyendo $x=2$: $2^2 + 3(2) - 1 = 4 + 6 - 1 = 9$.",
        "tema": "Cálculo de límites"
    },
    9: {
        "enunciado": "Calcula la integral indefinida de $f(x) = 2x$ (sin escribir la constante $+C$):",
        "respuestas": ["x^2", "x²"],
        "pista": "¿Qué función al derivarla nos da $2x$? Recuerda que $\\int x^n dx = \\frac{x^{n+1}}{n+1}$.",
        "explicacion": "$\\int 2x\\,dx = 2 \\cdot \\frac{x^2}{2} = x^2 + C$.",
        "tema": "Integrales inmediatas"
    },
    10: {
        "enunciado": "Calcula el determinante de la matriz $2 \\times 2$: $$A = \\begin{pmatrix} 5 & 2 \\\\ 3 & 4 \\end{pmatrix}$$",
        "respuestas": ["14", "14.0"],
        "pista": "El determinante de $\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$ es $a \\cdot d - b \\cdot c$.",
        "explicacion": "$\\det(A) = (5 \\times 4) - (2 \\times 3) = 20 - 6 = 14$.",
        "tema": "Determinantes y matrices"
    }
}


def construir_system_prompt(datos_alumno):
    """
    El 'System Prompt' son las instrucciones secretas que la IA lee antes de
    responderte. Aquí le enseñamos a comportarse como un verdadero tutor.
    """
    estado_diagnostico = (
        "COMPLETADA" if datos_alumno["prueba_nivel_completada"]
        else f"EN CURSO (Pregunta actual: {datos_alumno['pregunta_diagnostico_actual']} de 5)"
    )

    temas_ok = ", ".join(datos_alumno["temas_dominados"]) or "Ninguno registrado aún"
    temas_mejorar = ", ".join(datos_alumno["temas_por_mejorar"]) or "Ninguno detectado aún"

    return f"""Eres 'Matheo', un tutor de matemáticas personal, cercano, paciente, motivador y muy didáctico.
Tu objetivo NO es hacerle la tarea al alumno, sino ayudarle a pensar, aprender paso a paso y superar retos progresivos.

=== FICHA ACTUAL DEL ALUMNO (MEMORIA) ===
- Nombre: {datos_alumno['nombre']}
- Prueba de nivel inicial: {estado_diagnostico}
- Nivel actual: {datos_alumno['nivel_actual']} ({TEMARIO_POR_NIVEL.get(datos_alumno['nivel_actual'], '')})
- Puntos de experiencia (XP): {datos_alumno['puntos_xp']} XP
- Retos resueltos: {datos_alumno['retos_resueltos']}
- Racha de estudio: {datos_alumno['racha_dias']} días seguidos
- Temas que ya domina: {temas_ok}
- Temas que le cuestan o debe repasar: {temas_mejorar}
- Reto activo pendiente: {datos_alumno.get('reto_activo') or 'Ninguno en este momento'}

=== TUS 5 REGLAS DE ORO COMO TUTOR ===
1. PRUEBA DE NIVEL INICIAL (Si 'Prueba de nivel inicial' está EN CURSO):
   - Hazle una prueba diagnóstica de 5 preguntas, UNA POR UNA (no las 5 de golpe).
   - Pregunta 1: Operaciones combinadas / fracciones básicas (Nivel 1-2).
   - Pregunta 2: Ecuación de primer grado o porcentajes (Nivel 3).
   - Pregunta 3: Ecuación de segundo grado o sistema de ecuaciones (Nivel 4-5).
   - Pregunta 4: Funciones, trigonometría o logaritmos (Nivel 6-7).
   - Pregunta 5: Concepto de derivada o matrices/probabilidad (Nivel 8-10).
   - Si el alumno dice "no sé hacer esto" en una pregunta de diagnóstico, anímale y tras la pregunta 5 (o si ya encontraste su techo claro) asígnale su `nuevo_nivel` real (del 1 al 10) y marca `prueba_nivel_completada: true`.

2. RETOS PROGRESIVOS:
   - Cuando el alumno pida un reto o termine uno, ponle un ejercicio adaptado a su `nivel_actual` y a sus `temas_por_mejorar`.
   - Guarda el enunciado breve del reto en el campo `reto_activo`.

3. CORRECCIÓN SOCRÁTICA (NUNCA REGALES LA RESPUESTA A LA PRIMERA):
   - Si el alumno falla un ejercicio, NO le des la solución final directamente.
   - Señala con amabilidad en qué paso estuvo el desliz y dale una pista para que lo intente de nuevo.
   - Solo si lo pide explícitamente o falla dos veces seguidas, explícalo paso a paso con total claridad.
   - Si acierta: ¡felicítale!, explica brevemente por qué su razonamiento fue bueno, súmale entre 15 y 30 puntos en `xp_ganado`, incrementa `reto_resuelto: true` y actualiza `reto_activo`.

4. FORMATO MATEMÁTICO CLARO:
   - Usa Markdown para organizar tus explicaciones (negritas, listas paso a paso).
   - Escribe las fórmulas matemáticas entre signos de dólar para que se vean bonitas, por ejemplo: $\\frac{{x + 2}}{{3}} = 5$ o $x^2 - 4x + 4 = 0$.

5. FORMATO DE RESPUESTA OBLIGATORIO (JSON PURO):
   Responde ÚNICAMENTE con un objeto JSON válido con exactamente esta estructura:
   {{
     "respuesta_tutor": "Tu mensaje completo para el alumno en Markdown y LaTeX...",
     "xp_ganado": 0,
     "reto_resuelto": false,
     "nuevo_nivel": {datos_alumno['nivel_actual']},
     "prueba_nivel_completada": {"true" if datos_alumno['prueba_nivel_completada'] else "false"},
     "pregunta_diagnostico_actual": {datos_alumno['pregunta_diagnostico_actual']},
     "reto_activo": "Enunciado corto del reto pendiente o null si no hay",
     "nuevo_tema_dominado": null,
     "nuevo_tema_por_mejorar": null,
     "consejo_del_tutor": "Un consejo corto y práctico (1 frase) basado en lo que acabáis de ver"
   }}
"""


def extraer_json_respuesta(texto):
    """
    Limpia y extrae el JSON devuelto por la IA aunque venga envuelto en bloques ```json.
    Además protege comandos LaTeX como \\frac, \\times, \\sqrt, \\beta, \\right para que
    JSON no los interprete como saltos de tabulación (\\t) o página (\\f).
    """
    texto_limpio = texto.strip()
    if texto_limpio.startswith("```"):
        texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
        texto_limpio = re.sub(r"\s*```$", "", texto_limpio)

    comandos_latex = r"(frac|times|theta|tau|text|tan|beta|binom|boxed|bar|begin|right|rho|sqrt|sum|sin|sigma|pm|pi|cdot|cos|cases|div|det|left|log|ln|lim|alpha|approx|neq|leq|geq|infty|int)"
    texto_limpio = re.sub(r"(?<!\\)\\" + comandos_latex, r"\\\\\1", texto_limpio)

    try:
        return json.loads(texto_limpio)
    except Exception:
        inicio = texto_limpio.find("{")
        fin = texto_limpio.rfind("}")
        if inicio != -1 and fin != -1 and fin > inicio:
            try:
                return json.loads(texto_limpio[inicio:fin + 1])
            except Exception:
                pass
        return {
            "respuesta_tutor": texto,
            "xp_ganado": 0,
            "reto_resuelto": False
        }


def llamar_cerebro_gemini(llave, system_prompt, historial_chat, mensaje_usuario):
    """
    Cerebro oficial de Google Gemini 2.5 Flash cuando el usuario añade su API Key.
    """
    contenidos = []
    for msg in historial_chat[-10:]:
        rol_gemini = "user" if msg["rol"] == "usuario" else "model"
        contenidos.append({
            "role": rol_gemini,
            "parts": [{"text": msg["texto"]}]
        })
    contenidos.append({
        "role": "user",
        "parts": [{"text": mensaje_usuario}]
    })

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={llave}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contenidos,
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as respuesta:
        resultado_raw = json.loads(respuesta.read().decode("utf-8"))
        texto_ia = resultado_raw["candidates"][0]["content"]["parts"][0]["text"]
        return extraer_json_respuesta(texto_ia)


def motor_pedagogico_integrado(datos, mensaje_usuario):
    """
    Motor Matemático Socrático Integrado (100% autónomo y sin límites).
    Actúa automáticamente cuando el usuario aún no ha introducido su API Key de Gemini.
    Gestiona:
    - La prueba de diagnóstico inicial de 5 niveles paso a paso.
    - Retos progresivos del Nivel 1 al 10.
    - Pistas socráticas sin regalar la respuesta.
    - Explicaciones teóricas y consejos personalizados.
    """
    msg = mensaje_usuario.lower().strip()
    nivel = datos.get("nivel_actual", 1)
    en_diagnostico = not datos.get("prueba_nivel_completada", False)
    idx_diag = datos.get("pregunta_diagnostico_actual", 0)

    # 1. ¿El alumno pide iniciar o está en la prueba de nivel?
    if "prueba de nivel" in msg or (en_diagnostico and idx_diag == 0):
        q = PRUEBA_DIAGNOSTICO[0]
        return {
            "respuesta_tutor": (
                f"¡Genial, **{datos['nombre']}**! Vamos a descubrir tu nivel con **5 preguntas rápidas** de menos a más.\n\n"
                f"Si alguna no la sabes, escribe *\"no lo sé\"* o pide una *\"pista\"* sin miedo: ¡para eso es el diagnóstico!\n\n"
                f"---\n### 🧭 Pregunta 1 de 5 — *{q['tema']}*\n{q['enunciado']}"
            ),
            "xp_ganado": 0,
            "reto_resuelto": False,
            "nuevo_nivel": 1,
            "prueba_nivel_completada": False,
            "pregunta_diagnostico_actual": 1,
            "reto_activo": f"Diagnóstico 1/5: {q['tema']}",
            "consejo_del_tutor": "En operaciones combinadas, resuelve siempre multiplicaciones y divisiones antes que sumas y restas."
        }

    # 2. Si está respondiendo una pregunta del diagnóstico (1 a 5)
    if en_diagnostico and 1 <= idx_diag <= 5:
        q_actual = PRUEBA_DIAGNOSTICO[idx_diag - 1]

        if "pista" in msg or "ayuda" in msg:
            return {
                "respuesta_tutor": f"💡 **Pista para la Pregunta {idx_diag}:**\n\n{q_actual['pista']}\n\n¡Inténtalo ahora! ¿Qué resultado te da?",
                "xp_ganado": 0,
                "reto_resuelto": False,
                "nuevo_nivel": nivel,
                "prueba_nivel_completada": False,
                "pregunta_diagnostico_actual": idx_diag,
                "reto_activo": datos.get("reto_activo"),
                "consejo_del_tutor": q_actual["pista"]
            }

        no_sabe = any(fr in msg for fr in ["no se", "no sé", "no lo se", "no lo sé", "paso", "saltar", "ni idea"])
        limpio = msg.replace(" ", "")
        acerto = any(r.replace(" ", "") == limpio or r in msg for r in q_actual["respuestas_validas"])

        if not acerto and not no_sabe:
            # Corrección socrática: damos pista antes de pasar
            return {
                "respuesta_tutor": (
                    f"¡Casi! Ese no es el resultado exacto, pero no te preocupes, vamos a pensarlo juntos. 🤔\n\n"
                    f"💡 **Pista de Matheo:** {q_actual['pista']}\n\n"
                    f"*(Inténtalo una vez más, o escribe **\"no lo sé\"** si prefieres que te lo explique y pasemos a la siguiente pregunta)*."
                ),
                "xp_ganado": 0,
                "reto_resuelto": False,
                "nuevo_nivel": nivel,
                "prueba_nivel_completada": False,
                "pregunta_diagnostico_actual": idx_diag,
                "reto_activo": datos.get("reto_activo"),
                "nuevo_tema_por_mejorar": q_actual["tema"],
                "consejo_del_tutor": "Equivocarse es la mejor pista para saber qué paso revisar."
            }

        # Si acertó o dijo "no lo sé", avanzamos a la siguiente pregunta o terminamos diagnóstico
        feedback = (
            f"✅ **¡Correcto! (+20 XP)** Muy bien resuelto: {q_actual['explicacion']}\n\n"
            if acerto else
            f"¡No pasa nada! Para eso sirve esta prueba. Mira cómo se hacía:\n> {q_actual['explicacion']}\n\n"
        )
        xp_sumar = 20 if acerto else 5
        nuevo_niv = min(10, max(1, idx_diag * 2 - (0 if acerto else 1)))

        if idx_diag < 5 and (acerto or idx_diag < 3):
            q_sig = PRUEBA_DIAGNOSTICO[idx_diag]
            return {
                "respuesta_tutor": (
                    f"{feedback}---\n### 🧭 Pregunta {idx_diag + 1} de 5 — *{q_sig['tema']}*\n{q_sig['enunciado']}"
                ),
                "xp_ganado": xp_sumar,
                "reto_resuelto": acerto,
                "nuevo_nivel": nuevo_niv,
                "prueba_nivel_completada": False,
                "pregunta_diagnostico_actual": idx_diag + 1,
                "reto_activo": f"Diagnóstico {idx_diag + 1}/5: {q_sig['tema']}",
                "nuevo_tema_dominado": q_actual["tema"] if acerto else None,
                "nuevo_tema_por_mejorar": None if acerto else q_actual["tema"],
                "consejo_del_tutor": "Avanzas genial en el diagnóstico. ¡Vamos con la siguiente!"
            }
        else:
            # Fin de la prueba de nivel
            nivel_asignado = max(1, (idx_diag * 2) if acerto else max(1, (idx_diag - 1) * 2))
            reto_inicial = RETOS_POR_NIVEL.get(nivel_asignado, RETOS_POR_NIVEL[1])
            return {
                "respuesta_tutor": (
                    f"{feedback}🎉 **¡Prueba de Nivel Completada!**\n\n"
                    f"He analizado tus respuestas y tu punto de partida ideal es el **{TEMARIO_POR_NIVEL[nivel_asignado]}**.\n\n"
                    f"---\n### 🎯 Tu Primer Reto de Nivel {nivel_asignado}:\n{reto_inicial['enunciado']}"
                ),
                "xp_ganado": xp_sumar + 30,
                "reto_resuelto": True,
                "nuevo_nivel": nivel_asignado,
                "prueba_nivel_completada": True,
                "pregunta_diagnostico_actual": 5,
                "reto_activo": reto_inicial["enunciado"],
                "nuevo_tema_dominado": q_actual["tema"] if acerto else None,
                "nuevo_tema_por_mejorar": None if acerto else q_actual["tema"],
                "consejo_del_tutor": f"Has sido asignado al Nivel {nivel_asignado}. ¡Supera retos para subir hasta el Nivel 10!"
            }

    # 3. Fuera del diagnóstico: Retos, Pistas, Teoría y Consejos por nivel
    reto_actual = RETOS_POR_NIVEL.get(nivel, RETOS_POR_NIVEL[1])

    if "pista" in msg or "ayuda" in msg:
        return {
            "respuesta_tutor": f"💡 **Pista Socrática (Nivel {nivel}):**\n\n{reto_actual['pista']}\n\n¿Cómo quedaría el siguiente paso?",
            "xp_ganado": 0,
            "reto_resuelto": False,
            "nuevo_nivel": nivel,
            "prueba_nivel_completada": True,
            "pregunta_diagnostico_actual": 5,
            "reto_activo": reto_actual["enunciado"],
            "consejo_del_tutor": reto_actual["pista"]
        }

    if "teoría" in msg or "teoria" in msg or "explic" in msg:
        return {
            "respuesta_tutor": (
                f"📖 **Explicación Paso a Paso — {TEMARIO_POR_NIVEL[nivel]}**\n\n"
                f"En este nivel trabajamos **{reto_actual['tema']}**.\n\n"
                f"* **Idea clave:** {reto_actual['pista']}\n"
                f"* **Ejemplo aplicado a tu reto actual:**\n{reto_actual['enunciado']}\n\n"
                f"¡Anímate a escribir el resultado para ganar **+25 XP**!"
            ),
            "xp_ganado": 5,
            "reto_resuelto": False,
            "nuevo_nivel": nivel,
            "prueba_nivel_completada": True,
            "pregunta_diagnostico_actual": 5,
            "reto_activo": reto_actual["enunciado"],
            "consejo_del_tutor": f"Dominar {reto_actual['tema']} te abrirá las puertas al Nivel {min(10, nivel + 1)}."
        }

    if "consejo" in msg:
        mejorar = ", ".join(datos.get("temas_por_mejorar", [])) or reto_actual["tema"]
        return {
            "respuesta_tutor": (
                f"🧠 **Consejo Personalizado de Matheo para {datos['nombre']}:**\n\n"
                f"1. Estás en el **Nivel {nivel}/10** con **{datos['puntos_xp']} XP** y una racha de **{datos['racha_dias']} días**.\n"
                f"2. Te recomiendo centrarte hoy en: **{mejorar}**.\n"
                f"3. Antes de calcular rápido, escribe cada paso en una línea distinta para evitar errores de signos.\n\n"
                f"🎯 **Tu reto activo es:**\n{reto_actual['enunciado']}"
            ),
            "xp_ganado": 0,
            "reto_resuelto": False,
            "nuevo_nivel": nivel,
            "prueba_nivel_completada": True,
            "pregunta_diagnostico_actual": 5,
            "reto_activo": reto_actual["enunciado"],
            "consejo_del_tutor": f"Dedica 10 minutos diarios a {mejorar} para consolidar tu base."
        }

    if "reto" in msg:
        return {
            "respuesta_tutor": (
                f"🎯 **¡Nuevo Reto Matemático (Nivel {nivel})!**\n"
                f"*Tema: {reto_actual['tema']}*\n\n"
                f"{reto_actual['enunciado']}\n\n"
                f"Escribe tu respuesta o pídeme una **pista** si te atascas."
            ),
            "xp_ganado": 0,
            "reto_resuelto": False,
            "nuevo_nivel": nivel,
            "prueba_nivel_completada": True,
            "pregunta_diagnostico_actual": 5,
            "reto_activo": reto_actual["enunciado"],
            "consejo_del_tutor": reto_actual["pista"]
        }

    # Comprobamos si el alumno está respondiendo al reto del nivel actual
    limpio = msg.replace(" ", "")
    acerto = any(r.replace(" ", "") == limpio or r in msg for r in reto_actual["respuestas"])
    if acerto:
        sig_nivel = min(10, nivel + 1)
        reto_sig = RETOS_POR_NIVEL.get(sig_nivel, RETOS_POR_NIVEL[10])
        return {
            "respuesta_tutor": (
                f"🌟 **¡Excelente, {datos['nombre']}! Respuesta correcta (+30 XP).**\n\n"
                f"✅ **Explicación:** {reto_actual['explicacion']}\n\n"
                f"Has demostrado dominar **{reto_actual['tema']}** y subes al **Nivel {sig_nivel}**.\n\n"
                f"---\n### 🎯 Siguiente Reto (Nivel {sig_nivel} — {reto_sig['tema']}):\n{reto_sig['enunciado']}"
            ),
            "xp_ganado": 30,
            "reto_resuelto": True,
            "nuevo_nivel": sig_nivel,
            "prueba_nivel_completada": True,
            "pregunta_diagnostico_actual": 5,
            "reto_activo": reto_sig["enunciado"],
            "nuevo_tema_dominado": reto_actual["tema"],
            "consejo_del_tutor": f"¡Felicidades por alcanzar el Nivel {sig_nivel}!"
        }

    # Si dio una respuesta incorrecta o hizo una pregunta general
    return {
        "respuesta_tutor": (
            f"🤔 Vamos a revisar tu respuesta para el reto de **{reto_actual['tema']}**:\n\n"
            f"{reto_actual['enunciado']}\n\n"
            f"💡 **Pista de Matheo (sin darte aún el resultado final):**\n{reto_actual['pista']}\n\n"
            f"¡Vuelve a intentarlo con esta pista! *(Nota: si quieres conversar sobre cualquier otro problema libre, puedes pegar tu API Key gratuita de Google Gemini en el panel izquierdo)*."
        ),
        "xp_ganado": 0,
        "reto_resuelto": False,
        "nuevo_nivel": nivel,
        "prueba_nivel_completada": True,
        "pregunta_diagnostico_actual": 5,
        "reto_activo": reto_actual["enunciado"],
        "nuevo_tema_por_mejorar": reto_actual["tema"],
        "consejo_del_tutor": reto_actual["pista"]
    }


def consultar_ia(mensaje_usuario, api_key=None):
    """
    Envía el mensaje del alumno junto con su memoria y el System Prompt a Google Gemini
    (si hay API Key) o al Motor Pedagógico Matemático Integrado (si no hay API Key),
    procesa la respuesta y actualiza automáticamente la ficha del alumno.
    """
    datos = cargar_memoria()
    llave = (api_key or os.environ.get("GEMINI_API_KEY", "")).strip()

    datos = registrar_actividad_diaria(datos)
    system_prompt = construir_system_prompt(datos)
    historial = datos.get("historial_chat", [])

    if llave:
        try:
            datos_respuesta = llamar_cerebro_gemini(llave, system_prompt, historial, mensaje_usuario)
        except Exception:
            datos_respuesta = motor_pedagogico_integrado(datos, mensaje_usuario)
    else:
        datos_respuesta = motor_pedagogico_integrado(datos, mensaje_usuario)

    # Extraemos la respuesta y actualizamos la memoria del alumno
    mensaje_tutor = datos_respuesta.get("respuesta_tutor", "¡Hola! ¿En qué trabajamos hoy?")
    xp_ganado = int(datos_respuesta.get("xp_ganado") or 0)
    datos["puntos_xp"] = datos.get("puntos_xp", 0) + xp_ganado

    if datos_respuesta.get("reto_resuelto"):
        datos["retos_resueltos"] = datos.get("retos_resueltos", 0) + 1

    nuevo_nivel = datos_respuesta.get("nuevo_nivel")
    if isinstance(nuevo_nivel, int) and 1 <= nuevo_nivel <= 10:
        datos["nivel_actual"] = nuevo_nivel

    if datos.get("prueba_nivel_completada") and datos["puntos_xp"] >= datos["nivel_actual"] * 100:
        if datos["nivel_actual"] < 10:
            datos["nivel_actual"] += 1

    datos["titulo_nivel"] = TEMARIO_POR_NIVEL.get(datos["nivel_actual"], f"Nivel {datos['nivel_actual']}")

    if "prueba_nivel_completada" in datos_respuesta:
        datos["prueba_nivel_completada"] = bool(datos_respuesta["prueba_nivel_completada"])

    if "pregunta_diagnostico_actual" in datos_respuesta and datos_respuesta["pregunta_diagnostico_actual"] is not None:
        try:
            datos["pregunta_diagnostico_actual"] = int(datos_respuesta["pregunta_diagnostico_actual"])
        except Exception:
            pass

    if "reto_activo" in datos_respuesta:
        datos["reto_activo"] = datos_respuesta["reto_activo"]

    tema_ok = datos_respuesta.get("nuevo_tema_dominado")
    if tema_ok and tema_ok not in datos["temas_dominados"]:
        datos["temas_dominados"].append(tema_ok)
        if tema_ok in datos["temas_por_mejorar"]:
            datos["temas_por_mejorar"].remove(tema_ok)

    tema_mejorar = datos_respuesta.get("nuevo_tema_por_mejorar")
    if tema_mejorar and tema_mejorar not in datos["temas_por_mejorar"]:
        datos["temas_por_mejorar"].append(tema_mejorar)

    if datos_respuesta.get("consejo_del_tutor"):
        datos["ultimo_consejo"] = datos_respuesta["consejo_del_tutor"]

    datos = agregar_mensaje_historial(datos, "usuario", mensaje_usuario)
    datos = agregar_mensaje_historial(datos, "tutor", mensaje_tutor)
    guardar_memoria(datos)

    return {
        "error": False,
        "mensaje": mensaje_tutor,
        "xp_ganado": xp_ganado,
        "datos_alumno": datos
    }

#!/usr/bin/env python3
"""
Folleto institucional (2 páginas) que va ANTES de la lista de precios.
Pensado como carta de presentación para nuevos clientes, con foco en la
remisión y gestión 100% digital mediante la app propia del laboratorio.

>>> TODO EL TEXTO ES EDITABLE ACÁ ABAJO <<<
Cambiá las frases del diccionario FOLLETO a gusto; el diseño se reacomoda solo.
"""

FONT = "DejaVu"
DISPLAY = "Poppins"

# Paleta (misma que generar_pdf)
TEAL       = (0, 120, 144)
TEAL_OSC   = (0, 96, 120)
TEAL_SUAVE = (224, 240, 242)
AZUL       = (48, 168, 240)
NARANJA    = (240, 120, 0)
GRIS_TXT   = (70, 78, 82)
GRIS_SUAVE = (140, 148, 152)
BLANCO     = (255, 255, 255)

# ------------------------------------------------------------------ #
#  TEXTO DEL FOLLETO — editá libremente
# ------------------------------------------------------------------ #
FOLLETO = {
    # Portada
    # Lo que manda en la tapa. Es una afirmación de identidad, no una promesa.
    "titular": "Otra forma|de hacer laboratorio",   # el "|" marca el quiebre
    "bajada": "Catálogo de servicios",
    "sello": "Remisión y gestión 100% digital",

    # Página 2 — bloque destacado (la app)
    "app_titulo": "Trabajamos 100% digital",
    "app_bajada": "Con nuestra app propia olvidate del papel: cargás los protocolos, "
                  "hacés el seguimiento de cada muestra y recibís los resultados online, "
                  "todo desde un mismo lugar.",
    "app_bullets": [
        "Remisión digital de protocolos, sin planillas ni papeles",
        "Seguimiento del estado de cada muestra en tiempo real",
        "Resultados e historial siempre disponibles, al instante",
    ],

    # Página 2 — grilla de diferenciales (ícono, título, texto)
    "diferenciales_titulo": "¿Por qué elegir DimeroLab?",
    "diferenciales": [
        ("➜", "Remisión digital", "Cargás tus protocolos desde la app, en minutos y sin errores de transcripción."),
        ("✔", "Resultados online", "Accedés a los informes apenas están listos, desde cualquier dispositivo."),
        ("◆", "Gestión integral", "Seguí el estado de tus muestras y consultá el historial cuando lo necesites."),
        ("✚", "Menú completo", "Hematología, bioquímica, endocrino, PCR, histopatología y cultivos."),
        ("★", "Asesoramiento", "Nuestro equipo te acompaña en la interpretación de cada resultado."),
        ("●", "Logística de muestras", "Coordinamos el retiro para que enviar tus muestras sea simple."),
    ],

    # Cierre
    "cierre": "Sumate a las clínicas que ya trabajan con nosotros.",
}


def _pill(pdf, x, y, texto, w, h=8, fill=NARANJA, fg=BLANCO, size=10):
    pdf.set_fill_color(*fill)
    pdf.set_text_color(*fg)
    pdf.set_font(FONT, "B", size)
    pdf.set_xy(x, y)
    pdf.cell(w, h, texto, align="C", fill=True)


def _circulo(pdf, cx, cy, d, color):
    pdf.set_fill_color(*color)
    pdf.ellipse(cx - d / 2, cy - d / 2, d, d, style="F")


def portada(pdf, cfg, areas=None):
    """Página 1: portada institucional.
    `areas` llega desde el catálogo real, así la portada nunca queda desfasada."""
    pdf.add_page()
    W = 210

    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, W, 5, style="F")
    _circulo(pdf, 176, 30, 16, TEAL_SUAVE)
    _circulo(pdf, 190, 22, 10, TEAL_SUAVE)
    _circulo(pdf, 184, 40, 7, (214, 234, 246))

    if pdf.logo.exists():
        lw = 108
        pdf.image(str(pdf.logo), x=(W - lw) / 2, y=52, w=lw)

    # el eslogan manda, en dos tiempos: el quiebre es parte del diseño
    partes = FOLLETO["titular"].split("|")
    if len(partes) == 2:
        pdf.set_xy(18, 92); pdf.set_font(DISPLAY, "B", 32); pdf.set_text_color(*TEAL_OSC)
        pdf.multi_cell(W - 36, 14, partes[0].strip(), align="C")
        pdf.set_xy(18, pdf.get_y() + 1); pdf.set_font(DISPLAY, "", 23)
        pdf.set_text_color(*TEAL)
        pdf.multi_cell(W - 36, 11, partes[1].strip(), align="C")
    else:
        pdf.set_xy(18, 94); pdf.set_font(FONT, "B", 30); pdf.set_text_color(*TEAL_OSC)
        pdf.multi_cell(W - 36, 14, FOLLETO["titular"], align="C")

    # qué es este documento (dato menor)
    pdf.set_xy(20, pdf.get_y() + 7); pdf.set_font(DISPLAY, "B", 11)
    pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(W - 40, 6, FOLLETO["bajada"], align="C")
    vig = cfg.get("vigencia", "")
    if vig:
        pdf.set_xy(20, pdf.get_y() + 0.5); pdf.set_font(FONT, "", 9.5)
        pdf.set_text_color(*GRIS_SUAVE)
        pdf.multi_cell(W - 40, 5, f"{cfg.get('subtitulo','')} · Vigencia {vig}", align="C")

    # sello
    sello = FOLLETO["sello"]
    pdf.set_font(FONT, "B", 11)
    sw = pdf.get_string_width(sello) + 16
    _pill(pdf, (W - sw) / 2, pdf.get_y() + 9, sello, sw, h=9, fill=NARANJA, size=11)

    # dato de amplitud (sale de los datos, nunca queda desfasado)
    if areas:
        y = pdf.get_y() + 18
        pdf.set_xy(20, y); pdf.set_font(FONT, "B", 10.5); pdf.set_text_color(*TEAL_OSC)
        pdf.cell(W - 40, 5, areas, align="C")

    # franja de contacto abajo
    y_band = 262
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, y_band, W, 35, style="F")
    pdf.set_text_color(*BLANCO)
    pdf.set_font(FONT, "B", 12)
    pdf.set_xy(0, y_band + 7)
    pdf.cell(W, 6, str(cfg.get("tagline", "Laboratorio Veterinario")), align="C")
    pdf.set_font(FONT, "", 10)
    pdf.set_xy(0, y_band + 15)
    datos = "     ".join([
        "☎ WhatsApp " + str(cfg.get("whatsapp", "")),
        str(cfg.get("web", "")),
        str(cfg.get("instagram", "")),
    ])
    pdf.cell(W, 6, datos, align="C")
    pdf.set_font(FONT, "I", 8.5)
    pdf.set_xy(0, y_band + 24)
    pdf.set_text_color(*TEAL_SUAVE)
    vig = cfg.get("vigencia", "")
    pdf.cell(W, 5, f"Lista de precios vigente · {vig}" if vig else "", align="C")


def diferenciales(pdf, cfg):
    """Página 2: bloque de la app + grilla de diferenciales."""
    pdf.add_page()
    W = 210
    ML = 16
    ancho = W - 2 * ML

    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, W, 5, style="F")

    # ---- bloque destacado: la app ----
    y = 20
    h_app = 62
    pdf.set_fill_color(*TEAL)
    pdf.rect(ML, y, ancho, h_app, style="F")
    # borde acento naranja a la izquierda
    pdf.set_fill_color(*NARANJA)
    pdf.rect(ML, y, 3, h_app, style="F")

    pdf.set_xy(ML + 10, y + 7)
    pdf.set_font(FONT, "B", 18)
    pdf.set_text_color(*BLANCO)
    pdf.cell(ancho - 20, 9, FOLLETO["app_titulo"])
    pdf.set_xy(ML + 10, y + 18)
    pdf.set_font(FONT, "", 10.5)
    pdf.set_text_color(*TEAL_SUAVE)
    pdf.multi_cell(ancho - 20, 5.4, FOLLETO["app_bajada"], align="L")
    yb = pdf.get_y() + 2
    pdf.set_font(FONT, "", 10)
    for b in FOLLETO["app_bullets"]:
        pdf.set_xy(ML + 10, yb)
        pdf.set_text_color(*NARANJA)
        pdf.cell(6, 5.2, "✔")
        pdf.set_text_color(*BLANCO)
        pdf.multi_cell(ancho - 30, 5.2, b, align="L")
        yb = pdf.get_y() + 0.6

    # ---- título grilla ----
    pdf.set_xy(ML, y + h_app + 8)
    pdf.set_font(FONT, "B", 15)
    pdf.set_text_color(*TEAL_OSC)
    pdf.cell(ancho, 8, FOLLETO["diferenciales_titulo"])

    # ---- grilla 2 columnas x 3 filas ----
    items = FOLLETO["diferenciales"]
    col_w = (ancho - 8) / 2
    x0 = ML
    y0 = y + h_app + 20
    card_h = 34
    colores = [TEAL, AZUL, NARANJA]
    for i, (icono, titulo, texto) in enumerate(items):
        col = i % 2
        fila = i // 2
        cx = x0 + col * (col_w + 8)
        cy = y0 + fila * (card_h + 5)
        # tarjeta
        pdf.set_draw_color(*TEAL_SUAVE)
        pdf.set_line_width(0.3)
        pdf.rect(cx, cy, col_w, card_h, style="D")
        # chip de ícono
        color = colores[i % len(colores)]
        pdf.set_fill_color(*color)
        pdf.rect(cx + 5, cy + 6, 11, 11, style="F", round_corners=True, corner_radius=2)
        pdf.set_xy(cx + 5, cy + 6.6)
        pdf.set_font(FONT, "B", 12)
        pdf.set_text_color(*BLANCO)
        pdf.cell(11, 10, icono, align="C")
        # título + texto
        pdf.set_xy(cx + 20, cy + 5.5)
        pdf.set_font(FONT, "B", 11)
        pdf.set_text_color(*TEAL_OSC)
        pdf.cell(col_w - 24, 6, titulo)
        pdf.set_xy(cx + 20, cy + 12)
        pdf.set_font(FONT, "", 8.6)
        pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(col_w - 24, 4.1, texto, align="L")

    # ---- cierre / CTA ----
    yc = y0 + 3 * (card_h + 5) + 3
    pdf.set_fill_color(*TEAL_SUAVE)
    pdf.rect(ML, yc, ancho, 16, style="F")
    pdf.set_xy(ML, yc + 3)
    pdf.set_font(FONT, "B", 11)
    pdf.set_text_color(*TEAL_OSC)
    pdf.cell(ancho, 5, FOLLETO["cierre"], align="C")
    pdf.set_xy(ML, yc + 9)
    pdf.set_font(FONT, "", 9.5)
    pdf.set_text_color(*GRIS_TXT)
    pdf.cell(ancho, 5, f"Escribinos por WhatsApp {cfg.get('whatsapp','')}  ·  {cfg.get('web','')}", align="C")


def agregar_folleto(pdf, cfg, areas=None):
    """Agrega las páginas del folleto y deja el chrome listo para la lista."""
    pdf.set_auto_page_break(auto=False)  # el folleto se dibuja a mano, sin saltos
    portada(pdf, cfg, areas)
    # La página de diferenciales se retiró: quedó reemplazada por
    # 'El camino de tu muestra', que cuenta lo mismo con hechos concretos.
    # Para recuperarla, descomentar la línea siguiente y poner folleto_pages=2.
    # diferenciales(pdf, cfg)
    pdf.set_auto_page_break(auto=True, margin=18)  # vuelve el flujo normal para la lista
    # (el encabezado/pie de la lista se controla con pdf.folleto_pages en construir_pdf)

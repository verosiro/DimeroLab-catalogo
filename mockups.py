#!/usr/bin/env python3
"""
Mockups de 2 conceptos estéticos DISTINTOS (nada que ver con Diagnotest),
para que la usuaria elija dirección. Cada uno renderiza una muestra con
perfiles + estudios individuales reales.

Idea propia de identidad: PUNTOS DE COLOR = tubo de muestra.
"""
from pathlib import Path
from fpdf import FPDF

BASE = Path(__file__).parent
ASSETS = BASE / "assets"
FONT = "DejaVu"

TEAL     = (0, 120, 144)
TEAL_OSC = (0, 96, 120)
TEAL_SUAVE = (224, 240, 242)
TEAL_XSUAVE = (242, 249, 250)
AZUL     = (48, 168, 240)
NARANJA  = (240, 120, 0)
GRIS_TXT = (70, 78, 82)
GRIS_SUAVE = (150, 158, 162)
BLANCO   = (255, 255, 255)

# color de tubo -> (etiqueta, color)
TUBOS = [
    ("edta",     ("EDTA",     (123, 79, 163))),   # violeta
    ("violeta",  ("EDTA",     (123, 79, 163))),
    ("seco",     ("Seco/con gel", (214, 72, 74))),     # rojo (suero)
    ("rojo",     ("Seco/con gel", (214, 72, 74))),
    ("citrato",  ("Citrato",  (77, 182, 230))),    # celeste
    ("celeste",  ("Citrato",  (77, 182, 230))),
    ("glucemia", ("Glucemia", (120, 126, 131))),   # gris (tapa gris)
    ("naranja",  ("Glucemia", (120, 126, 131))),
    ("gris",     ("Glucemia", (120, 126, 131))),
    ("orina",    ("Orina",    (232, 185, 58))),     # amarillo
    ("formol",   ("Formol",   (176, 181, 186))),    # gris claro
    ("frotis",   ("Frotis",   (214, 72, 74))),
    ("materia",  ("M. fecal", (150, 120, 80))),
]


def tubos_de(muestra):
    m = (muestra or "").lower()
    vistos, out = set(), []
    for key, (label, color) in TUBOS:
        if key in m and label not in vistos:
            vistos.add(label)
            out.append((label, color))
    return out


def determinaciones(desc):
    items = [x.strip().lstrip("•").strip() for x in str(desc).split("\n")]
    return [x for x in items if x]


def base_pdf():
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_font(FONT, "", str(ASSETS / "DejaVuSans.ttf"))
    pdf.add_font(FONT, "B", str(ASSETS / "DejaVuSans-Bold.ttf"))
    pdf.add_font(FONT, "I", str(ASSETS / "DejaVuSans-Oblique.ttf"))
    pdf.add_page()
    return pdf


def money(v):
    return "$" + f"{int(v):,}".replace(",", ".")


def valor(v):
    """Precio sin símbolo ni decimales (estilo discreto)."""
    return f"{int(v):,}".replace(",", ".")


# datos de ejemplo
PERFILES = [
    ("Perfil general", 14580, "Tubo con EDTA (Violeta) + Tubo seco (Rojo) + Tubo glucemia (Naranja/Gris)",
     "• Hemograma completo\n• Urea\n• Creatinina\n• Proteínas totales\n• Albúmina\n• Globulinas\n• Relación A/G\n• GPT\n• GOT\n• FAS\n• Glucemia"),
    ("Perfil hepático", 17040, "Tubo con EDTA (Violeta) + Tubo seco (Rojo) + Tubo glucemia (Naranja/Gris)",
     "• Hemograma completo\n• Urea\n• Creatinina\n• Proteínas totales\n• Albúmina\n• GPT\n• GOT\n• GGT\n• FAS\n• Glucemia\n• Bilirrubinas\n• Colesterol total\n• Fósforo"),
    ("Perfil renal simple", 16300, "Tubo con EDTA (Violeta) + Tubo seco (Rojo)",
     "• Hemograma completo\n• Urea\n• Creatinina\n• Albúmina\n• Fósforo\n• Calcio total\n• Glucemia\n• Ionograma"),
]
INDIVIDUALES = [
    ("Hemograma completo", 7840, "Tubo con EDTA (Violeta)", "24 hs"),
    ("Glucemia", 1750, "Tubo seco (Rojo)", "24 hs"),
    ("Colesterol total", 1750, "Tubo seco (Rojo)", "24 hs"),
    ("Coagulograma (TP, KPTT)", 10880, "Tubo con citrato (Celeste)", "48 hs"),
    ("T4 Total", 8530, "Tubo seco (Rojo)", "5 días"),
]


def puntos_tubo(pdf, x, y, muestra, r=1.5, gap=4.2, con_texto=False):
    """Dibuja los puntos de color de tubo. Devuelve el ancho usado."""
    tl = tubos_de(muestra)
    cx = x
    for label, color in tl:
        pdf.set_fill_color(*color)
        pdf.ellipse(cx, y, r * 2, r * 2, style="F")
        if con_texto:
            pdf.set_font(FONT, "", 6.5)
            pdf.set_text_color(*GRIS_SUAVE)
            pdf.set_xy(cx + r * 2 + 0.8, y - 0.6)
            w = pdf.get_string_width(label) + 3
            pdf.cell(w, 3.5, label)
            cx += r * 2 + 1 + w
        else:
            cx += gap
    return cx - x


# ============================================================= #
#  CONCEPTO A — Editorial limpio (sin cajas, tipográfico, aireado)
# ============================================================= #
def concepto_a():
    pdf = base_pdf()
    W, ML, MR = 210, 18, 192
    ancho = MR - ML
    # rótulo del concepto
    pdf.set_xy(ML, 12); pdf.set_font(FONT, "I", 8); pdf.set_text_color(*NARANJA)
    pdf.cell(ancho, 4, "CONCEPTO A · Editorial", align="R")

    # encabezado de sección (dots molécula + texto + hairline)
    y = 20
    pdf.set_fill_color(*TEAL); pdf.ellipse(ML, y + 1.5, 3, 3, style="F")
    pdf.set_fill_color(*AZUL); pdf.ellipse(ML + 3.4, y + 1.5, 3, 3, style="F")
    pdf.set_fill_color(*NARANJA); pdf.ellipse(ML + 6.8, y + 1.5, 3, 3, style="F")
    pdf.set_xy(ML + 13, y - 1.5); pdf.set_font(FONT, "B", 17); pdf.set_text_color(*TEAL_OSC)
    pdf.cell(100, 8, "Perfiles")
    pdf.set_draw_color(*TEAL_SUAVE); pdf.set_line_width(0.5)
    pdf.line(ML, y + 9, MR, y + 9)
    y += 15

    for nombre, precio, muestra, desc in PERFILES:
        dets = determinaciones(desc)
        # nombre
        pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 12.5); pdf.set_text_color(*TEAL_OSC)
        pdf.cell(ancho - 40, 6, nombre)
        # precio grande, aireado, a la derecha (tipografía, sin caja)
        pdf.set_xy(MR - 40, y - 1); pdf.set_font(FONT, "B", 19); pdf.set_text_color(*TEAL)
        pdf.cell(40, 8, money(precio), align="R")
        # determinaciones como texto fluido
        pdf.set_xy(ML, y + 7); pdf.set_font(FONT, "", 8.3); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(ancho - 42, 4.3, "  ·  ".join(dets), align="L")
        yb = pdf.get_y() + 1.5
        # puntos de tubo + remitir
        pdf.set_font(FONT, "", 7); pdf.set_text_color(*GRIS_SUAVE)
        pdf.set_xy(ML, yb - 0.3); pdf.cell(14, 3.5, "Remitir")
        puntos_tubo(pdf, ML + 15, yb + 0.3, muestra, con_texto=True)
        y = yb + 6
        pdf.set_draw_color(*TEAL_SUAVE); pdf.set_line_width(0.2)
        pdf.line(ML, y, MR, y)
        y += 5

    # ---- estudios individuales ----
    y += 3
    pdf.set_fill_color(*TEAL); pdf.ellipse(ML, y + 1.5, 3, 3, style="F")
    pdf.set_fill_color(*AZUL); pdf.ellipse(ML + 3.4, y + 1.5, 3, 3, style="F")
    pdf.set_fill_color(*NARANJA); pdf.ellipse(ML + 6.8, y + 1.5, 3, 3, style="F")
    pdf.set_xy(ML + 13, y - 1.5); pdf.set_font(FONT, "B", 17); pdf.set_text_color(*TEAL_OSC)
    pdf.cell(100, 8, "Estudios individuales")
    pdf.set_draw_color(*TEAL_SUAVE); pdf.set_line_width(0.5); pdf.line(ML, y + 9, MR, y + 9)
    y += 14

    # encabezados de columna
    pdf.set_font(FONT, "B", 7.5); pdf.set_text_color(*GRIS_SUAVE)
    pdf.set_xy(ML, y); pdf.cell(95, 4, "ESTUDIO")
    pdf.set_xy(ML + 96, y); pdf.cell(45, 4, "MUESTRA")
    pdf.set_xy(ML + 140, y); pdf.cell(18, 4, "PLAZO")
    pdf.set_xy(MR - 30, y); pdf.cell(30, 4, "PRECIO", align="R")
    y += 5.5
    zebra = False
    for nombre, precio, muestra, plazo in INDIVIDUALES:
        h = 8
        if zebra:
            pdf.set_fill_color(*TEAL_XSUAVE); pdf.rect(ML - 2, y - 1, ancho + 4, h, style="F")
        zebra = not zebra
        pdf.set_xy(ML, y + 0.8); pdf.set_font(FONT, "", 9); pdf.set_text_color(*GRIS_TXT)
        pdf.cell(95, 5, nombre)
        puntos_tubo(pdf, ML + 96, y + 2, muestra, con_texto=True)
        pdf.set_xy(ML + 140, y + 0.8); pdf.set_font(FONT, "", 8); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(18, 5, plazo)
        pdf.set_xy(MR - 34, y + 0.4); pdf.set_font(FONT, "B", 11); pdf.set_text_color(*TEAL)
        pdf.cell(34, 5, money(precio), align="R")
        y += h

    pdf.output(str(BASE / "mockup_A.pdf"))


# ============================================================= #
#  CONCEPTO B — Fichas con espina de color + chips (soft, moderno)
# ============================================================= #
def chip_flow(pdf, x, y, w, items, chip_h=5.2):
    """Dibuja chips redondeados que envuelven. Devuelve y final."""
    cx, cy = x, y
    pdf.set_font(FONT, "", 7.5)
    for it in items:
        tw = pdf.get_string_width(it) + 5
        if cx + tw > x + w:
            cx = x; cy += chip_h + 1.6
        pdf.set_fill_color(*TEAL_SUAVE)
        pdf.rect(cx, cy, tw, chip_h, style="F", round_corners=True, corner_radius=1.6)
        pdf.set_xy(cx, cy + 0.3); pdf.set_text_color(*TEAL_OSC)
        pdf.cell(tw, chip_h - 0.6, it, align="C")
        cx += tw + 2
    return cy + chip_h


def concepto_b():
    pdf = base_pdf()
    W, ML, MR = 210, 18, 192
    ancho = MR - ML
    pdf.set_xy(ML, 12); pdf.set_font(FONT, "I", 8); pdf.set_text_color(*NARANJA)
    pdf.cell(ancho, 4, "CONCEPTO B · Fichas", align="R")

    # tab de sección
    y = 20
    pdf.set_fill_color(*TEAL)
    pdf.rect(ML, y, 42, 9, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(ML, y + 0.6); pdf.set_font(FONT, "B", 12); pdf.set_text_color(*BLANCO)
    pdf.cell(42, 8, "Perfiles", align="C")
    y += 14

    spine_colors = [TEAL, AZUL, NARANJA]
    for i, (nombre, precio, muestra, desc) in enumerate(PERFILES):
        dets = determinaciones(desc)
        # medir alto de chips
        # simulación de alto: filas de chips
        card_x, card_w = ML, ancho
        inner_x = card_x + 8
        inner_w = card_w - 12
        # alto aproximado
        pdf.set_font(FONT, "", 7.5)
        cx = inner_x; rows = 1
        for it in dets:
            tw = pdf.get_string_width(it) + 5
            if cx + tw > inner_x + inner_w:
                cx = inner_x; rows += 1
            cx += tw + 2
        h = 20 + rows * 6.8 + 6
        # tarjeta
        pdf.set_fill_color(*TEAL_XSUAVE)
        pdf.rect(card_x, y, card_w, h, style="F", round_corners=True, corner_radius=2.5)
        pdf.set_fill_color(*spine_colors[i % 3])
        pdf.rect(card_x, y, 3.5, h, style="F", round_corners=True, corner_radius=1)
        # nombre
        pdf.set_xy(inner_x, y + 4); pdf.set_font(FONT, "B", 12.5); pdf.set_text_color(*TEAL_OSC)
        pdf.cell(inner_w - 5, 6, nombre)
        # precio DEBAJO del nombre, grande, naranja, a la izquierda
        pdf.set_xy(inner_x, y + 10.5); pdf.set_font(FONT, "B", 15); pdf.set_text_color(*NARANJA)
        pdf.cell(50, 6, money(precio))
        # puntos de tubo a la derecha del precio
        puntos_tubo(pdf, inner_x + 46, y + 13.2, muestra, con_texto=True)
        # chips de determinaciones
        chip_flow(pdf, inner_x, y + 20, inner_w, dets)
        y += h + 4

    # ---- estudios individuales ----
    y += 2
    pdf.set_fill_color(*TEAL)
    pdf.rect(ML, y, 56, 9, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(ML, y + 0.6); pdf.set_font(FONT, "B", 12); pdf.set_text_color(*BLANCO)
    pdf.cell(56, 8, "Estudios individuales", align="C")
    y += 13

    for i, (nombre, precio, muestra, plazo) in enumerate(INDIVIDUALES):
        h = 9
        pdf.set_fill_color(*TEAL_XSUAVE)
        pdf.rect(ML, y, ancho, h, style="F", round_corners=True, corner_radius=1.5)
        pdf.set_fill_color(*spine_colors[i % 3])
        pdf.rect(ML, y, 2.5, h, style="F", round_corners=True, corner_radius=1)
        pdf.set_xy(ML + 6, y + 1.4); pdf.set_font(FONT, "B", 9.2); pdf.set_text_color(*TEAL_OSC)
        pdf.cell(90, 6, nombre)
        puntos_tubo(pdf, ML + 98, y + 3.2, muestra, con_texto=True)
        pdf.set_xy(ML + 134, y + 1.8); pdf.set_font(FONT, "", 7.5); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(16, 5, plazo)
        pdf.set_xy(MR - 34, y + 1.2); pdf.set_font(FONT, "B", 11); pdf.set_text_color(*NARANJA)
        pdf.cell(34, 6, money(precio), align="R")
        y += h + 2

    pdf.output(str(BASE / "mockup_B.pdf"))


# ============================================================= #
#  CONCEPTO A2 — Editorial con PRECIO DISCRETO (menu engineering)
#  Nombre protagonista · precio chico/gris en línea · sin $ · sin columna
# ============================================================= #
PRECIO_GRIS = (90, 100, 105)   # precio neutro (un punto más de peso que la 1ª versión)


def concepto_a2():
    pdf = base_pdf()
    W, ML, MR = 210, 18, 192
    ancho = MR - ML
    pdf.set_xy(ML, 12); pdf.set_font(FONT, "I", 8); pdf.set_text_color(*NARANJA)
    pdf.cell(ancho, 4, "CONCEPTO A · Editorial · precio discreto", align="R")

    # sección
    y = 20
    for j, c in enumerate([TEAL, AZUL, NARANJA]):
        pdf.set_fill_color(*c); pdf.ellipse(ML + j * 3.4, y + 1.5, 3, 3, style="F")
    pdf.set_xy(ML + 13, y - 1.5); pdf.set_font(FONT, "B", 17); pdf.set_text_color(*TEAL_OSC)
    pdf.cell(120, 8, "Perfiles")
    # aclaración de valores (una sola vez, discreta)
    pdf.set_xy(MR - 70, y + 1.5); pdf.set_font(FONT, "I", 7.5); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(70, 4, "Valores en pesos · IVA incluido", align="R")
    pdf.set_draw_color(*TEAL_SUAVE); pdf.set_line_width(0.5); pdf.line(ML, y + 9, MR, y + 9)
    y += 15

    for nombre, precio, muestra, desc in PERFILES:
        dets = determinaciones(desc)
        # nombre PROTAGONISTA
        pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 13); pdf.set_text_color(*TEAL_OSC)
        pdf.cell(pdf.get_string_width(nombre) + 2, 6, nombre)
        wn = pdf.get_string_width(nombre)
        # precio en línea, chico, gris, sin símbolo (posición variable segun nombre)
        pdf.set_xy(ML + wn + 5, y + 1.4); pdf.set_font(FONT, "", 10.5); pdf.set_text_color(*PRECIO_GRIS)
        pdf.cell(30, 4, valor(precio))
        # determinaciones fluidas
        pdf.set_xy(ML, y + 7.5); pdf.set_font(FONT, "", 8.3); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(ancho, 4.3, "  ·  ".join(dets), align="L")
        yb = pdf.get_y() + 1.5
        pdf.set_font(FONT, "", 7); pdf.set_text_color(*GRIS_SUAVE)
        pdf.set_xy(ML, yb - 0.3); pdf.cell(14, 3.5, "Remitir")
        puntos_tubo(pdf, ML + 15, yb + 0.3, muestra, con_texto=True)
        y = yb + 6
        pdf.set_draw_color(*TEAL_SUAVE); pdf.set_line_width(0.2); pdf.line(ML, y, MR, y)
        y += 5

    # estudios individuales — una línea, precio en línea tras el nombre
    y += 3
    for j, c in enumerate([TEAL, AZUL, NARANJA]):
        pdf.set_fill_color(*c); pdf.ellipse(ML + j * 3.4, y + 1.5, 3, 3, style="F")
    pdf.set_xy(ML + 13, y - 1.5); pdf.set_font(FONT, "B", 17); pdf.set_text_color(*TEAL_OSC)
    pdf.cell(120, 8, "Estudios individuales")
    pdf.set_draw_color(*TEAL_SUAVE); pdf.set_line_width(0.5); pdf.line(ML, y + 9, MR, y + 9)
    y += 15

    for nombre, precio, muestra, plazo in INDIVIDUALES:
        # punto(s) de tubo como viñeta de inicio
        w_dots = puntos_tubo(pdf, ML, y + 1.6, muestra, con_texto=False)
        x = ML + w_dots + 3
        # nombre
        pdf.set_xy(x, y); pdf.set_font(FONT, "B", 9.5); pdf.set_text_color(*GRIS_TXT)
        pdf.cell(pdf.get_string_width(nombre) + 2, 5, nombre)
        xn = x + pdf.get_string_width(nombre)
        # precio en línea (chico, gris, sin $)
        pdf.set_xy(xn + 4, y + 0.5); pdf.set_font(FONT, "", 9.5); pdf.set_text_color(*PRECIO_GRIS)
        pdf.cell(24, 4, valor(precio))
        xp = xn + 4 + pdf.get_string_width(valor(precio))
        # plazo, aún más discreto
        pdf.set_xy(xp + 5, y + 0.9); pdf.set_font(FONT, "I", 7.3); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(24, 4, "· " + plazo)
        y += 8.5

    pdf.output(str(BASE / "mockup_A2.pdf"))


if __name__ == "__main__":
    concepto_a()
    concepto_b()
    concepto_a2()
    print("mockups generados: mockup_A.pdf, mockup_B.pdf, mockup_A2.pdf")

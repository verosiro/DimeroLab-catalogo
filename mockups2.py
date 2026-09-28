#!/usr/bin/env python3
"""
Prototipo "audaz con sistema": color por área + índice de uña + portadas de
sección + barra de composición de perfiles. Y una versión para celular.

Genera: mockup_C.pdf (A4)  y  mockup_MOBILE.pdf
"""
from pathlib import Path
import pandas as pd
from fpdf import FPDF

BASE = Path(__file__).parent
ASSETS = BASE / "assets"
FONT = "DejaVu"

BLANCO = (255, 255, 255)
GRIS_TXT = (70, 78, 82)
GRIS_SUAVE = (150, 158, 162)
PRECIO_GRIS = (90, 100, 105)
NEGRO_SUAVE = (28, 38, 44)

# ---- SISTEMA DE COLOR POR ÁREA (derivado del logo) ----
AREAS = {
    "PERFILES":                 ("Perfiles",     (0, 96, 120)),
    "Químicas de Perfiles":     ("Químicas",     (0, 140, 155)),
    "Patología":                ("Patología",    (76, 154, 90)),
    "Hematología Y Hemostasia": ("Hematología",  (123, 79, 163)),
    "Química Sanguínea":        ("Química",      (0, 120, 144)),
    "Químicas Combinables":     ("Combinables",  (14, 154, 174)),
    "Hormonas":                 ("Hormonas",     (240, 120, 0)),
    "Serología e Inmunología":  ("Serología",    (48, 140, 220)),
    "Orina":                    ("Orina",        (214, 160, 26)),
    "Materia fecal":            ("M. fecal",     (140, 110, 60)),
    "Toxicología":              ("Toxicología",  (200, 70, 110)),
    "Biología Molecular":       ("Molecular",    (170, 58, 140)),
    "Cultivos":                 ("Cultivos",     (46, 155, 143)),
    "COMBOS":                   ("Combos",       (226, 88, 30)),
}
ORDEN_TABS = list(AREAS.keys())


def color_area(seccion):
    return AREAS.get(seccion, ("", (0, 120, 144)))[1]


def label_area(seccion):
    return AREAS.get(seccion, (seccion, (0, 120, 144)))[0]


# ---- clasificador de determinaciones -> área (para la barra de composición) ----
CLASIF = [
    ("Hematología", (123, 79, 163), [
        "hemograma", "plaqueta", "reticulocito", "hemoparásito", "coagulograma",
        "protrombina", "kptt", "tipificación", "knott", "coombs", "frotis"]),
    ("Hormonas", (240, 120, 0), [
        "t4", "t3", "tsh", "cortisol", "insulina", "progesterona", "estradiol",
        "testosterona", "parathormona", "igf"]),
    ("Serología", (48, 140, 220), [
        "vif", "vilef", "ehrlichia", "anaplasma", "toxoplasmosis", "leishmania",
        "(ic)", "ifi", "brucella", "moquillo", "parvovirus", "dirofilaria"]),
    ("Orina", (214, 160, 26), [
        "orina", "proteinuria", "creatininuria", "urinario"]),
    ("Química", (0, 120, 144), []),   # por defecto
]


def area_determinacion(texto):
    t = str(texto).lower()
    for nombre, color, claves in CLASIF:
        if claves and any(k in t for k in claves):
            return nombre, color
    return CLASIF[-1][0], CLASIF[-1][1]


# ---- PESOS: cuántos parámetros informa realmente cada determinación ----
# (contados sobre el informe real; a validar con criterio clínico)
PESOS = [
    (["hemograma"], 22),
    (["orina completo", "análisis de orina", "aoc"], 15),
    (["proteinograma"], 6),
    (["ionograma"], 4),
    (["lipidograma", "lipídica", "lipidico"], 4),
    (["bilirrubina"], 3),
    (["reticulocito"], 3),
    (["coagulograma"], 2),
]


def peso_det(texto):
    t = str(texto).lower()
    for claves, p in PESOS:
        if any(k in t for k in claves):
            return p
    return 1


def composicion(dets):
    """Suma PARÁMETROS por área -> [(nombre, color, n_parametros)]."""
    conteo = {}
    for d in dets:
        n, c = area_determinacion(d)
        if n not in conteo:
            conteo[n] = [c, 0]
        conteo[n][1] += peso_det(d)
    orden = ["Hematología", "Química", "Hormonas", "Serología", "Orina"]
    return [(k, conteo[k][0], conteo[k][1]) for k in orden if k in conteo]


def total_parametros(dets):
    return sum(peso_det(d) for d in dets)


def tiene_hemograma(dets):
    return any("hemograma" in str(d).lower() for d in dets)


# ---- tubos ----
TUBOS = [("edta", ("EDTA", (123, 79, 163))), ("violeta", ("EDTA", (123, 79, 163))),
         ("seco", ("Seco/con gel", (214, 72, 74))), ("rojo", ("Seco/con gel", (214, 72, 74))),
         ("citrato", ("Citrato", (77, 182, 230))), ("celeste", ("Citrato", (77, 182, 230))),
         ("glucemia", ("Glucemia", (120, 126, 131))), ("naranja", ("Glucemia", (120, 126, 131))),
         ("orina", ("Orina", (232, 185, 58))), ("formol", ("Formol", (176, 181, 186)))]


def tubos_de(muestra):
    m = str(muestra or "").lower()
    vistos, out = [], []
    for k, (lb, col) in TUBOS:
        if k in m and lb not in vistos:
            vistos.append(lb); out.append((lb, col))
    return out


def valor(v):
    try:
        return f"{int(round(float(v))):,}".replace(",", ".")
    except (ValueError, TypeError):
        return ""


def dets_de(desc):
    return [x.strip().lstrip("•").strip() for x in str(desc).split("\n") if x.strip()]


# ------------------------------------------------------------------ #
class Proto(FPDF):
    def __init__(self, fmt="A4"):
        super().__init__(orientation="P", unit="mm", format=fmt)
        self.set_auto_page_break(auto=False)
        self.add_font(FONT, "", str(ASSETS / "DejaVuSans.ttf"))
        self.add_font(FONT, "B", str(ASSETS / "DejaVuSans-Bold.ttf"))
        self.add_font(FONT, "I", str(ASSETS / "DejaVuSans-Oblique.ttf"))
        self.seccion_actual = None


def molecula(pdf, cx, cy, escala=1.0, color=BLANCO, alpha_dots=None):
    """Motivo de puntos inspirado en el logo."""
    puntos = [(0, 0, 9), (11, -7, 6), (8, 9, 5), (-10, 6, 4), (-7, -9, 3)]
    for i, (dx, dy, r) in enumerate(puntos):
        c = color if alpha_dots is None else alpha_dots[i % len(alpha_dots)]
        pdf.set_fill_color(*c)
        d = r * escala
        pdf.ellipse(cx + dx * escala - d / 2, cy + dy * escala - d / 2, d, d, style="F")


def thumb_index(pdf, seccion_activa, W=210, top=32, bot=285):
    """Pestañas de color en el borde derecho; la activa sobresale."""
    n = len(ORDEN_TABS)
    alto = (bot - top) / n
    for i, sec in enumerate(ORDEN_TABS):
        y = top + i * alto
        activa = (sec == seccion_activa)
        col = color_area(sec)
        w = 7 if activa else 4
        pdf.set_fill_color(*col)
        pdf.rect(W - w, y, w, alto - 1.2, style="F", round_corners=("TOP_LEFT", "BOTTOM_LEFT"),
                 corner_radius=1.2)
        if activa:
            with pdf.rotation(90, W - w + 5.2, y + alto - 3.5):
                pdf.set_font(FONT, "B", 5.8); pdf.set_text_color(*BLANCO)
                pdf.text(W - w + 5.2, y + alto - 3.5, label_area(sec).upper()[:13])


def portada_seccion(pdf, seccion, bajada, n_estudios):
    """Página de apertura a todo color."""
    pdf.add_page()
    col = color_area(seccion)
    pdf.set_fill_color(*col)
    pdf.rect(0, 0, 210, 297, style="F")
    # molécula grande translúcida (tonos del mismo color, más claros)
    claro = tuple(min(255, c + 38) for c in col)
    claro2 = tuple(min(255, c + 70) for c in col)
    molecula(pdf, 158, 70, escala=3.4, alpha_dots=[claro, claro2, claro, claro2, claro])
    molecula(pdf, 40, 250, escala=2.2, alpha_dots=[claro, claro2, claro, claro2, claro])
    # etiqueta
    pdf.set_xy(20, 120); pdf.set_font(FONT, "B", 9); pdf.set_text_color(*claro2)
    pdf.cell(100, 5, "SECCIÓN")
    # título gigante
    pdf.set_xy(20, 128); pdf.set_font(FONT, "B", 40); pdf.set_text_color(*BLANCO)
    pdf.multi_cell(170, 17, label_area(seccion).upper(), align="L")
    # bajada
    pdf.set_xy(20, pdf.get_y() + 4); pdf.set_font(FONT, "", 11.5); pdf.set_text_color(*claro2)
    pdf.multi_cell(150, 6, bajada, align="L")
    # contador
    pdf.set_xy(20, 250); pdf.set_font(FONT, "B", 15); pdf.set_text_color(*BLANCO)
    pdf.cell(60, 8, f"{n_estudios} estudios")
    thumb_index(pdf, seccion)


def encabezado(pdf, seccion):
    """Encabezado fino con el color del área."""
    col = color_area(seccion)
    pdf.set_fill_color(*col)
    pdf.rect(0, 0, 210, 3.5, style="F")
    if (ASSETS / "logo_dimero.png").exists():
        pdf.image(str(ASSETS / "logo_dimero.png"), x=14, y=9, h=8)
    pdf.set_xy(100, 9); pdf.set_font(FONT, "B", 11); pdf.set_text_color(*col)
    pdf.cell(96, 5, label_area(seccion).upper(), align="R")
    pdf.set_xy(100, 14.5); pdf.set_font(FONT, "I", 7); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(96, 4, "Valores en pesos · IVA incluido", align="R")
    pdf.set_draw_color(*[min(255, c + 120) for c in col]); pdf.set_line_width(0.4)
    pdf.line(14, 21, 196, 21)


def barra_composicion(pdf, x, y, w_max, comp, total, total_max=None, h=3.2, mostrar_total=True):
    """Barra apilada PROPORCIONAL: el largo muestra el tamaño del perfil,
    los colores de qué está hecho. Así se comparan perfiles de un vistazo."""
    if not total:
        return
    total_max = total_max or total
    w = w_max * (total / total_max)
    cx = x
    for _, col, n in comp:
        seg = w * n / total
        pdf.set_fill_color(*col)
        pdf.rect(cx, y, seg, h, style="F")
        cx += seg
    if mostrar_total:
        pdf.set_xy(cx + 1.5, y - 1.2); pdf.set_font(FONT, "B", 7.5)
        pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(14, 4, str(total))


def leyenda_composicion(pdf, x, y, comp):
    pdf.set_font(FONT, "", 6.2)
    cx = x
    for nombre, col, n in comp:
        pdf.set_fill_color(*col)
        pdf.ellipse(cx, y + 0.5, 2.2, 2.2, style="F")
        pdf.set_xy(cx + 3, y - 0.6); pdf.set_text_color(*GRIS_SUAVE)
        t = f"{nombre} {n}"
        w = pdf.get_string_width(t) + 4
        pdf.cell(w, 3.4, t)
        cx += 3 + w


# ------------------------------------------------------------------ #
def pagina_combinables(pdf, est):
    """Página 'Armá tu propio perfil': explica el sistema y muestra el ahorro."""
    sec = "Químicas Combinables"
    col = color_area(sec)
    comb = est[est["seccion"] == sec].sort_values("orden")
    tiers = []
    for _, r in comb.iterrows():
        try:
            cant = int(str(r["nombre"]).split()[0])
        except (ValueError, IndexError):
            continue
        if pd.notna(r["precio_num"]):
            tiers.append((cant, float(r["precio_num"])))
    if not tiers:
        return
    base = dict(tiers).get(1, tiers[0][1])
    dets = [x.strip() for x in str(comb.iloc[0]["muestra"]).split("\n") if x.strip()]

    pdf.add_page()
    encabezado(pdf, sec)
    thumb_index(pdf, sec)
    ML, MR = 14, 190

    # título
    pdf.set_xy(ML, 28); pdf.set_font(FONT, "B", 24); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML, 11, "Armá tu propio perfil")
    pdf.set_xy(ML, 40); pdf.set_font(FONT, "", 10); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 45, 5,
                   "Elegí solo las determinaciones que tu paciente necesita. "
                   "Cuantas más combinás, menos te cuesta cada una.", align="L")
    # sello "único"
    pdf.set_fill_color(*col)
    pdf.rect(MR - 42, 29, 42, 9, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(MR - 42, 29.6); pdf.set_font(FONT, "B", 8); pdf.set_text_color(*BLANCO)
    pdf.cell(42, 8, "SISTEMA PROPIO", align="C")

    # chips de determinaciones disponibles
    y = 54
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 8); pdf.set_text_color(*col)
    pdf.cell(MR - ML, 4, f"LAS {len(dets)} DETERMINACIONES QUE PODÉS COMBINAR")
    y += 6
    cx = ML
    pdf.set_font(FONT, "", 7.8)
    for d in dets:
        w = pdf.get_string_width(d) + 6
        if cx + w > MR:
            cx = ML; y += 7
        pdf.set_fill_color(*[min(255, c + 155) for c in col])
        pdf.rect(cx, y, w, 5.6, style="F", round_corners=True, corner_radius=1.6)
        pdf.set_xy(cx, y + 0.1); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(w, 5.4, d, align="C")
        cx += w + 2.5
    y += 14

    # gráfico: precio por determinación
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 8); pdf.set_text_color(*col)
    pdf.cell(MR - ML, 4, "CUÁNTO TE SALE CADA DETERMINACIÓN SEGÚN CUÁNTAS COMBINES")
    y += 8
    alto_max = 40
    usable = MR - ML - 6
    pitch = usable / len(tiers)
    bw = pitch - 2.4
    max_unit = max(p / c for c, p in tiers)
    base_y = y + alto_max
    for i, (cant, precio) in enumerate(tiers):
        unit = precio / cant
        h = alto_max * unit / max_unit
        bx = ML + 3 + i * pitch
        destacado = cant in (1, len(tiers))
        c_bar = (226, 88, 30) if cant == len(tiers) else col
        pdf.set_fill_color(*c_bar)
        pdf.rect(bx, base_y - h, bw, h, style="F", round_corners=("TOP_LEFT", "TOP_RIGHT"),
                 corner_radius=1)
        # cantidad abajo
        pdf.set_xy(bx - 1, base_y + 1); pdf.set_font(FONT, "B", 6.5); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(bw + 2, 3.4, str(cant), align="C")
        # precio arriba en los destacados
        if destacado or cant in (5, 10):
            pdf.set_xy(bx - 3, base_y - h - 4.4); pdf.set_font(FONT, "B", 6.5)
            pdf.set_text_color(*(c_bar if cant == len(tiers) else GRIS_TXT))
            pdf.cell(bw + 6, 3.4, valor(unit), align="C")
    pdf.set_xy(ML, base_y + 5); pdf.set_font(FONT, "I", 6.8); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(60, 3.4, "cantidad de químicas combinadas")
    y = base_y + 12

    # bloque explicativo con ejemplos reales (sin inflar el ahorro máximo)
    t = dict(tiers)
    pdf.set_fill_color(*[min(255, c + 150) for c in col])
    pdf.rect(ML, y, MR - ML, 27, style="F", round_corners=True, corner_radius=2.5)
    pdf.set_xy(ML + 6, y + 3.5); pdf.set_font(FONT, "B", 11); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML - 12, 5.5, "Cada determinación que sumás abarata a todas las demás")
    # dos ejemplos concretos, mismo peso visual
    ejemplos = [
        ("Urea + Creatinina + Fósforo + Calcio", 4),
        ("Un perfil bioquímico de 10 determinaciones", 10),
    ]
    yy = y + 11
    for texto, cant in ejemplos:
        if cant not in t:
            continue
        pdf.set_xy(ML + 6, yy); pdf.set_font(FONT, "", 8.4); pdf.set_text_color(*GRIS_TXT)
        pdf.cell(88, 4.4, f"{texto} = {cant} químicas")
        pdf.set_xy(ML + 96, yy); pdf.set_font(FONT, "B", 8.4); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(26, 4.4, valor(t[cant]))
        pdf.set_xy(ML + 120, yy); pdf.set_font(FONT, "I", 7.8); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(50, 4.4, f"en vez de {valor(base * cant)} por separado")
        yy += 5.4
    pdf.set_xy(ML + 6, yy + 0.8); pdf.set_font(FONT, "I", 7); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(MR - ML - 12, 3.6,
             "Las bilirrubinas (directa, indirecta y total) cuentan como una sola química.")

    # CTA
    y += 32
    pdf.set_fill_color(*col)
    pdf.rect(ML, y, MR - ML, 11, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(ML, y + 1.2); pdf.set_font(FONT, "B", 9); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML, 4.5, "Armá tu perfil y pedilo en dimerolab.com.ar", align="C")
    pdf.set_xy(ML, y + 6); pdf.set_font(FONT, "", 7.5)
    pdf.cell(MR - ML, 4, "¿Dudas sobre qué combinar? Escribinos por WhatsApp 11 55042497", align="C")


CAMINO = [
    ((14, 154, 174), "Cargás la remisión en la app",
     "Sin papel: cargás paciente y estudios en dimerolab.com.ar. La muestra viaja "
     "solo con su código de remisión.",
     [("REMISIÓN 100% DIGITAL", (14, 154, 174))],
     ""),

    ((46, 155, 143), "Pedís el retiro desde la misma app",
     "No hace falta llamar ni coordinar por otro lado: solicitás el retiro donde ya "
     "cargaste la remisión.",
     [("RETIRO CON SEGUIMIENTO", (46, 155, 143))],
     "Un encargado de logística coordina las motos, y vos seguís el estado desde la app: "
     "el ícono cambia de color cuando el retiro está coordinado y cuando ya se hizo."),

    ((0, 96, 120), "Ingresamos escaneando, sin transcribir nada",
     "Escaneamos ese código y aparece toda la información que cargaste. No copiamos "
     "datos a mano, así que no hay error de transcripción.",
     [("CERO TRANSCRIPCIÓN", (0, 96, 120)), ("TRAZABILIDAD", (48, 140, 220))],
     "Cada muestra se rotula de forma automática con los datos de tu remisión."),

    ((226, 88, 30), "Verificamos que la muestra sirva",
     "Antes de procesar, controlamos que esté en condiciones.",
     [("GARANTÍA DE MUESTRA", (226, 88, 30))],
     "Si no permite procesar el estudio —insuficiente, lipémica, muy hemolizada o con el "
     "tubo coagulado— queda pendiente y lo repetimos sin cargo. Coordinamos por WhatsApp."),

    ((0, 120, 144), "Procesamos con control de calidad",
     "Además de los controles internos de rutina del laboratorio, participamos de un "
     "programa externo de control de calidad.",
     [("AAVLD · CIAAVLD", (46, 155, 143))],
     "Somos socios de la AAVLD (Asociación Argentina de Veterinarios de Laboratorios de "
     "Diagnóstico) y participamos del CIAAVLD, su programa de control interlaboratorios: "
     "nuestros resultados se comparan periódicamente con los de otros laboratorios del país."),

    ((123, 79, 163), "Profesionales en todas las etapas",
     "Desde el ingreso hasta el informe, cada etapa está a cargo de profesionales.",
     [("LECTURA PROFESIONAL", (123, 79, 163)), ("YA INCLUIDO", (226, 88, 30))],
     "Nuestro hemograma ya incluye el recuento de plaquetas al microscopio y la "
     "morfología celular: no hace falta pedirlos aparte ni se cobran por separado."),

    ((240, 120, 0), "Recibís el informe y te acompañamos",
     "El informe llega online. Si te queda una duda, te respondemos por WhatsApp.",
     [("ASESORAMIENTO", (240, 120, 0))],
     "Antes de responderte revisamos el informe para interiorizarnos en el caso. Si tu "
     "clínica tiene varios profesionales, armamos un grupo."),

    ((48, 140, 220), "Guardamos tu muestra",
     "Suero y sangre entera: 10 días en heladera y 1 mes en freezer.",
     [("AMPLIÁ SIN VOLVER A EXTRAER", (48, 140, 220))],
     "¿Necesitás agregar un estudio? Consultanos por WhatsApp y te confirmamos si se "
     "puede hacer con la muestra guardada (puede demorar hasta 24 hs)."),
]


def pagina_camino(pdf):
    """Página institucional: el recorrido de la muestra dentro del laboratorio."""
    pdf.add_page()
    ML, MR = 16, 194
    col_base = (0, 96, 120)

    # franja superior + título
    pdf.set_fill_color(*col_base); pdf.rect(0, 0, 210, 3.5, style="F")
    if (ASSETS / "logo_dimero.png").exists():
        pdf.image(str(ASSETS / "logo_dimero.png"), x=ML, y=9, h=8)
    pdf.set_xy(ML, 24); pdf.set_font(FONT, "B", 26); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML, 12, "El camino de tu muestra")
    pdf.set_xy(ML, 37); pdf.set_font(FONT, "", 10.5); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 20, 5, "Qué pasa desde que nos la enviás hasta que tenés el "
                                    "resultado — y después también.", align="L")

    x_num = ML + 5          # centro de los círculos
    x_txt = ML + 18
    w_txt = MR - x_txt
    y = 47

    for i, (col, titulo, texto, sellos, detalle) in enumerate(CAMINO):
        # medir
        pdf.set_font(FONT, "", 8.4)
        n1 = len(pdf.multi_cell(w_txt, 4.2, texto, dry_run=True, output="LINES"))
        n2 = 0
        if detalle:
            pdf.set_font(FONT, "", 7.4)
            n2 = len(pdf.multi_cell(w_txt - 4, 3.7, detalle, dry_run=True, output="LINES"))
        h = 6.5 + n1 * 4.2 + 5.6 + (n2 * 3.7 + 1.5 if detalle else 0) + 3

        # línea conectora
        if i < len(CAMINO) - 1:
            pdf.set_draw_color(*[min(255, c + 130) for c in col])
            pdf.set_line_width(0.8)
            pdf.line(x_num, y + 9, x_num, y + h + 2)
        # círculo numerado
        pdf.set_fill_color(*col)
        pdf.ellipse(x_num - 4.2, y - 0.5, 8.4, 8.4, style="F")
        pdf.set_xy(x_num - 4.2, y + 0.9); pdf.set_font(FONT, "B", 8.5); pdf.set_text_color(*BLANCO)
        pdf.cell(8.4, 5, str(i + 1), align="C")

        # título
        pdf.set_xy(x_txt, y - 0.5); pdf.set_font(FONT, "B", 11); pdf.set_text_color(*col)
        pdf.cell(w_txt, 6, titulo)
        # texto
        pdf.set_xy(x_txt, y + 6); pdf.set_font(FONT, "", 8.4); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(w_txt, 4.2, texto, align="L")
        yy = pdf.get_y() + 1.2
        # sellos
        cx = x_txt
        for label, c_s in sellos:
            pdf.set_font(FONT, "B", 6.2)
            w = pdf.get_string_width(label) + 6
            pdf.set_fill_color(*c_s)
            pdf.rect(cx, yy, w, 4.6, style="F", round_corners=True, corner_radius=1.4)
            pdf.set_xy(cx, yy + 0.1); pdf.set_text_color(*BLANCO)
            pdf.cell(w, 4.4, label, align="C")
            cx += w + 2.5
        yy += 5.6
        # detalle en gris (si lo hay)
        if detalle:
            pdf.set_xy(x_txt + 4, yy + 1.5); pdf.set_font(FONT, "", 7.4)
            pdf.set_text_color(*GRIS_SUAVE)
            pdf.multi_cell(w_txt - 4, 3.7, detalle, align="L")
            yy = pdf.get_y()
        y = yy + 1.6

    # cierre
    pdf.set_fill_color(*col_base)
    pdf.rect(ML, y, MR - ML, 13, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(ML, y + 1.8); pdf.set_font(FONT, "B", 9.5); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML, 5, "Pedí tus estudios en dimerolab.com.ar", align="C")
    pdf.set_xy(ML, y + 7); pdf.set_font(FONT, "", 8)
    pdf.cell(MR - ML, 4, "Consultas y asesoramiento por WhatsApp 11 55042497", align="C")


def prototipo_A4(est):
    pdf = Proto()
    ML, MR = 14, 190

    # ---------- 1) portada de sección ----------
    perfiles = est[(est["lista"] == "Perfiles") & (est["seccion"] == "PERFILES")]
    portada_seccion(pdf, "PERFILES",
                    "Combinaciones armadas por nuestro equipo para responder "
                    "las preguntas clínicas más frecuentes, con el mejor rendimiento por muestra.",
                    len(perfiles))

    # ---------- 2) página de perfiles con barra de composición ----------
    pdf.add_page()
    encabezado(pdf, "PERFILES")
    thumb_index(pdf, "PERFILES")
    y = 28
    muestra_perfiles = perfiles.head(5)
    max_dets = max(total_parametros(dets_de(r.get("descripcion", ""))) for _, r in muestra_perfiles.iterrows())
    for _, row in muestra_perfiles.iterrows():
        nombre = str(row["nombre"])
        dets = dets_de(row.get("descripcion", ""))
        comp = composicion(dets)
        n_param = total_parametros(dets)
        muestra = "" if pd.isna(row.get("muestra")) else str(row["muestra"])
        flow = "  ·  ".join(dets)
        con_hg = tiene_hemograma(dets)

        pdf.set_font(FONT, "", 8.2)
        n_lines = len(pdf.multi_cell(MR - ML - 4, 4.2, flow, dry_run=True, output="LINES")) if flow else 0
        h = 13 + n_lines * 4.2 + 8 + (5 if con_hg else 0)

        # tarjeta con filete de color a la izquierda
        pdf.set_fill_color(250, 251, 252)
        pdf.rect(ML, y, MR - ML, h, style="F", round_corners=True, corner_radius=2)
        pdf.set_fill_color(*color_area("PERFILES"))
        pdf.rect(ML, y, 2.6, h, style="F", round_corners=True, corner_radius=1)

        pdf.set_xy(ML + 7, y + 3); pdf.set_font(FONT, "B", 12.5); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(pdf.get_string_width(nombre) + 2, 6, nombre)
        wn = pdf.get_string_width(nombre)
        pdf.set_xy(ML + 7 + wn + 5, y + 4.4); pdf.set_font(FONT, "", 10); pdf.set_text_color(*PRECIO_GRIS)
        pdf.cell(30, 4, valor(row.get("precio_num")))

        # barra de composición: largo = parámetros informados
        barra_composicion(pdf, MR - 60, y + 5, 44, comp, n_param, max_dets)
        pdf.set_xy(MR - 60, y + 0.5); pdf.set_font(FONT, "", 6.2); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(44, 3.4, "PARÁMETROS INFORMADOS")
        leyenda_composicion(pdf, MR - 60, y + 9.5, comp)

        pdf.set_xy(ML + 7, y + 13); pdf.set_font(FONT, "", 8.2); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(MR - ML - 12, 4.2, flow, align="L")
        yb = pdf.get_y() + 1
        pdf.set_font(FONT, "", 6.8); pdf.set_text_color(*GRIS_SUAVE)
        pdf.set_xy(ML + 7, yb); pdf.cell(12, 3.4, "Remitir")
        cx = ML + 20
        for lb, col in tubos_de(muestra):
            pdf.set_fill_color(*col); pdf.ellipse(cx, yb + 0.6, 2.6, 2.6, style="F")
            pdf.set_xy(cx + 3.4, yb - 0.3); pdf.set_text_color(*GRIS_SUAVE)
            w = pdf.get_string_width(lb) + 4
            pdf.cell(w, 3.4, lb); cx += 3.4 + w
        # sello "incluido siempre" cuando el perfil lleva hemograma
        if con_hg:
            ys = yb + 4.6
            col_s = color_area("Hematología Y Hemostasia")
            pdf.set_fill_color(*[min(255, c + 150) for c in col_s])
            pdf.rect(ML + 7, ys - 1, MR - ML - 14, 4.6, style="F", round_corners=True, corner_radius=1)
            pdf.set_xy(ML + 9, ys - 0.8); pdf.set_font(FONT, "B", 6.2); pdf.set_text_color(*col_s)
            pdf.cell(17, 4, "✓ INCLUIDO")
            pdf.set_font(FONT, "", 6.2); pdf.set_text_color(*GRIS_TXT)
            pdf.set_xy(ML + 27, ys - 0.8)
            pdf.cell(150, 4, "Recuento plaquetario corroborado por microscopía · fórmula leucocitaria con formas "
                             "inmaduras (relativa y absoluta) · morfología eritrocitaria")
        y += h + 4

    # ---------- 2b) armá tu propio perfil ----------
    pagina_combinables(pdf, est)

    # ---------- 3) sección individual con su color ----------
    sec = "Serología e Inmunología"
    sero = est[(est["lista"] == "Detallado") & (est["seccion"] == sec)]
    portada_seccion(pdf, sec,
                    "Detección de anticuerpos y antígenos para las infecciosas "
                    "que más impactan en la clínica diaria.", len(sero))

    pdf.add_page()
    encabezado(pdf, sec)
    thumb_index(pdf, sec)
    col = color_area(sec)
    y = 28
    for _, row in sero.head(16).iterrows():
        nombre = str(row["nombre"])
        obs = "" if pd.isna(row.get("observaciones")) else str(row["observaciones"])
        muestra = "" if pd.isna(row.get("muestra")) else str(row["muestra"])
        pdf.set_fill_color(*col)
        pdf.rect(ML, y + 1.6, 2, 2, style="F")
        pdf.set_xy(ML + 6, y); pdf.set_font(FONT, "B", 9.2); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(pdf.get_string_width(nombre) + 2, 5, nombre)
        xn = ML + 6 + pdf.get_string_width(nombre)
        pdf.set_xy(xn + 4, y + 0.5); pdf.set_font(FONT, "", 9); pdf.set_text_color(*PRECIO_GRIS)
        pdf.cell(24, 4, valor(row.get("precio_num")))
        xp = xn + 4 + pdf.get_string_width(valor(row.get("precio_num")))
        if obs:
            pdf.set_font(FONT, "I", 7); pdf.set_text_color(*GRIS_SUAVE)
            pdf.set_xy(xp + 5, y + 0.9); pdf.cell(60, 4, "· " + obs[:34])
        # tubo a la derecha
        cx = MR - 22
        for lb, c2 in tubos_de(muestra)[:2]:
            pdf.set_fill_color(*c2); pdf.ellipse(cx, y + 1.6, 2.4, 2.4, style="F"); cx += 4
        y += 7.2

    pdf.output(str(BASE / "mockup_C.pdf"))


# ------------------------------------------------------------------ #
def prototipo_mobile(est):
    """Formato pensado para leer en el celular."""
    W, H = 95, 170
    pdf = Proto(fmt=(W, H))
    ML, MR = 8, W - 8

    # portada
    pdf.add_page()
    col = color_area("PERFILES")
    pdf.set_fill_color(*col); pdf.rect(0, 0, W, H, style="F")
    claro = tuple(min(255, c + 45) for c in col)
    claro2 = tuple(min(255, c + 85) for c in col)
    molecula(pdf, 74, 34, escala=1.7, alpha_dots=[claro, claro2, claro, claro2, claro])
    pdf.set_xy(ML, 62); pdf.set_font(FONT, "B", 8); pdf.set_text_color(*claro2)
    pdf.cell(60, 4, "SECCIÓN")
    pdf.set_xy(ML, 68); pdf.set_font(FONT, "B", 24); pdf.set_text_color(*BLANCO)
    pdf.multi_cell(MR - ML, 11, "PERFILES", align="L")
    pdf.set_xy(ML, pdf.get_y() + 3); pdf.set_font(FONT, "", 8.5); pdf.set_text_color(*claro2)
    pdf.multi_cell(MR - ML, 4.6, "Deslizá para ver los perfiles y qué incluye cada uno.", align="L")
    pdf.set_xy(ML, H - 20); pdf.set_font(FONT, "B", 10); pdf.set_text_color(*BLANCO)
    pdf.cell(50, 6, f"{len(est[(est['lista']=='Perfiles') & (est['seccion']=='PERFILES')])} perfiles")

    # listado
    pdf.add_page()
    pdf.set_fill_color(*col); pdf.rect(0, 0, W, 2.5, style="F")
    pdf.set_xy(ML, 6); pdf.set_font(FONT, "B", 9); pdf.set_text_color(*col)
    pdf.cell(MR - ML, 5, "PERFILES")
    y = 14
    perfiles = est[(est["lista"] == "Perfiles") & (est["seccion"] == "PERFILES")].head(4)
    max_dets_m = max(len(dets_de(r.get("descripcion", ""))) for _, r in perfiles.iterrows())
    for _, row in perfiles.iterrows():
        nombre = str(row["nombre"])
        dets = dets_de(row.get("descripcion", ""))
        comp = composicion(dets)
        pdf.set_font(FONT, "", 6.6)
        flow = " · ".join(dets)
        nl = len(pdf.multi_cell(MR - ML - 4, 3.2, flow, dry_run=True, output="LINES"))
        h = 20 + nl * 3.2
        pdf.set_fill_color(249, 250, 251)
        pdf.rect(ML, y, MR - ML, h, style="F", round_corners=True, corner_radius=2)
        pdf.set_fill_color(*col); pdf.rect(ML, y, 2, h, style="F", round_corners=True, corner_radius=1)
        pdf.set_xy(ML + 5, y + 2.5); pdf.set_font(FONT, "B", 10); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(MR - ML - 8, 5, nombre)
        pdf.set_xy(ML + 5, y + 8); pdf.set_font(FONT, "", 9); pdf.set_text_color(*PRECIO_GRIS)
        pdf.cell(30, 4, valor(row.get("precio_num")))
        barra_composicion(pdf, MR - 40, y + 9, 31, comp, len(dets), max_dets_m, h=2.6)
        pdf.set_xy(ML + 5, y + 14); pdf.set_font(FONT, "", 6.6); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(MR - ML - 8, 3.2, flow, align="L")
        y += h + 3

    pdf.output(str(BASE / "mockup_MOBILE.pdf"))


if __name__ == "__main__":
    est = pd.read_excel(BASE / "data" / "estudios.xlsx", sheet_name="Estudios")
    est = est[est["activo"].astype(str).str.upper() == "SI"].sort_values("orden")
    prototipo_A4(est)
    prototipo_mobile(est)
    print("Generados: mockup_C.pdf y mockup_MOBILE.pdf")


# ------------------------------------------------------------------ #
#  Página "despertar": capacidades que el cliente quizás no usa
# ------------------------------------------------------------------ #
SABIAS = [
    ((46, 155, 143), "Hacer que el informe le llegue directo al tutor",
     "Cargá el mail del tutor en el protocolo y el informe se le envía solo cuando está "
     "listo. No tenés que reenviar nada: le avisás que le va a llegar por mail.",
     "También podés cargar el mail de la veterinaria si preferís recibirlos ahí en vez "
     "de entrar a la plataforma."),

    ((14, 154, 174), "Armar tu propio perfil",
     "Combiná solo las químicas que ese paciente necesita. Cada determinación sale menos "
     "que pedida por separado.",
     "Ver la página “Armá tu propio perfil”."),

    ((48, 140, 220), "Agregar estudios sin volver a pinchar",
     "Guardamos tus muestras hasta un mes. Si te faltó pedir algo, consultanos por "
     "WhatsApp y te confirmamos si se puede hacer con la muestra guardada.",
     ""),

    ((123, 79, 163), "Dejar de pedir aparte lo que ya está incluido",
     "El hemograma ya incluye el recuento de plaquetas al microscopio y la morfología "
     "celular. No hace falta agregarlos ni se cobran por separado.",
     ""),
]


def pagina_sabias(pdf):
    pdf.add_page()
    ML, MR = 16, 194
    col_base = (0, 96, 120)

    pdf.set_fill_color(*col_base); pdf.rect(0, 0, 210, 3.5, style="F")
    if (ASSETS / "logo_dimero.png").exists():
        pdf.image(str(ASSETS / "logo_dimero.png"), x=ML, y=9, h=8)

    pdf.set_xy(ML, 26); pdf.set_font(FONT, "B", 27); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML, 12, "¿Sabías que podés…?")
    pdf.set_xy(ML, 40); pdf.set_font(FONT, "", 10.5); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 15, 5, "Cosas que ya están disponibles y quizás no estás "
                                    "usando. Todas se hacen desde la app.", align="L")

    y = 56
    for col, titulo, texto, extra in SABIAS:
        pdf.set_font(FONT, "", 9)
        n1 = len(pdf.multi_cell(MR - ML - 16, 4.6, texto, dry_run=True, output="LINES"))
        n2 = 0
        if extra:
            pdf.set_font(FONT, "I", 7.6)
            n2 = len(pdf.multi_cell(MR - ML - 16, 3.8, extra, dry_run=True, output="LINES"))
        h = 11 + n1 * 4.6 + (n2 * 3.8 + 2 if extra else 0) + 7

        pdf.set_fill_color(250, 251, 252)
        pdf.rect(ML, y, MR - ML, h, style="F", round_corners=True, corner_radius=2.5)
        pdf.set_fill_color(*col)
        pdf.rect(ML, y, 3, h, style="F", round_corners=True, corner_radius=1)
        # punto de marca
        pdf.ellipse(ML + 8, y + 5.6, 4.4, 4.4, style="F")

        pdf.set_xy(ML + 16, y + 3.4); pdf.set_font(FONT, "B", 12); pdf.set_text_color(*col)
        pdf.cell(MR - ML - 20, 6, titulo)
        pdf.set_xy(ML + 16, y + 11); pdf.set_font(FONT, "", 9); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(MR - ML - 22, 4.6, texto, align="L")
        if extra:
            pdf.set_xy(ML + 16, pdf.get_y() + 1.2); pdf.set_font(FONT, "I", 7.6)
            pdf.set_text_color(*GRIS_SUAVE)
            pdf.multi_cell(MR - ML - 22, 3.8, extra, align="L")
        y += h + 5

    # cierre
    pdf.set_fill_color(*col_base)
    pdf.rect(ML, y + 2, MR - ML, 14, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(ML, y + 4); pdf.set_font(FONT, "B", 10); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML, 5, "Todo esto ya está en dimerolab.com.ar", align="C")
    pdf.set_xy(ML, y + 9.5); pdf.set_font(FONT, "", 8)
    pdf.cell(MR - ML, 4, "¿Te ayudamos a empezar? WhatsApp 11 55042497", align="C")

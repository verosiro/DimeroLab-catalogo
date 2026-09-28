#!/usr/bin/env python3
"""
Generador del Catálogo de Servicios DimeroLab.

Diseño "audaz con sistema":
  - color por área diagnóstica (el color SIEMPRE significa algo)
  - índice de uña (pestañas de color en el borde de la página)
  - portadas de lista a todo color
  - precio discreto (menu engineering): el nombre manda, el precio acompaña
  - puntos de color = tubo de muestra
  - barra de PARÁMETROS INFORMADOS en los perfiles

Uso:
    from generar_pdf import construir_pdf, cargar_datos
    est, cfg = cargar_datos("data/estudios.xlsx")
    construir_pdf(est, cfg, "Catalogo.pdf", incluir_folleto=True)
"""
from pathlib import Path
import pandas as pd
from fpdf import FPDF

BASE = Path(__file__).parent
ASSETS = BASE / "assets"
FONT = "DejaVu"        # datos y texto: legible en tamaños chicos
DISPLAY = "Poppins"    # títulos: geométrica, dialoga con el logo

# ---- Paleta base DimeroLab ----
TEAL        = (0, 120, 144)
TEAL_OSC    = (0, 96, 120)
TEAL_SUAVE  = (224, 240, 242)
TEAL_XSUAVE = (242, 249, 250)
AZUL        = (48, 168, 240)
NARANJA     = (240, 120, 0)
GRIS_TXT    = (70, 78, 82)
GRIS_SUAVE  = (150, 158, 162)
NEGRO_SUAVE = (28, 38, 44)
BLANCO      = (255, 255, 255)
PRECIO_GRIS = (90, 100, 105)

# ---- SISTEMA DE COLOR POR ÁREA ----
AREAS = {
    "PERFILES":                 ("Perfiles",     (0, 96, 120)),
    "Paneles bioquímicos":      ("Paneles",      (0, 140, 155)),
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
    return AREAS.get(seccion, ("", TEAL))[1]


def label_area(seccion):
    return AREAS.get(seccion, (str(seccion), TEAL))[0]


# ---- puntos de color = tubo de muestra ----
TUBOS = [
    ("edta",     ("EDTA",         (123, 79, 163))),
    ("violeta",  ("EDTA",         (123, 79, 163))),
    ("seco",     ("Seco/con gel", (214, 72, 74))),
    ("rojo",     ("Seco/con gel", (214, 72, 74))),
    ("suero",    ("Seco/con gel", (214, 72, 74))),
    ("citrato",  ("Citrato",      (77, 182, 230))),
    ("celeste",  ("Citrato",      (77, 182, 230))),
    ("glucemia", ("Glucemia",     (120, 126, 131))),
    ("naranja",  ("Glucemia",     (120, 126, 131))),
    ("gris",     ("Glucemia",     (120, 126, 131))),
    ("orina",    ("Orina",        (232, 185, 58))),
    ("hisopado", ("Hisopado",     (88, 168, 122))),
    ("fecal",    ("Materia fecal",(140, 110, 60))),
    ("formol",   ("Tejido/Formol",(176, 181, 186))),
    ("tejido",   ("Tejido/Formol",(176, 181, 186))),
    ("frotis",   ("Frotis",       (214, 72, 74))),
    ("capilar",  ("Frotis",       (214, 72, 74))),
]
LEYENDA_TUBOS = ["EDTA", "Seco/con gel", "Citrato", "Glucemia", "Orina",
                 "Hisopado", "Materia fecal"]


def tubos_de(muestra):
    m = str(muestra or "").lower()
    vistos, out = [], []
    for key, (label, color) in TUBOS:
        if key in m and label not in vistos:
            vistos.append(label)
            out.append((label, color))
    return out


def color_tubo(label):
    for _, (lb, color) in TUBOS:
        if lb == label:
            return color
    return GRIS_SUAVE


# ---- parámetros informados (peso real de cada determinación) ----
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
AREAS_DET = [
    ("Hematología", (123, 79, 163),
     ["hemograma", "plaqueta", "reticulocito", "hemoparásito", "coagulograma",
      "protrombina", "kptt", "tipificación", "knott", "coombs", "frotis"]),
    ("Hormonas", (240, 120, 0),
     ["t4", "t3", "tsh", "cortisol", "insulina", "progesterona", "estradiol",
      "testosterona", "parathormona", "igf"]),
    ("Serología", (48, 140, 220),
     ["vif", "vilef", "ehrlichia", "anaplasma", "toxoplasmosis", "leishmania",
      "(ic)", "ifi", "brucella", "moquillo", "parvovirus", "dirofilaria"]),
    ("Orina", (214, 160, 26), ["orina", "proteinuria", "creatininuria", "urinario"]),
    ("Química", (0, 120, 144), []),
]


def peso_det(texto):
    t = str(texto).lower()
    for claves, p in PESOS:
        if any(k in t for k in claves):
            return p
    return 1


def area_det(texto):
    t = str(texto).lower()
    for nombre, color, claves in AREAS_DET:
        if claves and any(k in t for k in claves):
            return nombre, color
    return AREAS_DET[-1][0], AREAS_DET[-1][1]


def composicion(dets):
    conteo = {}
    for d in dets:
        n, c = area_det(d)
        conteo.setdefault(n, [c, 0])[1] += peso_det(d)
    orden = ["Hematología", "Química", "Hormonas", "Serología", "Orina"]
    return [(k, conteo[k][0], conteo[k][1]) for k in orden if k in conteo]


def total_parametros(dets):
    return sum(peso_det(d) for d in dets)


# ---- formato ----
def money(v):
    """Formato $14.580 (se mantiene por compatibilidad con la app)."""
    try:
        return "$" + f"{int(round(float(v))):,}".replace(",", ".")
    except (ValueError, TypeError):
        return ""


def valor(v):
    """Precio discreto: sin símbolo ni decimales."""
    try:
        return f"{int(round(float(v))):,}".replace(",", ".")
    except (ValueError, TypeError):
        return ""


def cargar_datos(xlsx_path):
    est = pd.read_excel(xlsx_path, sheet_name="Estudios")
    cfg_df = pd.read_excel(xlsx_path, sheet_name="Config")
    cfg = dict(zip(cfg_df["clave"], cfg_df["valor"]))
    return est, cfg


# ---- sellos (etiquetas de valor junto al estudio) ----
SELLO_COLORES = {
    "YA INCLUIDO":         (226, 88, 30),
    "CON IMÁGENES":        (48, 140, 220),
    "LECTURA PROFESIONAL": (123, 79, 163),
    "MUESTRA CONSERVADA":  (48, 140, 220),
}

# Notas al pie del encabezado de sección (evitan repetir un sello en cada estudio)
NOTAS_SECCION = {
    "Paneles bioquímicos": "Son los perfiles sin el hemograma. Si además necesitás "
                           "hematología, mirá la sección Perfiles.",
    "Patología": "Las citologías e histopatologías incluyen imágenes de lo observado "
                 "cuando el hallazgo lo amerita.",
}


def _sellos_de(row):
    v = row.get("sellos", "")
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    return [x.strip() for x in str(v).split(",") if x.strip()]


def _dibujar_sellos(pdf, x, y, sellos, size=5.8):
    """Chips de sello. Devuelve el ancho usado."""
    cx = x
    for etq in sellos:
        col = SELLO_COLORES.get(etq.upper(), TEAL)
        pdf.set_font(FONT, "B", size)
        w = pdf.get_string_width(etq) + 4.5
        pdf.set_fill_color(*col)
        pdf.rect(cx, y, w, 3.9, style="F", round_corners=True, corner_radius=1.2)
        pdf.set_xy(cx, y + 0.05); pdf.set_text_color(*BLANCO)
        pdf.cell(w, 3.8, etq, align="C")
        cx += w + 1.8
    return cx - x


def _split_bullets(desc):
    return [x.strip().lstrip("•").strip()
            for x in str(desc).split("\n") if x.strip().lstrip("•").strip()]


# ================================================================== #
class DimeroPDF(FPDF):
    ML, MR = 14, 192   # el margen derecho deja lugar al índice de uña

    def __init__(self, cfg):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.cfg = cfg
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(self.ML, 14, 210 - self.MR)
        self.add_font(FONT, "", str(ASSETS / "DejaVuSans.ttf"))
        self.add_font(FONT, "B", str(ASSETS / "DejaVuSans-Bold.ttf"))
        self.add_font(FONT, "I", str(ASSETS / "DejaVuSans-Oblique.ttf"))
        self.add_font(DISPLAY, "", str(ASSETS / "Poppins-Regular.ttf"))
        self.add_font(DISPLAY, "B", str(ASSETS / "Poppins-Bold.ttf"))
        self.add_font(DISPLAY, "I", str(ASSETS / "Poppins-SemiBold.ttf"))
        self.logo = ASSETS / "logo_dimero.png"
        self.folleto_pages = 0
        self.seccion_actual = None
        self.en_portada = False
        self.paginas_sin_chrome = set()
        self.tabs = list(ORDEN_TABS)   # se reemplaza por las secciones realmente activas
        self.modo_institucional = False  # páginas de relato: encabezado simple, sin índice

    def _sin_chrome(self):
        return (self.page_no() <= self.folleto_pages
                or self.page_no() in self.paginas_sin_chrome)

    # ---------- Encabezado ----------
    def header(self):
        if self.en_portada or self._sin_chrome():
            return
        if self.modo_institucional:
            self.set_fill_color(*TEAL_OSC)
            self.rect(0, 0, 210, 3.2, style="F")
            if self.logo.exists():
                self.image(str(self.logo), x=16, y=8.5, h=8)
            self.set_y(22)
            return
        col = color_area(self.seccion_actual)
        self.set_fill_color(*col)
        self.rect(0, 0, 210, 3.2, style="F")
        if self.logo.exists():
            self.image(str(self.logo), x=self.ML, y=8.5, h=8)
        self.set_xy(90, 8.5); self.set_font(FONT, "B", 11); self.set_text_color(*col)
        self.cell(self.MR - 90, 5, label_area(self.seccion_actual).upper(), align="R")
        self.set_xy(90, 14); self.set_font(FONT, "I", 7); self.set_text_color(*GRIS_SUAVE)
        self.cell(self.MR - 90, 4, "Valores en pesos · IVA incluido", align="R")
        self.set_draw_color(*[min(255, c + 120) for c in col]); self.set_line_width(0.4)
        self.line(self.ML, 20.5, self.MR, 20.5)
        self.thumb_index()
        self.set_y(26)

    # ---------- Pie ----------
    def footer(self):
        if self._sin_chrome():
            return
        self.set_y(-13)
        self.set_font(FONT, "", 7.2)
        self.set_text_color(*GRIS_SUAVE)
        c = self.cfg
        datos = "   ·   ".join([str(c.get("web", "")), str(c.get("instagram", "")),
                                f"WhatsApp {c.get('whatsapp','')}"])
        self.cell(0, 5, datos, align="L")
        self.cell(0, 5, str(self.page_no()), align="R")

    # ---------- Índice de uña ----------
    def thumb_index(self, top=30, bot=283):
        if not self.tabs:
            return
        alto = (bot - top) / len(self.tabs)
        for i, sec in enumerate(self.tabs):
            y = top + i * alto
            activa = (sec == self.seccion_actual)
            w = 7 if activa else 3.5
            self.set_fill_color(*color_area(sec))
            self.rect(210 - w, y, w, alto - 1.2, style="F",
                      round_corners=("TOP_LEFT", "BOTTOM_LEFT"), corner_radius=1.2)
            if activa:
                with self.rotation(90, 210 - w + 5.2, y + alto - 3.5):
                    self.set_font(FONT, "B", 5.6); self.set_text_color(*BLANCO)
                    self.text(210 - w + 5.2, y + alto - 3.5, label_area(sec).upper()[:13])

    def _lineas(self, texto, w, font_style="", size=9):
        self.set_font(FONT, font_style, size)
        return self.multi_cell(w, 5, str(texto), dry_run=True, output="LINES")


def molecula(pdf, cx, cy, escala, tonos):
    for i, (dx, dy, r) in enumerate([(0, 0, 9), (11, -7, 6), (8, 9, 5), (-10, 6, 4), (-7, -9, 3)]):
        pdf.set_fill_color(*tonos[i % len(tonos)])
        d = r * escala
        pdf.ellipse(cx + dx * escala - d / 2, cy + dy * escala - d / 2, d, d, style="F")


def portada_lista(pdf, titulo, bajada, n, col):
    """Página de apertura a todo color."""
    pdf.en_portada = True
    pdf.add_page()
    pdf.paginas_sin_chrome.add(pdf.page_no())
    pdf.en_portada = False
    pdf.set_fill_color(*col); pdf.rect(0, 0, 210, 297, style="F")
    claro = tuple(min(255, c + 38) for c in col)
    claro2 = tuple(min(255, c + 78) for c in col)
    molecula(pdf, 158, 68, 3.4, [claro, claro2])
    molecula(pdf, 38, 252, 2.2, [claro, claro2])
    logo_b = ASSETS / "logo_blanco.png"
    if logo_b.exists():
        pdf.image(str(logo_b), x=20, y=24, w=52)
    pdf.set_xy(20, 118); pdf.set_font(FONT, "B", 9); pdf.set_text_color(*claro2)
    pdf.cell(120, 5, "CATÁLOGO DE SERVICIOS")
    pdf.set_xy(20, 126); pdf.set_font(DISPLAY, "B", 34); pdf.set_text_color(*BLANCO)
    pdf.multi_cell(165, 16, titulo, align="L")
    pdf.set_xy(20, pdf.get_y() + 4); pdf.set_font(FONT, "", 11.5); pdf.set_text_color(*claro2)
    pdf.multi_cell(150, 6, bajada, align="L")
    pdf.set_xy(20, 252); pdf.set_font(FONT, "B", 15); pdf.set_text_color(*BLANCO)
    pdf.cell(80, 8, f"{n} estudios")


def _seccion(pdf, titulo):
    """Encabezado de sección con el color del área."""
    ML, MR = pdf.ML, pdf.MR
    col = color_area(titulo)
    if pdf.get_y() > 258:
        pdf.add_page()
    pdf.ln(2)
    y = pdf.get_y()
    pdf.set_fill_color(*col)
    pdf.rect(ML, y + 1, 3.2, 8, style="F", round_corners=True, corner_radius=1)
    pdf.set_xy(ML + 7, y - 0.5); pdf.set_font(DISPLAY, "B", 13); pdf.set_text_color(*col)
    pdf.cell(MR - ML - 7, 8, str(titulo))
    pdf.set_draw_color(*[min(255, c + 130) for c in col]); pdf.set_line_width(0.5)
    pdf.line(ML, y + 10.5, MR, y + 10.5)
    pdf.set_y(y + 14)
    nota = NOTAS_SECCION.get(str(titulo).strip())
    if nota:
        pdf.set_xy(ML, pdf.get_y() - 1); pdf.set_font(FONT, "I", 7.4)
        pdf.set_text_color(*GRIS_SUAVE)
        pdf.multi_cell(MR - ML, 3.8, nota, align="L")
        pdf.set_y(pdf.get_y() + 2)


def _leyenda_tubos(pdf):
    ML, MR = pdf.ML, pdf.MR
    y = pdf.get_y()
    pdf.set_xy(ML, y); pdf.set_font(FONT, "", 7); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(15, 4, "Muestra:")
    cx = ML + 15
    for label in LEYENDA_TUBOS:
        pdf.set_fill_color(*color_tubo(label))
        pdf.ellipse(cx, y + 1, 3, 3, style="F")
        pdf.set_xy(cx + 4, y - 0.3); pdf.set_text_color(*GRIS_SUAVE)
        w = pdf.get_string_width(label) + 5
        pdf.cell(w, 4, label)
        cx += 4 + w
    pdf.set_y(y + 6)


def _precio_medida(pdf, row, size):
    if isinstance(row["precio_num"], (int, float)) and not pd.isna(row["precio_num"]):
        txt = valor(row["precio_num"]); pdf.set_font(FONT, "", size)
    else:
        t = row.get("precio_texto", "")
        txt = "" if pd.isna(t) else " / ".join(str(t).split("\n")).strip()
        pdf.set_font(FONT, "I", max(size - 1.5, 7))
    return txt, (pdf.get_string_width(txt) if txt else 0)


def _dibujar_precio(pdf, x, y, row, size=10.5):
    if isinstance(row["precio_num"], (int, float)) and not pd.isna(row["precio_num"]):
        txt = valor(row["precio_num"])
        pdf.set_font(FONT, "", size); pdf.set_text_color(*PRECIO_GRIS)
    else:
        t = row.get("precio_texto", "")
        txt = "" if pd.isna(t) else " / ".join(str(t).split("\n")).strip()
        pdf.set_font(FONT, "I", max(size - 1.5, 7)); pdf.set_text_color(*NARANJA)
    if not txt:
        return 0
    pdf.set_xy(x, y)
    pdf.cell(pdf.get_string_width(txt) + 2, 5, txt)
    return pdf.get_string_width(txt)


def _puntos_tubo(pdf, x, y, muestra, r=1.5, gap=4.2, con_texto=False):
    cx = x
    for label, color in tubos_de(muestra):
        pdf.set_fill_color(*color)
        pdf.ellipse(cx, y, r * 2, r * 2, style="F")
        if con_texto:
            pdf.set_font(FONT, "", 6.8); pdf.set_text_color(*GRIS_SUAVE)
            pdf.set_xy(cx + r * 2 + 0.8, y - 0.7)
            w = pdf.get_string_width(label) + 3
            pdf.cell(w, 3.5, label)
            cx += r * 2 + 1 + w
        else:
            cx += gap
    return cx - x


def _barra_parametros(pdf, x_der, y, comp, total, total_max, w_max=34):
    """Barra apilada proporcional + total, alineada a la derecha."""
    if not total or not total_max:
        return
    w = w_max * (total / total_max)
    pdf.set_font(FONT, "B", 6.6)
    txt = f"{total} parámetros"
    w_txt = pdf.get_string_width(txt) + 2
    cx = x_der - w_txt - w
    for _, col, n in comp:
        seg = w * n / total
        pdf.set_fill_color(*col)
        pdf.rect(cx, y, seg, 2.6, style="F")
        cx += seg
    pdf.set_xy(cx + 1.5, y - 1.3); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(w_txt, 4, txt)


def _obs_truncada(pdf, obs, disp):
    if disp <= 12 or not obs:
        return ""
    s = "· " + obs
    if pdf.get_string_width(s) <= disp:
        return s
    while len(obs) > 1 and pdf.get_string_width("· " + obs + "…") > disp:
        obs = obs[:-1]
    return "· " + obs + "…" if len(obs) > 1 else ""


def _render_perfiles(pdf, grupo, max_param):
    ML, MR = pdf.ML, pdf.MR
    ancho = MR - ML
    for _, row in grupo.iterrows():
        nombre = str(row["nombre"])
        desc = "" if pd.isna(row.get("descripcion")) else str(row["descripcion"])
        if not desc.strip():   # COMBOS y similares: el contenido está en observaciones
            desc = "" if pd.isna(row.get("observaciones")) else str(row["observaciones"])
        muestra = "" if pd.isna(row.get("muestra")) else str(row["muestra"])
        es_bullets = "•" in desc
        dets = _split_bullets(desc) if es_bullets else []
        flow = "  ·  ".join(dets) if es_bullets else " ".join(desc.split("\n")).strip()
        n_param = total_parametros(dets) if dets else 0

        n_lines = len(pdf._lineas(flow, ancho, "", 8.3)) if flow else 0
        tiene_tubos = bool(tubos_de(muestra))
        h = 7 + n_lines * 4.3 + (5 if (tiene_tubos or n_param) else 0) + 4
        if pdf.get_y() + h > 272:
            pdf.add_page()
        y0 = pdf.get_y()

        pdf.set_xy(ML, y0); pdf.set_font(FONT, "B", 12.5); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(pdf.get_string_width(nombre) + 2, 6, nombre)
        wn = pdf.get_string_width(nombre)
        _dibujar_precio(pdf, ML + wn + 5, y0 + 1.4, row, size=10.5)

        y = y0 + 7.5
        if flow:
            pdf.set_xy(ML, y); pdf.set_font(FONT, "", 8.3); pdf.set_text_color(*GRIS_TXT)
            pdf.multi_cell(ancho, 4.3, flow, align="L")
            y = pdf.get_y()
        y += 1.2
        if tiene_tubos:
            pdf.set_font(FONT, "", 7); pdf.set_text_color(*GRIS_SUAVE)
            pdf.set_xy(ML, y - 0.3); pdf.cell(14, 3.5, "Remitir")
            _puntos_tubo(pdf, ML + 15, y + 0.5, muestra, con_texto=True)
        if n_param:
            _barra_parametros(pdf, MR, y + 0.8, composicion(dets), n_param, max_param)
        if tiene_tubos or n_param:
            y += 5
        pdf.set_draw_color(*TEAL_SUAVE); pdf.set_line_width(0.2)
        pdf.line(ML, y + 1, MR, y + 1)
        pdf.set_y(y + 5)


def _render_detallado(pdf, grupo):
    ML, MR = pdf.ML, pdf.MR
    name_x = ML + 12
    for _, row in grupo.iterrows():
        nombre = str(row["nombre"])
        muestra = "" if pd.isna(row.get("muestra")) else str(row["muestra"])
        obs = "" if pd.isna(row.get("observaciones")) else " ".join(str(row["observaciones"]).split("\n")).strip()

        pdf.set_font(FONT, "B", 9.3)
        w_name = pdf.get_string_width(nombre)
        multilinea = w_name > (MR - name_x - 26)
        _t, w_precio = _precio_medida(pdf, row, 9.3)

        if not multilinea:
            n_lineas, w_last, cabe, h = 1, w_name, True, 7.4
        else:
            lineas = pdf._lineas(nombre, MR - name_x, "B", 9.3)
            n_lineas = len(lineas)
            pdf.set_font(FONT, "B", 9.3)
            w_last = pdf.get_string_width(lineas[-1])
            cabe = (name_x + w_last + 4 + w_precio) <= MR
            h = n_lineas * 5 + (3.4 if cabe else 8.4)

        # ¿la observación entra al lado del precio, o necesita renglón propio?
        sellos = _sellos_de(row)
        w_sellos = 0
        if sellos:
            pdf.set_font(FONT, "B", 5.8)
            w_sellos = sum(pdf.get_string_width(x) + 6.3 for x in sellos)
        x_precio = (name_x + w_last + 4) if cabe else name_x
        obs_inline, n_obs = True, 0
        if obs:
            pdf.set_font(FONT, "I", 7.3)
            disp = MR - (x_precio + w_precio + w_sellos + 6)
            if disp <= 12 or pdf.get_string_width("· " + obs) > disp:
                obs_inline = False
                n_obs = len(pdf._lineas(obs, MR - name_x, "I", 7.3))
                h += n_obs * 3.7 + 1.5

        if pdf.get_y() + h > 275:
            pdf.add_page()
        y0 = pdf.get_y()
        _puntos_tubo(pdf, ML, y0 + 1.8, muestra)
        pdf.set_font(FONT, "B", 9.3); pdf.set_text_color(*GRIS_TXT)
        pdf.set_xy(name_x, y0)
        if not multilinea:
            pdf.cell(w_name + 2, 5.2, nombre)
        else:
            pdf.multi_cell(MR - name_x, 5, nombre, align="L")

        if cabe:
            xp, yp = name_x + w_last + 4, y0 + (n_lineas - 1) * 5
        else:
            xp, yp = name_x, y0 + n_lineas * 5
        wp = _dibujar_precio(pdf, xp, yp + 0.6, row, size=9.3)
        if sellos:
            _dibujar_sellos(pdf, xp + wp + 5, yp + 1.1, sellos)
        x_obs = xp + wp + 5 + (w_sellos + 1 if sellos else 0)
        if obs:
            pdf.set_font(FONT, "I", 7.3); pdf.set_text_color(*GRIS_SUAVE)
            if obs_inline:
                pdf.set_xy(x_obs, yp + 1.0)
                pdf.cell(MR - x_obs, 4, "· " + obs)
            else:
                pdf.set_xy(name_x, yp + 5.4)
                pdf.multi_cell(MR - name_x, 3.7, obs, align="L")
        pdf.set_y(y0 + h)


# ---------------- páginas institucionales ----------------
CAMINO = [
    ((14, 154, 174), "Cargás la remisión en la app",
     "Sin papel: cargás paciente y estudios en dimerolab.com.ar. La muestra viaja "
     "solo con su código de remisión.",
     [("REMISIÓN 100% DIGITAL", (14, 154, 174))], ""),
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
     "WhatsApp y te confirmamos si se puede hacer con la muestra guardada.", ""),
    ((123, 79, 163), "Dejar de pedir aparte lo que ya está incluido",
     "El hemograma ya incluye el recuento de plaquetas al microscopio y la morfología "
     "celular. No hace falta agregarlos ni se cobran por separado.", ""),
]


def _cta(pdf, ML, MR, y, titulo, sub, col=TEAL_OSC, h=13):
    pdf.set_fill_color(*col)
    pdf.rect(ML, y, MR - ML, h, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(ML, y + 1.8); pdf.set_font(FONT, "B", 9.5); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML, 5, titulo, align="C")
    pdf.set_xy(ML, y + 7); pdf.set_font(FONT, "", 8)
    pdf.cell(MR - ML, 4, sub, align="C")


def _qr(pdf, x, y, lado, data, color=(0, 0, 0)):
    """Dibuja un QR (en el A4 impreso el link no se puede tocar)."""
    import qrcode
    from io import BytesIO
    img = qrcode.make(data, box_size=10, border=1).convert("RGB")
    buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    pdf.image(buf, x=x, y=y, w=lado, h=lado)


def _link_whatsapp(cfg, texto=""):
    num = "".join(ch for ch in str(cfg.get("whatsapp", "")) if ch.isdigit())
    base = f"https://wa.me/549{num}" if num else "https://wa.me/"
    if texto:
        from urllib.parse import quote
        base += "?text=" + quote(texto)
    return base


def _pagina_como_leer(pdf):
    """Explica el sistema de lectura del catálogo + QR a la app y a WhatsApp."""
    ML, MR = 16, 194
    pdf.modo_institucional = True
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    cfg = pdf.cfg

    pdf.set_xy(ML, 24); pdf.set_font(DISPLAY, "B", 25); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML, 12, "Cómo leer este catálogo")
    pdf.set_xy(ML, 37); pdf.set_font(FONT, "", 10.5); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 20, 5, "Tres cosas que te van a ahorrar tiempo.", align="L")

    # 1) los puntos de color
    y = 50
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 12); pdf.set_text_color(*TEAL_OSC)
    pdf.cell(MR - ML, 6, "1 · Los puntos de color indican la muestra")
    pdf.set_xy(ML, y + 7); pdf.set_font(FONT, "", 9); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 10, 4.4, "Cada estudio lleva el punto de la muestra en la que "
                                      "hay que remitirlo. Si ves más de un punto, hacen falta "
                                      "todas esas muestras.", align="L")
    y = pdf.get_y() + 3
    col_w = (MR - ML) / 2
    for i, label in enumerate(LEYENDA_TUBOS):
        cx = ML + (i % 2) * col_w
        cy = y + (i // 2) * 6.4
        pdf.set_fill_color(*color_tubo(label))
        pdf.ellipse(cx + 1, cy + 1, 3.4, 3.4, style="F")
        pdf.set_xy(cx + 7, cy); pdf.set_font(FONT, "", 8.6); pdf.set_text_color(*GRIS_TXT)
        pdf.cell(col_w - 8, 5.4, label)
    y += ((len(LEYENDA_TUBOS) + 1) // 2) * 6.4 + 5

    # 2) la barra de parámetros
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 12); pdf.set_text_color(*TEAL_OSC)
    pdf.cell(MR - ML, 6, "2 · En los perfiles, la barra muestra cuánto informa")
    pdf.set_xy(ML, y + 7); pdf.set_font(FONT, "", 9); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 62, 4.4, "No todas las determinaciones pesan igual: un hemograma "
                                      "informa 22 parámetros y una urea, uno. La barra muestra "
                                      "el total y de qué áreas se compone.", align="L")
    ejemplo = [("Hematología", (123, 79, 163), 22), ("Química", (0, 120, 144), 10)]
    bx = MR - 56
    for _, c, n in ejemplo:
        seg = 40 * n / 32
        pdf.set_fill_color(*c); pdf.rect(bx, y + 9, seg, 3.4, style="F")
        bx += seg
    pdf.set_xy(bx + 2, y + 7.6); pdf.set_font(FONT, "B", 8); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(16, 4.4, "32")
    pdf.set_xy(MR - 56, y + 13.5); pdf.set_font(FONT, "I", 6.8); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(56, 3.4, "ejemplo: Perfil general")
    y += 22

    # 3) los sellos
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 12); pdf.set_text_color(*TEAL_OSC)
    pdf.cell(MR - ML, 6, "3 · Los sellos marcan lo que ya está incluido")
    pdf.set_xy(ML, y + 7); pdf.set_font(FONT, "", 9); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 50, 4.4, "Cuando un estudio lleva un sello, eso ya viene adentro: "
                                      "no hace falta pedirlo aparte ni se cobra por separado.", align="L")
    _dibujar_sellos(pdf, MR - 46, y + 8.5, ["YA INCLUIDO"], size=7)
    y = pdf.get_y() + 8

    # QR a la app y a WhatsApp
    pdf.set_fill_color(*TEAL_XSUAVE)
    pdf.rect(ML, y, MR - ML, 46, style="F", round_corners=True, corner_radius=3)
    lado = 30
    _qr(pdf, ML + 8, y + 8, lado, "https://www.dimerolab.com.ar")
    pdf.set_xy(ML + 8 + lado + 5, y + 12); pdf.set_font(FONT, "B", 11)
    pdf.set_text_color(*TEAL_OSC)
    pdf.cell(50, 6, "Pedí tus estudios")
    pdf.set_xy(ML + 8 + lado + 5, y + 19); pdf.set_font(FONT, "", 8.2)
    pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(48, 4, "Escaneá y entrá a la app: remisión, retiro e informes.", align="L")

    x2 = ML + (MR - ML) / 2 + 4
    _qr(pdf, x2, y + 8, lado, _link_whatsapp(cfg, "Hola DimeroLab, quiero hacer una consulta."))
    pdf.set_xy(x2 + lado + 5, y + 12); pdf.set_font(FONT, "B", 11); pdf.set_text_color(*TEAL_OSC)
    pdf.cell(50, 6, "Consultanos")
    pdf.set_xy(x2 + lado + 5, y + 19); pdf.set_font(FONT, "", 8.2); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(46, 4, f"WhatsApp {cfg.get('whatsapp','')}. Dudas, ampliaciones y "
                          f"asesoramiento.", align="L")

    pdf.modo_institucional = False
    pdf.set_auto_page_break(auto=True, margin=18)


def _pagina_cierre(pdf):
    """Última página: invitación a comunicarse, con QR a la app y a WhatsApp."""
    ML, MR = 16, 194
    cfg = pdf.cfg
    pdf.modo_institucional = True
    pdf.set_auto_page_break(auto=False)
    pdf.en_portada = True
    pdf.add_page()
    pdf.paginas_sin_chrome.add(pdf.page_no())   # sin pie: la página ya trae los datos
    pdf.en_portada = False
    col = TEAL_OSC
    pdf.set_fill_color(*col); pdf.rect(0, 0, 210, 297, style="F")
    claro = tuple(min(255, c + 38) for c in col)
    claro2 = tuple(min(255, c + 80) for c in col)
    molecula(pdf, 160, 62, 3.2, [claro, claro2])
    molecula(pdf, 176, 268, 1.7, [claro, claro2])

    logo_b = ASSETS / "logo_blanco.png"
    if logo_b.exists():
        pdf.image(str(logo_b), x=ML, y=26, w=54)

    pdf.set_xy(ML, 108); pdf.set_font(DISPLAY, "B", 29); pdf.set_text_color(*BLANCO)
    pdf.multi_cell(150, 14, "¿Empezamos?", align="L")
    pdf.set_xy(ML, pdf.get_y() + 4); pdf.set_font(FONT, "", 11.5); pdf.set_text_color(*claro2)
    pdf.multi_cell(142, 6, "Cargá tu remisión, pedí el retiro y seguí tus muestras desde "
                           "un mismo lugar. Y si tenés una duda clínica, escribinos: "
                           "miramos el caso y te respondemos.", align="L")

    y = 172
    lado = 32
    pdf.set_fill_color(*claro)
    pdf.rect(ML, y, MR - ML, 52, style="F", round_corners=True, corner_radius=3)
    _qr(pdf, ML + 9, y + 10, lado, "https://www.dimerolab.com.ar")
    pdf.set_xy(ML + 9 + lado + 6, y + 15); pdf.set_font(FONT, "B", 12)
    pdf.set_text_color(*BLANCO); pdf.cell(50, 6, "Pedí tus estudios")
    pdf.set_xy(ML + 9 + lado + 6, y + 23); pdf.set_font(FONT, "", 8.4)
    pdf.multi_cell(46, 4.2, "Escaneá y entrá a la app.", align="L")

    x2 = ML + (MR - ML) / 2 + 4
    _qr(pdf, x2, y + 10, lado, _link_whatsapp(cfg, "Hola DimeroLab, quiero hacer una consulta."))
    pdf.set_xy(x2 + lado + 6, y + 15); pdf.set_font(FONT, "B", 12); pdf.set_text_color(*BLANCO)
    pdf.cell(50, 6, "Consultanos")
    pdf.set_xy(x2 + lado + 6, y + 23); pdf.set_font(FONT, "", 8.4)
    pdf.multi_cell(42, 4.2, f"WhatsApp {cfg.get('whatsapp','')}", align="L")

    # datos al pie
    pdf.set_xy(ML, 252); pdf.set_font(FONT, "B", 10); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML, 5, str(cfg.get("tagline", "Laboratorio Veterinario")))
    pdf.set_xy(ML, 258); pdf.set_font(FONT, "", 8.6); pdf.set_text_color(*claro2)
    pdf.cell(MR - ML, 5, f"{cfg.get('web','')}   ·   {cfg.get('instagram','')}")
    pdf.set_xy(ML, 266); pdf.set_font(FONT, "I", 7.6)
    vig = cfg.get("vigencia", "")
    pdf.cell(MR - ML, 4, f"Valores vigentes al {vig}. Esta lista anula las anteriores." if vig else "")
    pdf.modo_institucional = False
    pdf.set_auto_page_break(auto=True, margin=18)


def _pagina_camino(pdf):
    ML, MR = 16, 194
    pdf.modo_institucional = True
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_xy(ML, 24); pdf.set_font(DISPLAY, "B", 25); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML, 12, "El camino de tu muestra")
    pdf.set_xy(ML, 37); pdf.set_font(FONT, "", 10.5); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 20, 5, "Qué pasa desde que nos la enviás hasta que tenés el "
                                    "resultado — y después también.", align="L")
    x_num, x_txt = ML + 5, ML + 18
    w_txt = MR - x_txt
    y = 47
    for i, (col, titulo, texto, sellos, detalle) in enumerate(CAMINO):
        pdf.set_font(FONT, "", 8.4)
        n1 = len(pdf.multi_cell(w_txt, 4.2, texto, dry_run=True, output="LINES"))
        n2 = 0
        if detalle:
            pdf.set_font(FONT, "", 7.4)
            n2 = len(pdf.multi_cell(w_txt - 4, 3.7, detalle, dry_run=True, output="LINES"))
        h = 6.5 + n1 * 4.2 + 5.6 + (n2 * 3.7 + 1.5 if detalle else 0) + 3
        if i < len(CAMINO) - 1:
            pdf.set_draw_color(*[min(255, c + 130) for c in col]); pdf.set_line_width(0.8)
            pdf.line(x_num, y + 9, x_num, y + h + 2)
        pdf.set_fill_color(*col)
        pdf.ellipse(x_num - 4.2, y - 0.5, 8.4, 8.4, style="F")
        pdf.set_xy(x_num - 4.2, y + 0.9); pdf.set_font(FONT, "B", 8.5); pdf.set_text_color(*BLANCO)
        pdf.cell(8.4, 5, str(i + 1), align="C")
        pdf.set_xy(x_txt, y - 0.5); pdf.set_font(FONT, "B", 11); pdf.set_text_color(*col)
        pdf.cell(w_txt, 6, titulo)
        pdf.set_xy(x_txt, y + 6); pdf.set_font(FONT, "", 8.4); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(w_txt, 4.2, texto, align="L")
        yy = pdf.get_y() + 1.2
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
        if detalle:
            pdf.set_xy(x_txt + 4, yy + 1.5); pdf.set_font(FONT, "", 7.4)
            pdf.set_text_color(*GRIS_SUAVE)
            pdf.multi_cell(w_txt - 4, 3.7, detalle, align="L")
            yy = pdf.get_y()
        y = yy + 1.6
    _cta(pdf, ML, MR, y, "Pedí tus estudios en dimerolab.com.ar",
         f"Consultas y asesoramiento por WhatsApp {pdf.cfg.get('whatsapp','')}")
    pdf.modo_institucional = False
    pdf.set_auto_page_break(auto=True, margin=18)


def _pagina_sabias(pdf):
    ML, MR = 16, 194
    pdf.modo_institucional = True
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_xy(ML, 24); pdf.set_font(DISPLAY, "B", 26); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML, 12, "¿Sabías que podés…?")
    pdf.set_xy(ML, 38); pdf.set_font(FONT, "", 10.5); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 15, 5, "Cosas que ya están disponibles y quizás no estás "
                                    "usando. Todas se hacen desde la app.", align="L")
    y = 54
    for col, titulo, texto, extra in SABIAS:
        pdf.set_font(FONT, "", 9)
        n1 = len(pdf.multi_cell(MR - ML - 22, 4.6, texto, dry_run=True, output="LINES"))
        n2 = 0
        if extra:
            pdf.set_font(FONT, "I", 7.6)
            n2 = len(pdf.multi_cell(MR - ML - 22, 3.8, extra, dry_run=True, output="LINES"))
        h = 11 + n1 * 4.6 + (n2 * 3.8 + 2 if extra else 0) + 7
        pdf.set_fill_color(250, 251, 252)
        pdf.rect(ML, y, MR - ML, h, style="F", round_corners=True, corner_radius=2.5)
        pdf.set_fill_color(*col)
        pdf.rect(ML, y, 3, h, style="F", round_corners=True, corner_radius=1)
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
    _cta(pdf, ML, MR, y + 2, "Todo esto ya está en dimerolab.com.ar",
         f"¿Te ayudamos a empezar? WhatsApp {pdf.cfg.get('whatsapp','')}", h=14)
    pdf.modo_institucional = False
    pdf.set_auto_page_break(auto=True, margin=18)


def _pagina_combinables(pdf, grupo):
    """Reemplaza la tabla críptica '1 química / 2 químicas…' por una página que
    explica el sistema y muestra el ahorro."""
    ML, MR = pdf.ML, pdf.MR
    col = color_area("Químicas Combinables")

    tiers = []
    for _, r in grupo.sort_values("orden").iterrows():
        try:
            cant = int(str(r["nombre"]).split()[0])
        except (ValueError, IndexError):
            continue
        if pd.notna(r["precio_num"]):
            tiers.append((cant, float(r["precio_num"])))
    if not tiers:
        _render_detallado(pdf, grupo)
        return
    t = dict(tiers)
    base = t.get(1, tiers[0][1])
    dets = [x.strip() for x in str(grupo.iloc[0]["muestra"]).split("\n") if x.strip()]

    # título
    y = pdf.get_y()
    pdf.set_xy(ML, y); pdf.set_font(DISPLAY, "B", 21); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML - 44, 11, "Armá tu propio perfil")
    pdf.set_fill_color(*col)
    pdf.rect(MR - 42, y + 1, 42, 8.5, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(MR - 42, y + 1.4); pdf.set_font(FONT, "B", 7.8); pdf.set_text_color(*BLANCO)
    pdf.cell(42, 7.6, "SISTEMA PROPIO", align="C")
    pdf.set_xy(ML, y + 12); pdf.set_font(FONT, "", 9.6); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 45, 4.8, "Elegí solo las determinaciones que tu paciente "
                                      "necesita. Cuantas más combinás, menos te cuesta cada una.")
    y = pdf.get_y() + 4

    # chips de determinaciones
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 7.6); pdf.set_text_color(*col)
    pdf.cell(MR - ML, 4, f"LAS {len(dets)} DETERMINACIONES QUE PODÉS COMBINAR")
    y += 5.5
    cx = ML
    pdf.set_font(FONT, "", 7.4)
    for d in dets:
        w = pdf.get_string_width(d) + 6
        if cx + w > MR:
            cx = ML; y += 6.6
        pdf.set_fill_color(*[min(255, c + 155) for c in col])
        pdf.rect(cx, y, w, 5.4, style="F", round_corners=True, corner_radius=1.6)
        pdf.set_xy(cx, y + 0.1); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(w, 5.2, d, align="C")
        cx += w + 2.4
    y += 12

    # gráfico: precio por determinación
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 7.6); pdf.set_text_color(*col)
    pdf.cell(MR - ML, 4, "CUÁNTO TE SALE CADA DETERMINACIÓN SEGÚN CUÁNTAS COMBINES")
    y += 7
    alto = 38
    pitch = (MR - ML - 4) / len(tiers)
    bw = pitch - 2.2
    max_unit = max(p / c for c, p in tiers)
    base_y = y + alto
    for i, (cant, precio) in enumerate(tiers):
        unit = precio / cant
        h = alto * unit / max_unit
        bx = ML + 2 + i * pitch
        ultimo = (cant == tiers[-1][0])
        pdf.set_fill_color(*((226, 88, 30) if ultimo else col))
        pdf.rect(bx, base_y - h, bw, h, style="F",
                 round_corners=("TOP_LEFT", "TOP_RIGHT"), corner_radius=1)
        pdf.set_xy(bx - 1, base_y + 1); pdf.set_font(FONT, "B", 6.2)
        pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(bw + 2, 3.2, str(cant), align="C")
        if cant in (1, 5, 10, tiers[-1][0]):
            pdf.set_xy(bx - 3, base_y - h - 4.2); pdf.set_font(FONT, "B", 6.2)
            pdf.set_text_color(*((226, 88, 30) if ultimo else GRIS_TXT))
            pdf.cell(bw + 6, 3.2, valor(unit), align="C")
    pdf.set_xy(ML, base_y + 4.5); pdf.set_font(FONT, "I", 6.6); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(70, 3.2, "cantidad de químicas combinadas")
    y = base_y + 11

    # tabla completa de precios (es también la declaración de aranceles)
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 7.6); pdf.set_text_color(*col)
    pdf.cell(MR - ML, 4, "PRECIO TOTAL SEGÚN CUÁNTAS COMBINES")
    y += 5.5
    pdf.set_fill_color(*[min(255, c + 158) for c in col])
    pdf.rect(ML, y, MR - ML, 12, style="F", round_corners=True, corner_radius=1.6)
    for i, (cant, precio) in enumerate(tiers):
        bx = ML + 2 + i * pitch
        pdf.set_xy(bx - 1, y + 1); pdf.set_font(FONT, "", 6.2); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(bw + 2, 3.4, str(cant), align="C")
        pdf.set_xy(bx - 1, y + 5); pdf.set_font(FONT, "B", 7); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(bw + 2, 4, valor(precio), align="C")
    y += 16

    # ejemplos + aclaración
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 10.5); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML, 5.5, "Cada determinación que sumás abarata a todas las demás")
    y += 7
    for texto, cant in [("Urea + Creatinina + Fósforo + Calcio", 4),
                        ("Un perfil bioquímico de 10 determinaciones", 10)]:
        if cant not in t:
            continue
        pdf.set_xy(ML, y); pdf.set_font(FONT, "", 8.2); pdf.set_text_color(*GRIS_TXT)
        pdf.cell(86, 4.4, f"{texto} = {cant} químicas")
        pdf.set_xy(ML + 88, y); pdf.set_font(FONT, "B", 8.2); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(22, 4.4, valor(t[cant]))
        pdf.set_xy(ML + 110, y); pdf.set_font(FONT, "I", 7.6); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(60, 4.4, f"en vez de {valor(base * cant)} por separado")
        y += 5.2
    pdf.set_xy(ML, y + 0.8); pdf.set_font(FONT, "I", 7); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(MR - ML, 3.6,
             "Las bilirrubinas (directa, indirecta y total) cuentan como una sola química.")
    y += 8

    # CTA
    pdf.set_fill_color(*col)
    pdf.rect(ML, y, MR - ML, 11, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(ML, y + 1.2); pdf.set_font(FONT, "B", 8.8); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML, 4.4, "Armá tu perfil y pedilo en dimerolab.com.ar", align="C")
    pdf.set_xy(ML, y + 5.8); pdf.set_font(FONT, "", 7.4)
    pdf.cell(MR - ML, 4, f"¿Dudas sobre qué combinar? WhatsApp {pdf.cfg.get('whatsapp','')}",
             align="C")
    pdf.set_y(y + 14)


def _molecula_al_pie(pdf, seccion):
    """Si la sección terminó dejando mucho aire, llena el hueco con la molécula
    en el color del área. Nunca se dibuja detrás de texto."""
    y = pdf.get_y()
    if y > 215:          # no hay espacio libre suficiente
        return
    col = color_area(seccion)
    # mezcla fija hacia el blanco: queda igual de sutil en cualquier color de área
    tono1 = tuple(int(c + (255 - c) * 0.88) for c in col)
    tono2 = tuple(int(c + (255 - c) * 0.93) for c in col)
    molecula(pdf, 148, 238, 3.4, [tono1, tono2])


def _grupos_ordenados(sub):
    for s in dict.fromkeys(sub["seccion"].tolist()):
        yield s, sub[sub["seccion"] == s].sort_values("orden")


LISTAS_META = {
    "Perfiles": ("Perfiles y búsquedas",
                 "Combinaciones armadas por nuestro equipo para responder las preguntas "
                 "clínicas más frecuentes, con el mejor rendimiento por muestra.",
                 (0, 96, 120)),
    "Detallado": ("Estudios individuales",
                  "Todas las determinaciones disponibles, organizadas por área. "
                  "Los puntos de color indican el tubo en el que hay que remitir.",
                  (0, 120, 144)),
}


def construir_pdf(est, cfg, salida=None, listas=("Perfiles", "Detallado"),
                  incluir_folleto=False, incluir_institucional=True):
    """Genera el catálogo. Solo imprime estudios con activo == 'SI'."""
    est = est.copy()
    est = est[est["activo"].astype(str).str.upper().str.strip() == "SI"]
    est = est.sort_values("orden")

    pdf = DimeroPDF(cfg)
    # el índice de uña solo muestra las secciones que realmente se imprimen
    pdf.tabs = [s for s in dict.fromkeys(
        est[est["lista"].isin(listas)].sort_values("orden")["seccion"].tolist()) if s]
    if incluir_folleto:
        from folleto import agregar_folleto
        pdf.folleto_pages = 1   # solo la portada
        # las áreas salen del catálogo real: la portada no puede quedar desfasada
        n_est = len(est[est["lista"].isin(listas)])
        n_sec = len({s for s in est[est["lista"].isin(listas)]["seccion"] if s})
        agregar_folleto(pdf, cfg, f"{n_est} estudios en {n_sec} secciones")

    if incluir_institucional:
        _pagina_camino(pdf)
        _pagina_sabias(pdf)
        _pagina_como_leer(pdf)

    for lista in listas:
        sub = est[est["lista"] == lista]
        if sub.empty:
            continue
        titulo, bajada, col = LISTAS_META.get(lista, (lista, "", TEAL))
        primera = next(iter(dict.fromkeys(sub["seccion"].tolist())), None)
        pdf.seccion_actual = primera
        portada_lista(pdf, titulo, bajada, len(sub), col)

        # máximo de parámetros para escalar las barras dentro de la lista
        max_param = 1
        if lista == "Perfiles":
            for _, r in sub.iterrows():
                d = _split_bullets(r.get("descripcion", "") or "")
                if "•" in str(r.get("descripcion", "")):
                    max_param = max(max_param, total_parametros(d))

        pdf.add_page()
        _leyenda_tubos(pdf)
        for i, (seccion, grupo) in enumerate(_grupos_ordenados(sub)):
            pdf.seccion_actual = seccion
            if i > 0:
                pdf.add_page()   # cada sección arranca en página nueva
            _seccion(pdf, seccion)
            if seccion == "Químicas Combinables":
                _pagina_combinables(pdf, grupo)
            elif lista == "Perfiles":
                _render_perfiles(pdf, grupo, max_param)
            else:
                _render_detallado(pdf, grupo)
            _molecula_al_pie(pdf, seccion)

    if incluir_institucional:
        _pagina_cierre(pdf)

    data = bytes(pdf.output())
    if salida is not None:
        Path(salida).write_bytes(data)
    return data


if __name__ == "__main__":
    est, cfg = cargar_datos(BASE / "data" / "estudios.xlsx")
    salida = BASE / "Catalogo_DimeroLab.pdf"
    construir_pdf(est, cfg, salida, incluir_folleto=True)
    print("PDF generado:", salida)

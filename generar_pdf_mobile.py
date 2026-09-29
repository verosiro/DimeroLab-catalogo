#!/usr/bin/env python3
"""
Versión CELULAR del catálogo DimeroLab.

Pensada para leerse en el teléfono (que es donde realmente se abre un PDF que
llega por WhatsApp): página angosta, una sola columna, tipografía grande y
botones tocables a la app y a WhatsApp en vez de códigos QR.

Reusa los datos, la paleta y el sistema de puntos de `generar_pdf`.
"""
from pathlib import Path
import pandas as pd
from fpdf import FPDF

import generar_pdf as G
from generar_pdf import (FONT, DISPLAY, BLANCO, GRIS_TXT, GRIS_SUAVE, NEGRO_SUAVE, PRECIO_GRIS,
                         TEAL_OSC, color_area, label_area, tubos_de, color_tubo,
                         LEYENDA_TUBOS, valor, _split_bullets, total_parametros,
                         composicion, _sellos_de, SELLO_COLORES, NOTAS_SECCION,
                         LISTAS_META, cargar_datos, ASSETS)

# formato tipo teléfono (relación ~9:16)
W, H = 95.0, 169.0
ML, MR = 7.0, 88.0


def _link_whatsapp(cfg, texto=""):
    num = "".join(ch for ch in str(cfg.get("whatsapp", "")) if ch.isdigit())
    base = f"https://wa.me/549{num}" if num else "https://wa.me/"
    if texto:
        from urllib.parse import quote
        base += "?text=" + quote(texto)
    return base


class MobilePDF(FPDF):
    def __init__(self, cfg):
        super().__init__(orientation="P", unit="mm", format=(W, H))
        self.cfg = cfg
        self.set_auto_page_break(auto=True, margin=11)
        self.set_margins(ML, 8, W - MR)
        self.add_font(FONT, "", str(ASSETS / "DejaVuSans.ttf"))
        self.add_font(FONT, "B", str(ASSETS / "DejaVuSans-Bold.ttf"))
        self.add_font(FONT, "I", str(ASSETS / "DejaVuSans-Oblique.ttf"))
        self.add_font(DISPLAY, "", str(ASSETS / "Poppins-Regular.ttf"))
        self.add_font(DISPLAY, "B", str(ASSETS / "Poppins-Bold.ttf"))
        self.seccion_actual = None
        self.en_portada = False
        self.portadas = set()

    def header(self):
        if self.en_portada or self.page_no() in self.portadas:
            return
        col = color_area(self.seccion_actual) if self.seccion_actual else TEAL_OSC
        self.set_fill_color(*col)
        self.rect(0, 0, W, 2.4, style="F")
        if self.seccion_actual:
            icono = ASSETS / "logo_solo.png"
            x_txt = ML
            if icono.exists():
                self.image(str(icono), x=ML, y=4.4, w=5.2)
                x_txt = ML + 7
            self.set_xy(x_txt, 4.5); self.set_font(FONT, "B", 7.4); self.set_text_color(*col)
            self.cell(MR - x_txt, 4, label_area(self.seccion_actual).upper())
        self.set_y(11 if self.seccion_actual else 7)

    def footer(self):
        if self.page_no() in self.portadas:
            return
        self.set_y(-8)
        self.set_font(FONT, "", 5.8); self.set_text_color(*GRIS_SUAVE)
        self.cell(0, 4, "dimerolab.com.ar", align="L",
                  link="https://www.dimerolab.com.ar")
        self.cell(0, 4, str(self.page_no()), align="R")

    def _lineas(self, texto, w, style="", size=8):
        self.set_font(FONT, style, size)
        return self.multi_cell(w, 4, str(texto), dry_run=True, output="LINES")


def _boton(pdf, y, texto, link, col=TEAL_OSC, h=8.5):
    """Botón tocable (en el celular el PDF abre el link directo)."""
    pdf.set_fill_color(*col)
    pdf.rect(ML, y, MR - ML, h, style="F", round_corners=True, corner_radius=2)
    pdf.set_xy(ML, y + 0.4); pdf.set_font(FONT, "B", 7.6); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML, h - 0.8, texto, align="C", link=link)
    return y + h + 2.5


def _portada(pdf, cfg):
    pdf.en_portada = True
    pdf.add_page()
    pdf.portadas.add(pdf.page_no())
    pdf.en_portada = False
    col = TEAL_OSC
    pdf.set_fill_color(*col); pdf.rect(0, 0, W, H, style="F")
    claro = tuple(min(255, c + 45) for c in col)
    claro2 = tuple(min(255, c + 90) for c in col)
    for dx, dy, r in [(0, 0, 9), (11, -7, 6), (8, 9, 5), (-10, 6, 4)]:
        pdf.set_fill_color(*(claro if r > 5 else claro2))
        d = r * 1.5
        pdf.ellipse(70 + dx * 1.5 - d / 2, 30 + dy * 1.5 - d / 2, d, d, style="F")
    # sobre fondo oscuro va la versión blanca (el teal del logo se pierde)
    logo = ASSETS / "logo_blanco.png"
    if not logo.exists():
        logo = ASSETS / "logo_dimero.png"
    pdf.image(str(logo), x=ML, y=62, w=58)
    pdf.set_xy(ML, 84); pdf.set_font(DISPLAY, "B", 14); pdf.set_text_color(*BLANCO)
    pdf.multi_cell(MR - ML, 7, "Catálogo de servicios", align="L")
    pdf.set_xy(ML, pdf.get_y() + 2); pdf.set_font(FONT, "", 8); pdf.set_text_color(*claro2)
    pdf.multi_cell(MR - ML, 4.2, str(cfg.get("subtitulo", "")) + " · Vigencia " +
                   str(cfg.get("vigencia", "")), align="L")
    y = 128
    y = _boton(pdf, y, "Pedí tus estudios en la app", "https://www.dimerolab.com.ar",
               col=(14, 154, 174))
    _boton(pdf, y, "Consultanos por WhatsApp",
           _link_whatsapp(cfg, "Hola DimeroLab, quiero hacer una consulta."),
           col=(46, 155, 143))


def _portada_lista(pdf, titulo, bajada, n, col):
    pdf.en_portada = True
    pdf.add_page()
    pdf.portadas.add(pdf.page_no())
    pdf.en_portada = False
    pdf.set_fill_color(*col); pdf.rect(0, 0, W, H, style="F")
    claro2 = tuple(min(255, c + 85) for c in col)
    pdf.set_xy(ML, 52); pdf.set_font(FONT, "B", 6.6); pdf.set_text_color(*claro2)
    pdf.cell(MR - ML, 4, "CATÁLOGO DE SERVICIOS")
    pdf.set_xy(ML, 58); pdf.set_font(DISPLAY, "B", 18); pdf.set_text_color(*BLANCO)
    pdf.multi_cell(MR - ML, 9, titulo, align="L")
    pdf.set_xy(ML, pdf.get_y() + 2); pdf.set_font(FONT, "", 7.6); pdf.set_text_color(*claro2)
    pdf.multi_cell(MR - ML, 4, bajada, align="L")
    pdf.set_xy(ML, H - 24); pdf.set_font(FONT, "B", 10); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML, 6, f"{n} estudios")


def _seccion(pdf, titulo):
    col = color_area(titulo)
    y = pdf.get_y()
    pdf.set_xy(ML + 4.5, y - 0.5); pdf.set_font(DISPLAY, "B", 9.6); pdf.set_text_color(*col)
    pdf.multi_cell(MR - ML - 4.5, 5.5, str(titulo), align="L")
    y_fin = pdf.get_y()
    # la píldora acompaña al alto real del título (puede ocupar 2 renglones)
    pdf.set_fill_color(*col)
    pdf.rect(ML, y + 0.6, 2.2, max(y_fin - y - 1.4, 5), style="F",
             round_corners=True, corner_radius=0.8)
    y = y_fin + 1.6
    pdf.set_draw_color(*[min(255, c + 130) for c in col]); pdf.set_line_width(0.4)
    pdf.line(ML, y, MR, y)
    pdf.set_y(y + 2.5)
    nota = NOTAS_SECCION.get(str(titulo).strip())
    if nota:
        pdf.set_xy(ML, pdf.get_y()); pdf.set_font(FONT, "I", 6.2)
        pdf.set_text_color(*GRIS_SUAVE)
        pdf.multi_cell(MR - ML, 3.2, nota, align="L")
        pdf.set_y(pdf.get_y() + 1.5)


def _puntos(pdf, x, y, muestra, con_texto=True, r=1.2):
    tubos = tubos_de(muestra)
    # igual que en el A4: la "o" avisa que alcanza con una de las muestras
    alternativas = len(tubos) > 1 and G.relacion_tubos(muestra) == "o"
    cx = x
    for i, (label, color) in enumerate(tubos):
        if i and alternativas:
            pdf.set_font(FONT, "I", 5.2); pdf.set_text_color(*GRIS_SUAVE)
            pdf.set_xy(cx - 0.3, y - 1.0)
            w_o = pdf.get_string_width("o") + 1.4
            pdf.cell(w_o, 3, "o", align="C")
            cx += w_o
        pdf.set_fill_color(*color)
        pdf.ellipse(cx, y, r * 2, r * 2, style="F")
        if con_texto:
            pdf.set_font(FONT, "", 5.6); pdf.set_text_color(*GRIS_SUAVE)
            pdf.set_xy(cx + r * 2 + 0.6, y - 0.8)
            w = pdf.get_string_width(label) + 2.4
            pdf.cell(w, 3, label)
            cx += r * 2 + 0.8 + w
        else:
            cx += r * 2 + 1.6
    return cx - x


def _combinables_mobile(pdf, grupo):
    """Versión resumida de 'Armá tu propio perfil' para el celular."""
    col = color_area("Químicas Combinables")
    tiers = []
    for _, r in grupo.sort_values("orden").iterrows():
        try:
            c = int(str(r["nombre"]).split()[0])
        except (ValueError, IndexError):
            continue
        if pd.notna(r["precio_num"]):
            tiers.append((c, float(r["precio_num"])))
    if not tiers:
        for _, row in grupo.iterrows():
            _item(pdf, row)
        return
    t = dict(tiers); base = t.get(1, tiers[0][1])

    y = pdf.get_y()
    pdf.set_xy(ML, y); pdf.set_font(DISPLAY, "B", 10.6); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.multi_cell(MR - ML, 5.4, "Armá tu propio perfil", align="L")
    pdf.set_xy(ML, pdf.get_y() + 0.5); pdf.set_font(FONT, "", 7); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML, 3.6, "Elegí solo las determinaciones que necesitás: cuantas "
                                 "más combinás, menos cuesta cada una.", align="L")
    y = pdf.get_y() + 2

    # gráfico compacto de precio por determinación
    alto, pitch = 20, (MR - ML) / len(tiers)
    bw = pitch - 0.9
    max_unit = max(p / c for c, p in tiers)
    base_y = y + alto
    for i, (cant, precio) in enumerate(tiers):
        h = alto * (precio / cant) / max_unit
        bx = ML + i * pitch
        ultimo = cant == tiers[-1][0]
        pdf.set_fill_color(*((226, 88, 30) if ultimo else col))
        pdf.rect(bx, base_y - h, bw, h, style="F")
    pdf.set_xy(ML, base_y + 0.8); pdf.set_font(FONT, "", 5.6); pdf.set_text_color(*GRIS_SUAVE)
    pdf.cell(30, 3, f"1 química: {valor(base)}")
    pdf.set_xy(MR - 34, base_y + 0.8)
    pdf.cell(34, 3, f"{tiers[-1][0]} químicas: {valor(tiers[-1][1] / tiers[-1][0])} c/u", align="R")
    y = base_y + 6

    # tabla compacta de precios totales (3 columnas)
    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 6.4); pdf.set_text_color(*col)
    pdf.cell(MR - ML, 3.6, "PRECIO TOTAL")
    y += 4.5
    colw = (MR - ML) / 3
    for i, (cant, precio) in enumerate(tiers):
        cx = ML + (i % 3) * colw
        cy = y + (i // 3) * 4.4
        pdf.set_xy(cx, cy); pdf.set_font(FONT, "", 6.6); pdf.set_text_color(*GRIS_SUAVE)
        pdf.cell(9, 3.6, str(cant))
        pdf.set_xy(cx + 9, cy); pdf.set_font(FONT, "B", 6.8); pdf.set_text_color(*NEGRO_SUAVE)
        pdf.cell(colw - 10, 3.6, valor(precio))
    y += ((len(tiers) + 2) // 3) * 4.4 + 2

    pdf.set_xy(ML, y); pdf.set_font(FONT, "I", 6); pdf.set_text_color(*GRIS_SUAVE)
    pdf.multi_cell(MR - ML, 3.2, "Las bilirrubinas (directa, indirecta y total) cuentan "
                                 "como una sola química.", align="L")
    y = pdf.get_y() + 1
    _puntos(pdf, ML, y + 0.6, "Tubo seco/con gel")
    pdf.set_y(y + 5)


def _molecula_al_pie(pdf, seccion):
    """Llena el hueco de las secciones cortas, nunca detrás del texto."""
    if pdf.get_y() > 118:
        return
    col = color_area(seccion)
    t1 = tuple(int(c + (255 - c) * 0.88) for c in col)
    t2 = tuple(int(c + (255 - c) * 0.93) for c in col)
    for i, (dx, dy, r) in enumerate([(0, 0, 9), (11, -7, 6), (8, 9, 5), (-10, 6, 4)]):
        pdf.set_fill_color(*(t1 if i % 2 == 0 else t2))
        d = r * 1.5
        pdf.ellipse(62 + dx * 1.5 - d / 2, 140 + dy * 1.5 - d / 2, d, d, style="F")


def _precio_txt(row):
    if isinstance(row["precio_num"], (int, float)) and not pd.isna(row["precio_num"]):
        return valor(row["precio_num"]), False
    t = row.get("precio_texto", "")
    return ("" if pd.isna(t) else " / ".join(str(t).split("\n")).strip()), True


def _item(pdf, row, es_perfil=False, max_param=1):
    nombre = str(row["nombre"])
    muestra = "" if pd.isna(row.get("muestra")) else str(row["muestra"])
    obs = "" if pd.isna(row.get("observaciones")) else " ".join(str(row["observaciones"]).split("\n")).strip()
    desc = "" if pd.isna(row.get("descripcion")) else str(row["descripcion"])
    if es_perfil and not desc.strip():
        desc, obs = obs, ""
    dets = _split_bullets(desc) if "•" in desc else []
    flow = "  ·  ".join(dets) if dets else " ".join(desc.split("\n")).strip()
    sellos = _sellos_de(row)
    precio, es_texto = _precio_txt(row)

    n_nom = len(pdf._lineas(nombre, MR - ML, "B", 8.6))
    n_flow = len(pdf._lineas(flow, MR - ML, "", 6.6)) if (es_perfil and flow) else 0
    n_obs = len(pdf._lineas(obs, MR - ML, "I", 6.2)) if obs else 0
    h = n_nom * 4.3 + 4.6 + n_flow * 3.2 + n_obs * 3.1 + (4 if tubos_de(muestra) else 0) + 3.5
    if pdf.get_y() + h > H - 13:
        pdf.add_page()
    y = pdf.get_y()

    pdf.set_xy(ML, y); pdf.set_font(FONT, "B", 8.6); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.multi_cell(MR - ML, 4.3, nombre, align="L")
    y = pdf.get_y() + 0.3

    # precio + sello en la misma línea
    pdf.set_font(FONT, "I" if es_texto else "", 8.4)
    pdf.set_text_color(*((226, 88, 30) if es_texto else PRECIO_GRIS))
    pdf.set_xy(ML, y); pdf.cell(pdf.get_string_width(precio) + 2, 4.2, precio)
    cx = ML + pdf.get_string_width(precio) + 4
    for etq in sellos:
        col = SELLO_COLORES.get(etq.upper(), TEAL_OSC)
        pdf.set_font(FONT, "B", 5.2)
        w = pdf.get_string_width(etq) + 3.6
        pdf.set_fill_color(*col)
        pdf.rect(cx, y + 0.3, w, 3.4, style="F", round_corners=True, corner_radius=1)
        pdf.set_xy(cx, y + 0.35); pdf.set_text_color(*BLANCO)
        pdf.cell(w, 3.3, etq, align="C")
        cx += w + 1.4
    # barra de parámetros (perfiles)
    if es_perfil and dets:
        n_par = total_parametros(dets)
        wmax = 26
        wbar = wmax * n_par / max(max_param, 1)
        bx = MR - wbar - 9
        for _, c, n in composicion(dets):
            seg = wbar * n / n_par
            pdf.set_fill_color(*c); pdf.rect(bx, y + 1.2, seg, 1.9, style="F")
            bx += seg
        pdf.set_xy(MR - 8.5, y - 0.2); pdf.set_font(FONT, "B", 5.4)
        pdf.set_text_color(*GRIS_SUAVE); pdf.cell(8.5, 4, str(n_par), align="R")
    y += 4.8

    if es_perfil and flow:
        pdf.set_xy(ML, y); pdf.set_font(FONT, "", 6.6); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(MR - ML, 3.2, flow, align="L")
        y = pdf.get_y() + 0.4
    if obs:
        pdf.set_xy(ML, y); pdf.set_font(FONT, "I", 6.2); pdf.set_text_color(*GRIS_SUAVE)
        pdf.multi_cell(MR - ML, 3.1, obs, align="L")
        y = pdf.get_y() + 0.4
    if tubos_de(muestra):
        _puntos(pdf, ML, y + 0.6, muestra)
        y += 4
    pdf.set_draw_color(238, 243, 245); pdf.set_line_width(0.2)
    pdf.line(ML, y + 1, MR, y + 1)
    pdf.set_y(y + 3.2)


def construir_pdf_mobile(est, cfg, salida=None, listas=("Perfiles", "Detallado")):
    est = est.copy()
    est = est[est["activo"].astype(str).str.upper().str.strip() == "SI"].sort_values("orden")
    pdf = MobilePDF(cfg)
    _portada(pdf, cfg)

    # leyenda de muestras
    pdf.seccion_actual = None
    pdf.add_page()
    pdf.set_xy(ML, 12); pdf.set_font(DISPLAY, "B", 9.8); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.cell(MR - ML, 6, "Cómo leer esta guía")
    y = 22
    pdf.set_xy(ML, y); pdf.set_font(FONT, "", 7); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML, 3.6, "El punto de color indica en qué muestra remitir "
                                 "el estudio. Si hay varios puntos hacen falta todas "
                                 "esas muestras; si entre ellos dice “o”, alcanza "
                                 "con una cualquiera.", align="L")
    y = pdf.get_y() + 2
    for label in LEYENDA_TUBOS:
        pdf.set_fill_color(*color_tubo(label))
        pdf.ellipse(ML, y + 0.6, 2.6, 2.6, style="F")
        pdf.set_xy(ML + 4.5, y - 0.3); pdf.set_font(FONT, "", 7); pdf.set_text_color(*GRIS_TXT)
        pdf.cell(MR - ML, 3.8, label)
        y += 4.6
    y += 2
    pdf.set_xy(ML, y); pdf.set_font(FONT, "", 7); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML, 3.6, "Los precios están en pesos, con IVA incluido. "
                                 "En los perfiles, la barra de color muestra cuántos "
                                 "parámetros informa cada uno.", align="L")
    y = _boton(pdf, pdf.get_y() + 4, "Abrir la app", "https://www.dimerolab.com.ar",
               col=(14, 154, 174))
    _boton(pdf, y, "Consultar por WhatsApp",
           _link_whatsapp(cfg, "Hola DimeroLab, quiero hacer una consulta."),
           col=(46, 155, 143))

    for lista in listas:
        sub = est[est["lista"] == lista]
        if sub.empty:
            continue
        titulo, bajada, col = LISTAS_META.get(lista, (lista, "", TEAL_OSC))
        secs = list(dict.fromkeys(sub["seccion"].tolist()))
        pdf.seccion_actual = secs[0] if secs else None
        _portada_lista(pdf, titulo, bajada, len(sub), col)

        max_param = 1
        if lista == "Perfiles":
            for _, r in sub.iterrows():
                if "•" in str(r.get("descripcion", "")):
                    max_param = max(max_param, total_parametros(_split_bullets(r["descripcion"])))

        for i, seccion in enumerate(secs):
            grupo = sub[sub["seccion"] == seccion].sort_values("orden")
            pdf.seccion_actual = seccion
            pdf.add_page()
            _seccion(pdf, seccion)
            if seccion == "Químicas Combinables":
                _combinables_mobile(pdf, grupo)
            else:
                for _, row in grupo.iterrows():
                    _item(pdf, row, es_perfil=(lista == "Perfiles"), max_param=max_param)
            _molecula_al_pie(pdf, seccion)

    # cierre
    pdf.seccion_actual = None
    pdf.add_page()
    pdf.set_xy(ML, 30); pdf.set_font(DISPLAY, "B", 12.5); pdf.set_text_color(*NEGRO_SUAVE)
    pdf.multi_cell(MR - ML, 6.5, "¿Empezamos?", align="L")
    pdf.set_xy(ML, pdf.get_y() + 2); pdf.set_font(FONT, "", 7.6); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML, 4, "Cargá tu remisión, pedí el retiro y seguí tus muestras "
                               "desde un mismo lugar.", align="L")
    y = _boton(pdf, pdf.get_y() + 5, "Ir a la app", "https://www.dimerolab.com.ar",
               col=(14, 154, 174))
    _boton(pdf, y, "Escribinos por WhatsApp",
           _link_whatsapp(cfg, "Hola DimeroLab, quiero empezar a trabajar con ustedes."),
           col=(46, 155, 143))

    data = bytes(pdf.output())
    if salida is not None:
        Path(salida).write_bytes(data)
    return data


if __name__ == "__main__":
    est, cfg = cargar_datos(Path(__file__).parent / "data" / "estudios.xlsx")
    out = Path(__file__).parent / G.nombre_archivo(cfg, "celular")
    construir_pdf_mobile(est, cfg, out)
    print("PDF celular generado:", out)

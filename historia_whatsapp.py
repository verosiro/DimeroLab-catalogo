#!/usr/bin/env python3
"""
Historia (estado) de WhatsApp anunciando el catálogo.

Formato 9:16 para que entre completa sin recortes. Usa la misma tipografía y
la misma paleta que el catálogo: si la pieza no se parece al PDF que van a
recibir, el anuncio y el producto se leen como dos cosas distintas.

Uso:  python3 historia_whatsapp.py
Sale: Historia DimeroLab <mes> <año>.png  (1080x1920)
"""
from pathlib import Path
import fitz
from fpdf import FPDF

from generar_pdf import (ASSETS, FONT, DISPLAY, BLANCO, NARANJA, TEAL, TEAL_OSC,
                         cargar_datos, periodo_vigencia, molecula)

BASE = Path(__file__).parent
W, H = 90.0, 160.0          # 9:16
ML = 10.0
ANCHO = W - ML * 2

# El texto, acá arriba para que sea fácil cambiarlo sin tocar el dibujo.
TITULO = "Catálogo|de servicios"     # el "|" marca el quiebre de renglón
CUERPO = ("215 estudios: qué incluye cada uno, "
          "en qué tubo va y cuánto sale.")
CIERRE = "¿No te llegó?"
CTA = "Respondé este estado\ny te lo mandamos."


class Historia(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format=(W, H))
        self.add_font(FONT, "", str(ASSETS / "DejaVuSans.ttf"))
        self.add_font(FONT, "B", str(ASSETS / "DejaVuSans-Bold.ttf"))
        self.add_font(DISPLAY, "B", str(ASSETS / "Poppins-Bold.ttf"))
        self.add_font(DISPLAY, "", str(ASSETS / "Poppins-Regular.ttf"))


def construir(cfg, salida_png):
    periodo = periodo_vigencia(cfg).title()

    pdf = Historia()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # fondo teal oscuro: el catálogo abre igual, así se reconoce de una
    pdf.set_fill_color(*TEAL_OSC)
    pdf.rect(0, 0, W, H, style="F")

    # molécula al pie, en tonos apenas más claros que el fondo (como en la portada)
    molecula(pdf, 70, 132, 0.62, [(12, 110, 134), (10, 104, 128), (16, 120, 144)])

    # Logo bajo el 12% de la altura: arriba van el reloj del sistema y el nombre
    # de quien publica, que tapan esa franja.
    logo = ASSETS / "logo_blanco.png"
    if logo.exists():
        pdf.image(str(logo), x=ML, y=H * 0.125, w=34)

    # titular
    y = 42
    pdf.set_text_color(*BLANCO)
    pdf.set_font(DISPLAY, "B", 21)
    for linea in TITULO.split("|"):
        pdf.set_xy(ML, y)
        pdf.cell(ANCHO, 10, linea)
        y += 10.5

    # el período, en naranja: es el dato que dice "esto es lo nuevo"
    pdf.set_xy(ML, y + 2)
    pdf.set_font(DISPLAY, "B", 12)
    pdf.set_text_color(*NARANJA)
    pdf.cell(ANCHO, 7, periodo)

    # regla
    y += 14
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.8)
    pdf.line(ML, y, ML + 16, y)

    # cuerpo
    pdf.set_xy(ML, y + 6)
    pdf.set_font(FONT, "", 9.4)
    pdf.set_text_color(235, 245, 247)
    pdf.multi_cell(ANCHO - 4, 5.4, CUERPO, align="L")

    # Cierre y llamada a la acción. Van después del cuerpo, no en una coordenada
    # fija: si el texto de arriba crece, esto baja en vez de pisarse.
    y = pdf.get_y() + 11
    pdf.set_xy(ML, y)
    pdf.set_font(DISPLAY, "B", 11)
    pdf.set_text_color(*BLANCO)
    pdf.cell(ANCHO, 6, CIERRE)

    pdf.set_xy(ML, y + 9)
    pdf.set_font(FONT, "B", 10)
    pdf.set_text_color(*NARANJA)
    pdf.multi_cell(ANCHO, 5.6, CTA, align="L")

    # Pie: separado del cierre, pero arriba del 88% de la altura, porque WhatsApp
    # tapa la franja de abajo con la barra de "Responder" y ahí no se lee nada.
    pdf.set_xy(ML, min(max(pdf.get_y() + 9, H * 0.80), H * 0.87))
    pdf.set_font(FONT, "", 7.4)
    pdf.set_text_color(150, 200, 210)
    pdf.cell(ANCHO, 4, "dimerolab.com.ar")

    tmp = BASE / "_historia_tmp.pdf"
    pdf.output(str(tmp))
    doc = fitz.open(tmp)
    # 1080 px de ancho sobre 90 mm
    doc[0].get_pixmap(dpi=round(1080 / (W / 25.4))).save(salida_png)
    doc.close()
    tmp.unlink()
    return salida_png


if __name__ == "__main__":
    est, cfg = cargar_datos(BASE / "data" / "estudios.xlsx")
    out = BASE / f"Historia DimeroLab {periodo_vigencia(cfg)}.png"
    construir(cfg, out)
    print("Historia generada:", out)

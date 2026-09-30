#!/usr/bin/env python3
"""
Propuesta para clínicas con internación (2 páginas A4).

Genérica y reutilizable: no lleva el nombre de la clínica impreso, así sirve
para la próxima. Si querés personalizarla, completá DESTINATARIO.

El ángulo: un paciente internado se controla varias veces por día, así que el
laboratorio tiene que poder seguir ese ritmo. Todo lo demás cuelga de ahí.

>>> TODO EL TEXTO ES EDITABLE ACÁ ABAJO <<<

Uso:  python3 propuesta_internacion.py
"""
from pathlib import Path
from fpdf import FPDF

from generar_pdf import (ASSETS, FONT, DISPLAY, BLANCO, GRIS_TXT, GRIS_SUAVE,
                         NEGRO_SUAVE, NARANJA, TEAL, TEAL_OSC, molecula,
                         cargar_datos, periodo_vigencia)

BASE = Path(__file__).parent
ML, MR = 16, 194

# Dejalo vacío para la versión genérica, o poné el nombre de la clínica.
DESTINATARIO = ""

TITULO = "Cuando el paciente|no se va a su casa"
BAJADA = ("Un internado se controla varias veces por día. El laboratorio tiene "
          "que poder seguir ese ritmo, y para eso hay cosas que no aparecen en "
          "el catálogo general.")

# (color, título, texto)
INTERNACION = [
    ((14, 154, 174), "Los retiros los pedís vos, cuando los necesitás",
     "No hay un horario único de paso. Solicitás el retiro desde la misma app donde "
     "cargaste la remisión, logística lo coordina y ves el estado en esa misma "
     "pantalla: sabés si ya está coordinado o si la moto ya pasó, sin llamar a "
     "preguntar. Para una internación eso significa mandar la muestra cuando el "
     "paciente lo pide, no cuando al laboratorio le queda cómodo."),
    ((226, 88, 30), "Marcás el protocolo como internación y sale en el día",
     "Las muestras de pacientes internados entran con prioridad: se procesan y se "
     "informan dentro de la misma jornada, siempre que lleguen dentro del horario "
     "de procesamiento. Coordinalo por WhatsApp y te confirmamos."),
    ((46, 155, 143), "Ampliás estudios sin volver a pinchar al paciente",
     "Guardamos todas las muestras: 10 días en heladera y un mes en freezer. Si la "
     "evolución pide otra determinación, consultanos por WhatsApp y te confirmamos "
     "si se puede hacer con la muestra que ya tenemos. En un paciente al que ya le "
     "sacaste sangre tres veces, esto se nota."),
]

TITULO_2 = "Y además, todo esto"
BAJADA_2 = ("Vale para cualquier cliente, pero en internación pesa más: hay varios "
            "profesionales, turnos que rotan y decisiones que no esperan.")

SISTEMA = [
    ((123, 79, 163), "Un grupo de WhatsApp para tu equipo",
     "Si en la clínica trabajan varios profesionales armamos un grupo. Antes de "
     "responder una consulta revisamos el informe y nos interiorizamos en el caso: "
     "no contestamos de memoria."),
    ((48, 140, 220), "El informe le llega a quien tiene que llegar",
     "Cargás uno o más mails en el protocolo y el informe se envía solo apenas está "
     "listo. Con turnos rotativos, el que entra lo encuentra sin tener que pedirlo. "
     "También podés cargar el mail del tutor y evitarte reenviar nada."),
    ((0, 140, 155), "Garantía de muestra",
     "Si la muestra no permite procesar el estudio —insuficiente, suero lipémico o "
     "muy hemolizado, un tubo coagulado— el estudio queda pendiente y lo repetimos "
     "sin cargo cuando nos envíen material nuevo, coordinando por WhatsApp."),
    ((214, 72, 74), "Todos los hemogramas los mira un profesional al microscopio",
     "El recuento de plaquetas se corrobora al microscopio y la fórmula leucocitaria "
     "se hace por microscopía, informando formas inmaduras. En un internado, "
     "distinguir una plaquetopenia real de un artefacto por agregados cambia la "
     "conducta."),
    ((140, 110, 60), "Calidad verificada por terceros",
     "Además de los controles internos de rutina del laboratorio, participamos de un "
     "programa externo de control de calidad: nuestros resultados se comparan "
     "periódicamente con los de otros laboratorios del país."),
]

CIERRE = ("Todas estas soluciones las fuimos construyendo a base de problemas que "
          "veíamos o que nos contaban que tenían nuestros clientes. Un poco ese "
          "siempre es el foco.")


class Propuesta(FPDF):
    def __init__(self, cfg):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.cfg = cfg
        self.add_font(FONT, "", str(ASSETS / "DejaVuSans.ttf"))
        self.add_font(FONT, "B", str(ASSETS / "DejaVuSans-Bold.ttf"))
        self.add_font(FONT, "I", str(ASSETS / "DejaVuSans-Oblique.ttf"))
        self.add_font(DISPLAY, "", str(ASSETS / "Poppins-Regular.ttf"))
        self.add_font(DISPLAY, "B", str(ASSETS / "Poppins-Bold.ttf"))
        self.set_auto_page_break(auto=False)

    def footer(self):
        cfg = self.cfg
        self.set_y(-14)
        self.set_font(FONT, "", 7.6)
        self.set_text_color(*GRIS_SUAVE)
        pie = f"{cfg.get('web','')}   ·   WhatsApp {cfg.get('whatsapp','')}"
        self.cell(MR - ML, 4, pie)


def _tarjetas(pdf, bloques, y, ancho_txt_off=22, gap=5):
    """Dibuja las tarjetas midiendo primero: nunca parte un bloque al pie."""
    for col, titulo, texto in bloques:
        pdf.set_font(DISPLAY, "B", 11)
        n_tit = len(pdf.multi_cell(MR - ML - ancho_txt_off, 5.4, titulo,
                                   dry_run=True, output="LINES"))
        pdf.set_font(FONT, "", 9)
        n_txt = len(pdf.multi_cell(MR - ML - ancho_txt_off, 4.6, texto,
                                   dry_run=True, output="LINES"))
        h = 7 + n_tit * 5.4 + n_txt * 4.6 + 7

        pdf.set_fill_color(250, 251, 252)
        pdf.rect(ML, y, MR - ML, h, style="F", round_corners=True, corner_radius=2.5)
        pdf.set_fill_color(*col)
        pdf.rect(ML, y + 1.5, 1.8, h - 3, style="F", round_corners=True, corner_radius=0.9)
        pdf.ellipse(ML + 7, y + 7.5, 3.2, 3.2, style="F")

        pdf.set_xy(ML + 14, y + 5)
        pdf.set_font(DISPLAY, "B", 11); pdf.set_text_color(*col)
        pdf.multi_cell(MR - ML - ancho_txt_off, 5.4, titulo, align="L")
        pdf.set_xy(ML + 14, y + 5 + n_tit * 5.4 + 1.5)
        pdf.set_font(FONT, "", 9); pdf.set_text_color(*GRIS_TXT)
        pdf.multi_cell(MR - ML - ancho_txt_off, 4.6, texto, align="L")
        y += h + gap
    return y


def _encabezado(pdf, titulo, bajada, primera):
    pdf.add_page()
    if primera:
        # banda de identidad: la propuesta abre como abre el catálogo
        pdf.set_fill_color(*TEAL_OSC)
        pdf.rect(0, 0, 210, 46, style="F")
        molecula(pdf, 178, 23, 0.5, [(12, 110, 134), (16, 120, 144), (10, 104, 128)])
        logo = ASSETS / "logo_blanco.png"
        if logo.exists():
            pdf.image(str(logo), x=ML, y=12, w=36)
        pdf.set_xy(ML, 30)
        pdf.set_font(FONT, "B", 8.6); pdf.set_text_color(160, 205, 215)
        etiqueta = "PROPUESTA PARA CLÍNICAS CON INTERNACIÓN"
        if DESTINATARIO:
            etiqueta += f"   ·   {DESTINATARIO.upper()}"
        pdf.cell(MR - ML, 5, etiqueta)
        y = 60
    else:
        logo = ASSETS / "logo_dimero.png"
        if logo.exists():
            pdf.image(str(logo), x=ML, y=13, w=30)
        y = 36

    pdf.set_xy(ML, y); pdf.set_font(DISPLAY, "B", 23); pdf.set_text_color(*NEGRO_SUAVE)
    for linea in titulo.split("|"):
        pdf.set_xy(ML, y)
        pdf.cell(MR - ML, 10, linea)
        y += 10.5

    pdf.set_xy(ML, y + 2); pdf.set_font(FONT, "", 10.2); pdf.set_text_color(*GRIS_TXT)
    pdf.multi_cell(MR - ML - 18, 5, bajada, align="L")
    return pdf.get_y() + 7


def construir(cfg, salida=None):
    pdf = Propuesta(cfg)

    y = _encabezado(pdf, TITULO, BAJADA, primera=True)
    y = _tarjetas(pdf, INTERNACION, y, gap=7)

    # Cierre de la página 1: si alguien lee solo esta hoja, tiene que saber qué
    # hacer. Además equilibra el blanco que queda abajo.
    y = max(y + 4, 232)
    pdf.set_fill_color(*TEAL_OSC)
    pdf.rect(ML, y, MR - ML, 17, style="F", round_corners=True, corner_radius=3)
    pdf.set_xy(ML + 9, y + 3.6)
    pdf.set_font(DISPLAY, "B", 10.4); pdf.set_text_color(*BLANCO)
    pdf.cell(MR - ML - 18, 5, "Todo esto se coordina por WhatsApp")
    pdf.set_xy(ML + 9, y + 9.4)
    pdf.set_font(FONT, "B", 9.6); pdf.set_text_color(*NARANJA)
    pdf.cell(MR - ML - 18, 4.6, str(cfg.get("whatsapp", "")))

    y = _encabezado(pdf, TITULO_2, BAJADA_2, primera=False)
    y = _tarjetas(pdf, SISTEMA, y, gap=4)

    # Cierre: la frase que explica por qué existe cada una de estas cosas.
    # Con tope, para que nunca se monte sobre el pie de página.
    y = min(y + 2, 297 - 18 - 30)
    pdf.set_fill_color(*TEAL_OSC)
    pdf.rect(ML, y, MR - ML, 30, style="F", round_corners=True, corner_radius=3)
    pdf.set_xy(ML + 9, y + 6)
    pdf.set_font(FONT, "I", 9.4); pdf.set_text_color(*BLANCO)
    pdf.multi_cell(MR - ML - 18, 4.8, CIERRE, align="L")
    pdf.set_xy(ML + 9, y + 22)
    pdf.set_font(FONT, "B", 9); pdf.set_text_color(*NARANJA)
    pdf.cell(MR - ML - 18, 4, f"Empezá en {cfg.get('web', 'dimerolab.com.ar')}")

    data = bytes(pdf.output())
    if salida is not None:
        Path(salida).write_bytes(data)
    return data


if __name__ == "__main__":
    est, cfg = cargar_datos(BASE / "data" / "estudios.xlsx")
    out = BASE / f"Propuesta internacion DimeroLab {periodo_vigencia(cfg)}.pdf"
    construir(cfg, out)
    print("Propuesta generada:", out)

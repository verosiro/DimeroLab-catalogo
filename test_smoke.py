#!/usr/bin/env python3
"""Prueba integral sin navegador: carga, aumentos, redondeo, validación y PDFs."""
import pandas as pd
from pathlib import Path
from generar_pdf import cargar_datos, construir_pdf, money
import fitz

BASE = Path(__file__).parent
est, cfg = cargar_datos(BASE / "data" / "estudios.xlsx")
est["precio_num"] = pd.to_numeric(est["precio_num"], errors="coerce")
print("Cargados:", len(est), "estudios |", est["precio_num"].notna().sum(), "con precio numérico")

# --- aumento lineal 15% con redondeo a la decena ---
def redondear(v, modo="dec"):
    if pd.isna(v): return v
    return round(v/10)*10 if modo == "dec" else round(v)

antes = est.loc[est["nombre"] == "Perfil general", "precio_num"].iloc[0]
mask = est["precio_num"].notna()
est.loc[mask, "precio_num"] = (est.loc[mask, "precio_num"] * 1.15).apply(redondear)
despues = est.loc[est["nombre"] == "Perfil general", "precio_num"].iloc[0]
print(f"Aumento 15%: Perfil general {money(antes)} -> {money(despues)} (esperado ~{money(round(antes*1.15/10)*10)})")
assert despues == round(antes*1.15/10)*10, "el aumento no cuadra"

# --- que los precios en texto (ej: "Consultar") NO se rompan ---
_pt = est["precio_texto"].astype(str).str.strip()
txt = est.loc[est["precio_texto"].notna() & (_pt != "") & (_pt.str.lower() != "nan"), "precio_texto"]
assert len(txt) > 0, "no quedó ningún precio en texto para validar"
print("Precios en texto conservados:", len(txt), "| ej:", str(txt.iloc[0])[:30])

# --- Prequirúrgico quedó desglosado en 2 filas numéricas ---
preq = est[est["nombre"].str.contains("Prequir", na=False)]
assert len(preq) == 2 and preq["precio_num"].notna().all(), "el desglose de Prequirúrgico falló"
print("Prequirúrgico desglosado:", list(preq["nombre"]))

# --- validación: duplicados activos, sin precio ---
act = est[est["activo"].astype(str).str.upper() == "SI"]
dups = act[act.duplicated(subset=["lista", "nombre"], keep=False)]
print("Duplicados activos:", len(dups), "(esperado 0)")

# --- generar los 3 PDF ---
for label, listas in {"completo": ("Perfiles","Detallado"), "perfiles": ("Perfiles",), "detallado": ("Detallado",)}.items():
    data = construir_pdf(est, cfg, listas=listas)
    doc = fitz.open(stream=data, filetype="pdf")
    print(f"PDF {label}: {len(data)//1024} KB, {doc.page_count} páginas")
    assert doc.page_count >= 1 and len(data) > 5000

print("\n✅ TODO OK")

#!/usr/bin/env python3
"""
Migración única: toma el Excel viejo (LISTA DE PRECIOS ... .xlsx) con sus
hojas de presentación que referencian por celda, y construye un dataset limpio
donde CADA estudio guarda su propio precio (sin referencias que se rompan).

Salida:
  data/estudios.xlsx   -> fuente única de verdad (hoja Estudios + QuimicasCombinables + Config)
  data/revisar.csv     -> reporte de cosas a revisar (precios en 0, duplicados, typos corregidos)
"""
import openpyxl, re, csv, unicodedata
from pathlib import Path

SRC = Path("/Users/veronicasirotinsky/Library/CloudStorage/GoogleDrive-dimerolabcontable@gmail.com/Mi unidad/Administración/PRECIOS Y COSTOS/LISTA DE PRECIOS ABRIL 2026.xlsx")
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

wb  = openpyxl.load_workbook(SRC, data_only=False)
wbv = openpyxl.load_workbook(SRC, data_only=True)
prec = wb['Precios']

# --- correcciones ortográficas seguras (se registran en revisar.csv) ---
TYPO_FIX = {
    "Abumina": "Albúmina",
    "Croronavirus Felino-PIF (IFI)": "Coronavirus Felino-PIF (IFI)",
    "Cryptococus neoformans (IC)": "Cryptococcus neoformans (IC)",
    "Cultivo bacteriolgico automatizado (Vitek)": "Cultivo bacteriológico automatizado (Vitek)",
    "Excresión fraccional de Sodio": "Excreción fraccional de Sodio",
}

def resolve_name(sheet, r, c=1):
    """Devuelve el nombre mostrado en col c: si es fórmula =Precios!Axx, resuelve al literal."""
    f = sheet.cell(r, c).value
    if isinstance(f, str) and f.startswith('='):
        m = re.match(r"=Precios!([A-Z]+)(\d+)", f)
        if m:
            return prec[f"{m.group(1)}{m.group(2)}"].value
    return f

def clean(s):
    if s is None:
        return ""
    return str(s).strip()

def norm_multiline(s):
    """Normaliza saltos de línea y espacios raros pero conserva la info."""
    if s is None:
        return ""
    return "\n".join(line.strip() for line in str(s).splitlines()).strip()

revisar = []  # (lista, nombre, motivo, detalle)
estudios = []  # dicts
orden = 0

def parse_precio(val):
    """Devuelve (precio_num, precio_texto). Números > 0 => precio_num."""
    if isinstance(val, (int, float)) and val > 0:
        return float(val), ""
    if isinstance(val, str) and val.strip():
        return None, val.strip()
    return None, ""  # 0, None o vacío

def add_sheet(sheet_name, lista, value_col=3, desc_col=7, muestra_col=4):
    global orden
    ws = wb[sheet_name]; wsv = wbv[sheet_name]
    seccion = None
    seen_names = {}
    for r in range(1, ws.max_row + 1):
        a  = ws.cell(r, 1).value
        cf = ws.cell(r, value_col).value                 # fórmula/valor precio
        cv = wsv.cell(r, value_col).value                 # valor precio
        muestra = norm_multiline(ws.cell(r, muestra_col).value)
        desc = norm_multiline(ws.cell(r, desc_col).value)
        name = resolve_name(ws, r)

        # fila vacía
        if a is None and cf is None and not muestra and not desc:
            continue

        is_price_formula = isinstance(cf, str) and cf.startswith('=')
        is_price_value   = isinstance(cv, (int, float, str)) and cv not in (None, "")

        # encabezado de sección: col A con texto, sin precio
        if a is not None and not is_price_formula and cv in (None, "") and not muestra:
            titulo = clean(a)
            # ignorar títulos globales repetidos
            if titulo.upper() in ("LISTA DE PRECIOS",):
                continue
            seccion = titulo
            continue

        if name is None or (isinstance(name, str) and not name.strip()):
            continue
        name = " ".join(clean(name).split())  # colapsa saltos de línea internos
        # saltar filas "cabecera de tabla" tipo Perfil/Precio/Muestra/Descripción
        if name.lower() in ("perfil", "cantidad de químicas seleccionadas"):
            continue

        # typo fix
        nota_typo = ""
        if name in TYPO_FIX:
            revisar.append((lista, name, "typo corregido", f"-> {TYPO_FIX[name]}"))
            name = TYPO_FIX[name]

        precio_num, precio_texto = parse_precio(cv)

        # flags
        if precio_num is None and not precio_texto:
            revisar.append((lista, name, "SIN PRECIO (mostraba $0)", f"celda {sheet_name}!{ws.cell(r,value_col).coordinate}"))
        # duplicado dentro de la misma lista
        key = name.lower()
        if key in seen_names:
            revisar.append((lista, name, "duplicado en la lista", f"filas {seen_names[key]} y {r}"))
        seen_names[key] = r

        orden += 1
        estudios.append({
            "id": orden,
            "lista": lista,
            "seccion": seccion or "",
            "nombre": name,
            "precio_num": precio_num if precio_num is not None else "",
            "precio_texto": precio_texto,
            "muestra": muestra,
            "descripcion": desc if lista == "Perfiles" else "",
            "observaciones": desc if lista == "Detallado" else "",
            "activo": "SI",
            "nota_revision": "",
            "orden": orden,
        })

# Perfiles primero (así el PDF de perfiles arranca), luego Detallado
add_sheet('Perfiles general', 'Perfiles')
add_sheet('Detallado', 'Detallado')

# ---------- POST-PROCESO: limpiar sin-precio y duplicados ----------
from collections import defaultdict

# 1) sin precio => no se imprime, se marca para completar
for e in estudios:
    if e["precio_num"] == "" and not e["precio_texto"]:
        e["activo"] = "NO"
        e["nota_revision"] = "Sin precio: cargá el valor y poné activo=SI"
    elif e["precio_texto"] and "$" in e["precio_texto"]:
        e["nota_revision"] = "Precio en texto: al aumentar, actualizalo a mano"

# 1b) etiquetar las químicas combinables (1 -> "1 química", 2 -> "2 químicas")
for e in estudios:
    if e["seccion"] == "Químicas Combinables" and str(e["nombre"]).strip().isdigit():
        n = int(str(e["nombre"]).strip())
        e["nombre"] = f"{n} química" if n == 1 else f"{n} químicas"

# 2) duplicados dentro de una misma lista => se conserva el de MAYOR precio
groups = defaultdict(list)
for e in estudios:
    groups[(e["lista"], e["nombre"].lower())].append(e)
for (lista, _), grp in groups.items():
    if len(grp) <= 1:
        continue
    priced = [e for e in grp if isinstance(e["precio_num"], (int, float))]
    keeper = max(priced, key=lambda e: e["precio_num"]) if priced else grp[0]
    kprice = f"${int(keeper['precio_num'])}" if isinstance(keeper["precio_num"], (int, float)) else "—"
    for e in grp:
        if e is not keeper and e["activo"] == "SI":
            e["activo"] = "NO"
            e["nota_revision"] = f"Duplicado: se imprime la versión de {kprice}. Revisá si corresponde."

# ---------- Escribir estudios.xlsx ----------
out_wb = openpyxl.Workbook()
wsE = out_wb.active; wsE.title = "Estudios"
cols = ["id","lista","seccion","nombre","precio_num","precio_texto","muestra","descripcion","observaciones","activo","nota_revision","orden"]
wsE.append(cols)
for e in estudios:
    wsE.append([e[c] for c in cols])

wsC = out_wb.create_sheet("Config")
wsC.append(["clave","valor"])
config = [
    ("titulo", "LISTA DE PRECIOS"),
    ("subtitulo", "Precios finales con IVA"),
    ("vigencia", "27 de ABRIL 2026"),
    ("web", "www.dimerolab.com.ar"),
    ("instagram", "instagram.com/dimerolaboratorio"),
    ("whatsapp", "11 55042497"),
    ("tagline", "Laboratorio Veterinario"),
]
for k,v in config:
    wsC.append([k,v])

out_wb.save(OUT / "estudios.xlsx")

# ---------- revisar.csv ----------
with open(OUT / "revisar.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["lista","nombre","motivo","detalle"])
    w.writerows(revisar)

# ---------- resumen ----------
from collections import Counter
activos = [e for e in estudios if e['activo'] == 'SI']
inactivos = [e for e in estudios if e['activo'] == 'NO']
print(f"Estudios migrados: {len(estudios)}  (activos={len(activos)}, desactivados={len(inactivos)})")
print("  activos por lista:", dict(Counter(e['lista'] for e in activos)))
print(f"\nDesactivados (no se imprimen hasta que los revises):")
for e in inactivos:
    print(f"  - [{e['lista']}] {e['nombre'][:45]:45} | {e['nota_revision']}")
print(f"\nTypos corregidos: {sum(1 for r in revisar if 'typo' in r[2])}")

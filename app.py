#!/usr/bin/env python3
"""
DimeroLab · Generador de Lista de Precios
App web (Streamlit) con fuente única de datos:
  - Editar estudios y precios
  - Aplicar aumentos lineales o puntuales con vista previa
  - Validar (precios faltantes, duplicados, desactivados)
  - Generar los PDF con diseño de marca

Correr local:   streamlit run app.py
"""
from pathlib import Path
from io import BytesIO
import pandas as pd
import streamlit as st

from generar_pdf import construir_pdf, money, nombre_archivo, periodo_vigencia
from generar_pdf_mobile import construir_pdf_mobile

BASE = Path(__file__).parent
DATOS = BASE / "data" / "estudios.xlsx"
LOGO = BASE / "assets" / "logo_dimero.png"

st.set_page_config(page_title="DimeroLab · Lista de Precios", page_icon="🧪", layout="wide")

COLS = ["id", "lista", "seccion", "nombre", "precio_num", "precio_texto",
        "muestra", "descripcion", "observaciones", "activo", "sellos", "nota_revision", "orden"]


# ---------------- carga / guardado ----------------
@st.cache_data
def _leer_excel(path, mtime):
    est = pd.read_excel(path, sheet_name="Estudios")
    cfg = pd.read_excel(path, sheet_name="Config")
    return est, cfg


def _normalizar(est, cfg_df):
    for c in COLS:
        if c not in est.columns:
            est[c] = ""
    est["precio_num"] = pd.to_numeric(est["precio_num"], errors="coerce")
    cfg = dict(zip(cfg_df["clave"], cfg_df["valor"]))
    return est[COLS].copy(), cfg


def cargar():
    """Lee el Excel local. Devuelve (None, None) si no está (caso web)."""
    if not DATOS.exists():
        return None, None
    est, cfg_df = _leer_excel(DATOS, DATOS.stat().st_mtime)
    return _normalizar(est, cfg_df)


def cargar_de_archivo(archivo):
    """Lee un Excel subido por la usuaria."""
    est = pd.read_excel(archivo, sheet_name="Estudios")
    try:
        cfg_df = pd.read_excel(archivo, sheet_name="Config")
    except ValueError:
        cfg_df = pd.DataFrame({"clave": [], "valor": []})
    return _normalizar(est, cfg_df)


def guardar_excel(est, cfg):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        est[COLS].to_excel(xl, sheet_name="Estudios", index=False)
        cfg_df = pd.DataFrame(list(cfg.items()), columns=["clave", "valor"])
        cfg_df.to_excel(xl, sheet_name="Config", index=False)
    return buf.getvalue()


def redondear(v, modo):
    if pd.isna(v):
        return v
    if modo == "A la decena ($10)":
        return round(v / 10) * 10
    if modo == "A la centena ($100)":
        return round(v / 100) * 100
    return round(v)


# ---------------- lista de trabajo (para cargar en sistemas de gestión) ----------------
def _precio_celda(r):
    if pd.notna(r["precio_num"]):
        return int(round(r["precio_num"]))
    txt = r.get("precio_texto", "")
    if pd.isna(txt) or not str(txt).strip():
        return ""
    return " / ".join(str(txt).split("\n")).strip()  # sin saltos de línea (rompen CSV)


def lista_trabajo_df(est, orden="Por rubro", incluir_muestra=False, incluir_plazo=False):
    """Tabla plana (una fila por práctica activa) lista para importar/copiar."""
    df = est[est["activo"].astype(str).str.upper().str.strip() == "SI"].copy()
    df["Práctica"] = df["nombre"].astype(str).str.strip()
    df["Rubro"] = df["seccion"].astype(str).str.strip()
    df["Precio"] = df.apply(_precio_celda, axis=1)
    cols = ["Práctica", "Rubro", "Precio"]
    # las opcionales entran siempre antes del precio, que cierra la fila
    if incluir_muestra:
        df["Muestra"] = df["muestra"].astype(str).str.replace("\n", " / ", regex=False).replace("nan", "")
        cols.insert(cols.index("Precio"), "Muestra")
    if incluir_plazo and "plazo" in df.columns:
        df["Plazo"] = df["plazo"].astype(str).replace("nan", "")
        cols.insert(cols.index("Precio"), "Plazo")
    out = df[cols].copy()
    if orden == "Alfabético":
        out = out.sort_values("Práctica", key=lambda s: s.str.lower())
    else:  # por rubro respetando el orden original
        out = out.loc[df.sort_values("orden").index]
    return out.reset_index(drop=True)


def lista_trabajo_csv(df):
    # UTF-8 con BOM para que Excel (es-AR) abra bien los acentos
    return ("﻿" + df.to_csv(index=False)).encode("utf-8")


def lista_trabajo_xlsx(df, cfg):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        df.to_excel(xl, sheet_name="Precios", index=False)
        leeme = pd.DataFrame({"": [
            "DimeroLab — Lista de trabajo (referencia interna).",
            f"Los precios oficiales son los del PDF de aranceles vigente al {cfg.get('vigencia','')}.",
            "Valores en pesos, IVA incluido.",
            "Este archivo es para facilitar la carga en tu sistema de gestión.",
        ]})
        leeme.to_excel(xl, sheet_name="LEEME", index=False)
    return buf.getvalue()


# ---------------- estado ----------------
if "est" not in st.session_state:
    est, cfg = cargar()
    if est is None:
        # Versión web: los precios NO viajan en el repositorio.
        # Se cargan acá y viven solo en esta sesión.
        c1, c2 = st.columns([1, 4])
        with c1:
            if LOGO.exists():
                st.image(str(LOGO))
        with c2:
            st.title("Catálogo de Servicios")
            st.caption("DimeroLab")
        st.subheader("Cargá tus datos para empezar")
        st.info("Los precios **no se guardan en la nube**: viven solo mientras usás "
                "la app. Subí tu `estudios.xlsx` y al terminar descargá la versión "
                "actualizada desde la barra lateral.")
        subido = st.file_uploader("Archivo de datos (estudios.xlsx)", type=["xlsx"])
        if subido is not None:
            try:
                e0, c0 = cargar_de_archivo(subido)
                st.session_state.est = e0
                st.session_state.cfg = c0
                st.rerun()
            except Exception as err:
                st.error(f"No pude leer el archivo: {err}")
        st.caption("¿No lo tenés a mano? Está en la carpeta `data/` de tu computadora, "
                   "o en `data/backups/` si necesitás una versión anterior.")
        st.stop()
    st.session_state.est = est
    st.session_state.cfg = cfg
if "historial" not in st.session_state:
    st.session_state.historial = []   # pila de estados anteriores (para deshacer)


def snapshot(descripcion=""):
    """Guarda el estado actual antes de un cambio, para poder deshacerlo."""
    st.session_state.historial.append((descripcion, st.session_state.est.copy()))
    st.session_state.historial = st.session_state.historial[-20:]  # últimos 20


est = st.session_state.est
cfg = st.session_state.cfg

# ---------------- encabezado ----------------
c1, c2 = st.columns([1, 4])
with c1:
    if LOGO.exists():
        st.image(str(LOGO))
with c2:
    st.title("Lista de Precios")
    st.caption("Fuente única de datos · aumentos con vista previa · PDF con diseño de marca")

activos = (est["activo"].astype(str).str.upper().str.strip() == "SI")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Estudios activos", int(activos.sum()))
m2.metric("Desactivados", int((~activos).sum()))
m3.metric("Perfiles", int(((est["lista"] == "Perfiles") & activos).sum()))
m4.metric("Individuales", int(((est["lista"] == "Detallado") & activos).sum()))

tab_pdf, tab_trabajo, tab_aum, tab_edit, tab_val = st.tabs(
    ["📄 Generar PDF", "🧾 Lista de trabajo", "📈 Aumentos", "📋 Editar estudios", "✅ Validación"])


# ================= TAB: GENERAR PDF =================
with tab_pdf:
    st.subheader("Generar y descargar los PDF")
    cc1, cc2 = st.columns(2)
    with cc1:
        cfg["vigencia"] = st.text_input("Vigencia (fecha que aparece en el PDF)",
                                        value=str(cfg.get("vigencia", "")))
        cfg["subtitulo"] = st.text_input("Subtítulo", value=str(cfg.get("subtitulo", "Precios finales con IVA")))
    with cc2:
        incluir_folleto = st.checkbox(
            "📖 Incluir folleto institucional (2 páginas al frente)", value=True,
            help="Portada + página de diferenciales con foco en la remisión 100% digital. "
                 "Ideal como carta de presentación para clientes nuevos.")
        st.caption("El PDF incluye solo los estudios **activos**. "
                   "Revisá la pestaña **Validación** antes de generar.")

    st.session_state.cfg = cfg
    gen = st.columns(3)
    # el nombre del archivo lleva la vigencia: así se sabe de cuándo es cada catálogo
    opciones = {
        "Catálogo completo": (("Perfiles", "Detallado"), ""),
        "Solo Perfiles": (("Perfiles",), "perfiles"),
        "Solo Estudios individuales": (("Detallado",), "estudios individuales"),
    }
    for (label, (listas, variante)), col in zip(opciones.items(), gen):
        with col:
            if st.button(f"🖨️ {label}", use_container_width=True):
                with st.spinner("Generando PDF…"):
                    data = construir_pdf(est, cfg, listas=listas, incluir_folleto=incluir_folleto)
                st.session_state["pdf_data"] = data
                st.session_state["pdf_name"] = nombre_archivo(cfg, variante)
                st.success("¡PDF listo! Botón de descarga abajo 👇")

    st.divider()
    st.markdown("**📱 Versión para celular**")
    st.caption("Formato angosto para leer en el teléfono, con botones tocables a la app "
               "y a WhatsApp. Ideal para mandar por WhatsApp.")
    if st.button("📱 Generar versión celular", use_container_width=True):
        with st.spinner("Generando versión celular…"):
            st.session_state["pdf_data"] = construir_pdf_mobile(est, cfg)
            st.session_state["pdf_name"] = nombre_archivo(cfg, "celular")
        st.success("¡Listo! Botón de descarga abajo 👇")

    if "pdf_data" in st.session_state:
        st.download_button("⬇️ Descargar PDF", data=st.session_state["pdf_data"],
                           file_name=st.session_state["pdf_name"], mime="application/pdf",
                           use_container_width=True, type="primary")


# ================= TAB: LISTA DE TRABAJO =================
with tab_trabajo:
    st.subheader("Lista de trabajo (para cargar en el sistema del cliente)")
    st.caption("Tabla plana, sin diseño, pensada para **importar o copiar/pegar** en sistemas "
               "de gestión (MyVete, etc.). No reemplaza al PDF oficial: es una comodidad para "
               "que el veterinario cargue tus precios sin tipear todo a mano.")
    st.info("📌 **El PDF oficial es el que vale.** Esta lista es de referencia/trabajo. "
            "El archivo lo aclara para evitar confusiones.")

    o1, o2, o3 = st.columns(3)
    orden = o1.radio("Orden", ["Por rubro", "Alfabético"])
    inc_muestra = o2.checkbox("Incluir columna Muestra", value=False)
    inc_plazo = o3.checkbox("Incluir columna Plazo", value=False,
                            help="Solo si ya cargaste los plazos de entrega.")

    lt = lista_trabajo_df(est, orden=orden, incluir_muestra=inc_muestra, incluir_plazo=inc_plazo)
    st.write(f"**{len(lt)} prácticas** activas.")
    st.dataframe(lt, use_container_width=True, height=340, hide_index=True)

    periodo = periodo_vigencia(cfg)
    d1, d2 = st.columns(2)
    d1.download_button("⬇️ Descargar Excel plano", data=lista_trabajo_xlsx(lt, cfg),
                       file_name=f"DimeroLab lista de trabajo {periodo}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)
    d2.download_button("⬇️ Descargar CSV", data=lista_trabajo_csv(lt),
                       file_name=f"DimeroLab lista de trabajo {periodo}.csv",
                       mime="text/csv", use_container_width=True)
    st.caption("El **Excel plano** sirve para copiar/pegar o importar por planilla. "
               "El **CSV** es el que suelen pedir los importadores masivos. "
               "Cuando sepas si MyVete importa y con qué columnas, lo dejamos calcado a ese formato.")


# ================= TAB: AUMENTOS =================
with tab_aum:
    st.subheader("Aplicar un aumento")
    st.caption("Elegí el alcance, previsualizá el antes/después y recién ahí aplicá.")

    modo = st.radio("¿A qué le aplico el aumento?",
                    ["Todos los estudios", "Por lista", "Por sección", "Un estudio puntual"],
                    horizontal=True)

    mask = pd.Series(True, index=est.index)
    if modo == "Por lista":
        lista_sel = st.selectbox("Lista", sorted(est["lista"].dropna().unique()))
        mask = est["lista"] == lista_sel
    elif modo == "Por sección":
        secc = st.selectbox("Sección", sorted(est["seccion"].dropna().unique()))
        mask = est["seccion"] == secc
    elif modo == "Un estudio puntual":
        opts = est[est["nombre"].astype(str).str.strip() != ""].copy()
        opts["etq"] = opts["nombre"] + "   (" + opts["seccion"].astype(str) + ")"
        sel = st.selectbox("Estudio", opts["etq"].tolist())
        idx_sel = opts[opts["etq"] == sel].index[0]
        mask = est.index == idx_sel

    con_precio = mask & est["precio_num"].notna()

    if modo == "Un estudio puntual":
        actual = est.loc[con_precio, "precio_num"]
        val_actual = float(actual.iloc[0]) if len(actual) else None
        c1, c2 = st.columns(2)
        tipo = c1.radio("Cómo", ["Por porcentaje", "Precio nuevo directo"])
        if tipo == "Por porcentaje":
            pct = c2.number_input("Aumento %", value=0.0, step=1.0)
            nuevo_val = None if val_actual is None else val_actual * (1 + pct / 100)
        else:
            nuevo_val = c2.number_input("Precio nuevo", value=float(val_actual or 0), step=10.0)
        redondeo = st.selectbox("Redondeo", ["A la decena ($10)", "A la centena ($100)", "Sin redondeo"])
        st.write(f"**{est.loc[mask, 'nombre'].iloc[0]}**")
        if val_actual is None:
            st.warning("Este estudio no tiene precio numérico (es texto o está vacío).")
        else:
            nv = redondear(nuevo_val, redondeo)
            st.write(f"Actual: {money(val_actual)}  →  Nuevo: **{money(nv)}**")
            if st.button("✅ Aplicar a este estudio", type="primary"):
                snapshot(f"Puntual: {est.loc[mask, 'nombre'].iloc[0]} → {money(nv)}")
                st.session_state.est.loc[mask, "precio_num"] = nv
                st.success("Aplicado. (Podés deshacerlo con ↩️ en la barra lateral.)")
                st.rerun()
    else:
        c1, c2 = st.columns(2)
        pct = c1.number_input("Aumento %", value=0.0, step=1.0,
                              help="Ej: 10 sube un 10%. Podés usar negativos para bajar.")
        redondeo = c2.selectbox("Redondeo", ["A la decena ($10)", "A la centena ($100)", "Sin redondeo"])

        prev = est.loc[con_precio, ["nombre", "seccion", "precio_num"]].copy()
        prev["Nuevo"] = (prev["precio_num"] * (1 + pct / 100)).apply(lambda v: redondear(v, redondeo))
        prev["Δ%"] = ((prev["Nuevo"] - prev["precio_num"]) / prev["precio_num"] * 100).round(1)
        prev_show = prev.rename(columns={"nombre": "Estudio", "seccion": "Sección", "precio_num": "Actual"})
        prev_show["Actual"] = prev_show["Actual"].apply(money)
        prev_show["Nuevo"] = prev_show["Nuevo"].apply(money)

        st.write(f"**{len(prev)} estudios** con precio numérico se van a actualizar "
                 f"(los de precio en texto o sin precio no se tocan).")
        st.dataframe(prev_show, use_container_width=True, height=320, hide_index=True)

        if st.button("✅ Aplicar aumento", type="primary", disabled=(pct == 0)):
            snapshot(f"Aumento {pct}% ({modo}) → {len(prev)} estudios")
            nuevos = (est.loc[con_precio, "precio_num"] * (1 + pct / 100)).apply(lambda v: redondear(v, redondeo))
            st.session_state.est.loc[con_precio, "precio_num"] = nuevos
            st.success(f"Aumento del {pct}% aplicado a {len(prev)} estudios. "
                       "Si te equivocaste, usá ↩️ Deshacer en la barra lateral.")
            st.rerun()


# ================= TAB: EDITAR =================
with tab_edit:
    st.subheader("Editar estudios")

    # ---- Editor con formulario (para descripciones con saltos de línea) ----
    with st.expander("✏️ Editar un estudio con formulario (recomendado para descripciones)", expanded=True):
        st.caption("Ideal para textos largos: en los cuadros grandes, **Enter hace un salto de renglón**. "
                   "En la descripción de un perfil, **cada renglón es una determinación**.")
        nombres = st.session_state.est["nombre"].astype(str)
        opciones = [f"{n}   ·   {s}" for n, s in
                    zip(nombres, st.session_state.est["seccion"].astype(str))]
        sel = st.selectbox("Elegí el estudio", opciones, key="form_sel")
        i = opciones.index(sel)
        idx = st.session_state.est.index[i]
        fila = st.session_state.est.loc[idx]

        def _v(c):
            x = fila.get(c, "")
            return "" if pd.isna(x) else str(x)

        with st.form("form_editar_estudio"):
            cA, cB = st.columns([3, 1])
            f_nombre = cA.text_input("Nombre", value=_v("nombre"))
            pn = fila.get("precio_num")
            f_precio = cB.number_input("Precio $", value=float(pn) if pd.notna(pn) else 0.0, step=10.0,
                                       help="Dejá 0 si el precio es un texto (ej: Consultar).")
            f_desc = st.text_area("Descripción / Determinaciones (un renglón por ítem)",
                                  value=_v("descripcion"), height=180)
            c1, c2 = st.columns(2)
            f_muestra = c1.text_area("Muestra", value=_v("muestra"), height=90)
            f_obs = c2.text_area("Observaciones", value=_v("observaciones"), height=90)
            c3, c4 = st.columns(2)
            f_ptexto = c3.text_input("Precio en texto (opcional)", value=_v("precio_texto"),
                                     help="Ej: Consultar. Si lo completás, se muestra en vez del número.")
            f_activo = c4.selectbox("Activo", ["SI", "NO"],
                                    index=0 if _v("activo").upper() != "NO" else 1)
            guardar = st.form_submit_button("💾 Guardar este estudio", type="primary")

        if guardar:
            snapshot(f"Editar '{f_nombre}'")
            e = st.session_state.est
            e.loc[idx, "nombre"] = f_nombre
            e.loc[idx, "precio_num"] = f_precio if f_precio > 0 else pd.NA
            e.loc[idx, "precio_texto"] = f_ptexto
            e.loc[idx, "descripcion"] = f_desc
            e.loc[idx, "muestra"] = f_muestra
            e.loc[idx, "observaciones"] = f_obs
            e.loc[idx, "activo"] = f_activo
            st.success("Guardado en la sesión. (Descargá/guardá el Excel en la barra lateral para conservarlo.)")
            st.rerun()

        # ---- eliminar este estudio ----
        st.markdown("**Eliminar este estudio**")
        cd1, cd2 = st.columns([3, 1])
        conf = cd1.checkbox(f"Confirmo que quiero eliminar «{_v('nombre')}»", key="conf_del")
        if cd2.button("🗑️ Eliminar", disabled=not conf, use_container_width=True):
            snapshot(f"Eliminar '{fila['nombre']}'")
            st.session_state.est = st.session_state.est.drop(index=idx).reset_index(drop=True)
            st.success("Estudio eliminado de la sesión. Guardá el Excel para conservarlo. "
                       "Si te arrepentís, usá ↩️ Deshacer.")
            st.rerun()

    # ---- Alta de un estudio nuevo ----
    with st.expander("➕ Dar de alta un estudio nuevo"):
        secciones_lista = {
            l: sorted(st.session_state.est[st.session_state.est["lista"] == l]["seccion"]
                      .dropna().astype(str).unique())
            for l in ["Detallado", "Perfiles"]
        }
        with st.form("form_nuevo_estudio", clear_on_submit=True):
            g1, g2 = st.columns(2)
            n_lista = g1.selectbox("¿Dónde va?", ["Detallado", "Perfiles"],
                                   help="Detallado = estudio individual · Perfiles = perfil/combo con determinaciones")
            n_secc_sel = g2.selectbox("Sección", secciones_lista["Detallado"] + secciones_lista["Perfiles"])
            n_secc_nueva = st.text_input("…o escribí una sección nueva (opcional)")
            g3, g4 = st.columns([3, 1])
            n_nombre = g3.text_input("Nombre del estudio *")
            n_precio = g4.number_input("Precio $", value=0.0, step=10.0)
            n_muestra = st.text_area("Muestra", height=70,
                                     help="Escribí el/los tubo(s); los puntos de color salen solos.")
            n_desc = st.text_area("Determinaciones (perfiles) — un renglón por ítem", height=110)
            n_obs = st.text_input("Observaciones (individuales, ej: PCR, técnica)")
            n_ptexto = st.text_input("Precio en texto (opcional, ej: Consultar)")
            alta = st.form_submit_button("➕ Agregar estudio", type="primary")

        if alta:
            if not n_nombre.strip():
                st.error("Poné un nombre para el estudio.")
            else:
                snapshot(f"Alta '{n_nombre}'")
                e = st.session_state.est
                seccion = n_secc_nueva.strip() or n_secc_sel
                # ubico el orden al final de esa sección (o al final de la lista)
                same_sec = e[(e["lista"] == n_lista) & (e["seccion"] == seccion)]
                same_lst = e[e["lista"] == n_lista]
                if len(same_sec):
                    nuevo_orden = float(same_sec["orden"].max()) + 0.5
                elif len(same_lst):
                    nuevo_orden = float(same_lst["orden"].max()) + 0.5
                else:
                    nuevo_orden = float(e["orden"].max()) + 1
                fila_nueva = {c: "" for c in COLS}
                fila_nueva.update({
                    "id": int(e["id"].max()) + 1,
                    "lista": n_lista, "seccion": seccion, "nombre": n_nombre.strip(),
                    "precio_num": n_precio if n_precio > 0 else pd.NA,
                    "precio_texto": n_ptexto.strip(),
                    "muestra": n_muestra.strip(),
                    "descripcion": n_desc.strip(), "observaciones": n_obs.strip(),
                    "activo": "SI", "nota_revision": "", "orden": nuevo_orden,
                })
                st.session_state.est = pd.concat(
                    [e, pd.DataFrame([fila_nueva])], ignore_index=True).sort_values("orden").reset_index(drop=True)
                st.success(f"«{n_nombre.strip()}» agregado en {n_lista} → {seccion}. "
                           "Guardá el Excel en la barra lateral para conservarlo.")
                st.rerun()

    st.divider()
    st.caption("O editá varios a la vez en la tabla (para textos cortos: nombres, precios, activar/desactivar). "
               "Para agregar un estudio nuevo, sumá una fila al final.")
    f1, f2 = st.columns(2)
    fl = f1.selectbox("Filtrar por lista", ["(todas)"] + sorted(est["lista"].dropna().unique()))
    fs = f2.selectbox("Filtrar por sección", ["(todas)"] + sorted(est["seccion"].dropna().unique()))
    view = est.copy()
    if fl != "(todas)":
        view = view[view["lista"] == fl]
    if fs != "(todas)":
        view = view[view["seccion"] == fs]

    edited = st.data_editor(
        view, use_container_width=True, height=460, num_rows="dynamic",
        column_config={
            "precio_num": st.column_config.NumberColumn("Precio $", format="%d"),
            "activo": st.column_config.SelectboxColumn("Activo", options=["SI", "NO"]),
            "id": st.column_config.NumberColumn("id", disabled=True),
            "orden": st.column_config.NumberColumn("orden"),
        },
        key="editor",
    )
    if st.button("💾 Guardar cambios de la tabla"):
        snapshot("Edición de tabla")
        base = st.session_state.est.copy()
        base.update(edited)  # actualiza filas existentes por índice
        nuevas = edited[~edited.index.isin(base.index)]
        if len(nuevas):
            base = pd.concat([base, nuevas], ignore_index=True)
        st.session_state.est = base.reset_index(drop=True)
        st.success("Cambios guardados en la sesión. Descargá el Excel abajo para conservarlos.")
        st.rerun()


# ================= TAB: VALIDACIÓN =================
with tab_val:
    st.subheader("Validación")
    problemas = []

    sin_precio = est[(est["precio_num"].isna()) & (est["precio_texto"].astype(str).str.strip() == "")]
    for _, r in sin_precio.iterrows():
        problemas.append(("Sin precio", r["lista"], r["nombre"], "No tiene precio numérico ni texto"))

    activos_df = est[est["activo"].astype(str).str.upper().str.strip() == "SI"]
    dup = activos_df[activos_df.duplicated(subset=["lista", "nombre"], keep=False)]
    for _, r in dup.sort_values("nombre").iterrows():
        problemas.append(("Duplicado activo", r["lista"], r["nombre"], "Aparece más de una vez activo"))

    texto_precio = est[(est["activo"].astype(str).str.upper() == "SI") &
                       est["precio_texto"].astype(str).str.contains(r"\$", na=False)]
    for _, r in texto_precio.iterrows():
        problemas.append(("Precio en texto", r["lista"], r["nombre"],
                          "Tiene $ dentro del texto: acordate de actualizarlo a mano al aumentar"))

    if problemas:
        dfp = pd.DataFrame(problemas, columns=["Tipo", "Lista", "Estudio", "Detalle"])
        st.warning(f"Hay {len(dfp)} cosas para revisar (no impiden generar el PDF, pero conviene mirarlas).")
        st.dataframe(dfp, use_container_width=True, hide_index=True, height=300)
    else:
        st.success("Todo en orden ✅")

    st.divider()
    desact = est[est["activo"].astype(str).str.upper() == "NO"]
    if len(desact):
        st.write(f"**{len(desact)} estudios desactivados** (no se imprimen):")
        st.dataframe(desact[["lista", "nombre", "nota_revision"]].rename(
            columns={"lista": "Lista", "nombre": "Estudio", "nota_revision": "Motivo / nota"}),
            use_container_width=True, hide_index=True, height=220)


# ---------------- DESHACER ----------------
st.sidebar.header("↩️ Deshacer")
n_undo = len(st.session_state.historial)
if n_undo == 0:
    st.sidebar.caption("No hay cambios para deshacer en esta sesión.")
else:
    ultimo = st.session_state.historial[-1][0]
    st.sidebar.caption(f"Último cambio: **{ultimo}**")
    if st.sidebar.button(f"↩️ Deshacer último cambio  ({n_undo} disponibles)",
                         use_container_width=True, type="primary"):
        _desc, prev = st.session_state.historial.pop()
        st.session_state.est = prev
        st.sidebar.success(f"Deshecho: {_desc}")
        st.rerun()
    if n_undo > 1 and st.sidebar.button("⏮️ Deshacer TODO (volver al inicio de la sesión)",
                                        use_container_width=True):
        _desc, prev = st.session_state.historial[0]
        st.session_state.est = prev
        st.session_state.historial = []
        st.sidebar.success("Se deshicieron todos los cambios de la sesión.")
        st.rerun()

# ---------------- guardar / descargar dataset ----------------
st.sidebar.header("💾 Guardar datos")
st.sidebar.caption("La fuente única es el archivo `data/estudios.xlsx`. "
                   "Descargalo para conservar tus cambios (y volver a subirlo la próxima).")
xls_bytes = guardar_excel(st.session_state.est, st.session_state.cfg)
st.sidebar.download_button("⬇️ Descargar Excel de datos", data=xls_bytes,
                           file_name="estudios.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
if st.sidebar.button("Guardar en el archivo local", use_container_width=True,
                     help="Solo funciona cuando corrés la app en tu computadora. "
                          "Antes de sobrescribir, hace un backup automático."):
    try:
        # backup automático del archivo actual antes de sobrescribir
        respaldo = ""
        if DATOS.exists():
            import shutil
            from datetime import datetime
            bkp_dir = DATOS.parent / "backups"
            bkp_dir.mkdir(exist_ok=True)
            respaldo = bkp_dir / f"estudios_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
            shutil.copy2(DATOS, respaldo)
            # conservar solo los últimos 15 backups
            viejos = sorted(bkp_dir.glob("estudios_*.xlsx"))[:-15]
            for v in viejos:
                v.unlink(missing_ok=True)
        DATOS.write_bytes(xls_bytes)
        _leer_excel.clear()
        msg = "Guardado en data/estudios.xlsx"
        if respaldo:
            msg += f"  ·  backup: {Path(respaldo).name}"
        st.sidebar.success(msg)
    except Exception as e:
        st.sidebar.error(f"No se pudo guardar: {e}")

# ---------------- restaurar desde backup ----------------
_bkp_dir = DATOS.parent / "backups"
_backups = sorted(_bkp_dir.glob("estudios_*.xlsx"), reverse=True) if _bkp_dir.exists() else []
if _backups:
    with st.sidebar.expander(f"🗂️ Restaurar desde backup ({len(_backups)})"):
        elegido = st.selectbox("Versión guardada", [b.name for b in _backups])
        if st.button("Restaurar esta versión", use_container_width=True):
            snapshot("Antes de restaurar backup")
            e2 = pd.read_excel(_bkp_dir / elegido, sheet_name="Estudios")
            e2["precio_num"] = pd.to_numeric(e2["precio_num"], errors="coerce")
            st.session_state.est = e2
            st.success(f"Restaurado: {elegido}")
            st.rerun()

up = st.sidebar.file_uploader("Cargar otro Excel de datos", type=["xlsx"])
if up is not None:
    try:
        e2 = pd.read_excel(up, sheet_name="Estudios")
        e2["precio_num"] = pd.to_numeric(e2["precio_num"], errors="coerce")
        st.session_state.est = e2
        st.sidebar.success("Datos cargados desde el archivo subido.")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Archivo inválido: {e}")

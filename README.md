# DimeroLab · Catálogo de Servicios

App para mantener el catálogo de servicios del laboratorio en **un solo lugar**,
aplicar aumentos (lineales o puntuales) con vista previa, y generar los **PDF con
diseño de marca** listos para compartir.

No es solo una lista de precios: es la **carta de presentación** para clientes nuevos
y un **"despertar"** para los actuales, que muchas veces no saben todo lo que el
laboratorio hace. La herramienta de uso diario es la app de remisión
(dimerolab.com.ar); esta guía es la puerta de entrada.

## Cómo usarla en tu compu

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Las 5 pestañas

- **📄 Generar PDF** — catálogo completo, solo Perfiles, solo Individuales, o la
  **versión celular** (formato angosto con botones tocables a la app y a WhatsApp).
  El archivo se llama solo con la vigencia que cargaste
  (`Catalogo DimeroLab octubre 2026.pdf`), así nunca se confunde con uno viejo.
- **🧾 Lista de trabajo** — tabla plana (Excel/CSV) para que el cliente cargue tus
  precios en su sistema de gestión.
- **📈 Aumentos** — por todo / lista / sección / estudio puntual, con vista previa
  antes de aplicar. Redondeo a la decena por defecto.
- **📋 Editar estudios** — formulario (ideal para textos largos: ahí Enter hace salto
  de renglón), alta de estudios nuevos, eliminación, y tabla para cambios rápidos.
- **✅ Validación** — precios faltantes, duplicados y estudios desactivados.

### Red de seguridad
- **↩️ Deshacer** en la barra lateral: vuelve atrás el último cambio (hasta 20 pasos)
  o todos los de la sesión.
- **Backup automático** cada vez que guardás al archivo local, con opción de restaurar.
- Nada se toca hasta que guardás: si algo sale mal, reiniciá y listo.

## Estructura
```
app.py                   La app (Streamlit)
generar_pdf.py           Catálogo A4: color por área, índice de uña, portadas, QR
generar_pdf_mobile.py    Versión celular con botones tocables
folleto.py               Portada institucional
build_dataset.py         Migración única del Excel viejo (ya corrida)
data/estudios.xlsx       FUENTE ÚNICA de datos (no se sube al repositorio)
```

## El diseño, en criterios
- **El color siempre significa algo**: cada área diagnóstica tiene el suyo, y los
  puntos indican la muestra en la que hay que remitir. Nunca es decoración.
- **El precio es discreto** (chico, gris, sin símbolo, en línea tras el nombre): el
  nombre y lo que incluye el estudio mandan. Es *menu engineering*, no timidez.
- **La barra de los perfiles mide parámetros informados**, no determinaciones: un
  hemograma informa 22 parámetros y una urea, uno.
- **Cada sección arranca en página nueva**; si sobra espacio, lo llena la molécula.

## Subirla a la web (Streamlit Cloud)

**Los precios NO están en este repositorio.** El repo tiene solo el código; la lista
vive en tu computadora (`data/estudios.xlsx`, ignorado por git).

Por eso el repo puede ser **público** sin exponer nada: no hay valores, ni costos, ni
notas internas. Y por eso Streamlit Cloud no necesita permisos especiales.

1. Creá un repo **público** en GitHub y subí esta carpeta.
2. Entrá a https://share.streamlit.io → **Create app** → elegí el repo, rama `main`,
   archivo `app.py`.

### Cómo se usa en la web
Al abrirla te va a pedir el Excel de datos:
1. **Subís** `data/estudios.xlsx` (está en tu compu).
2. Trabajás normalmente: aumentos, ediciones, generar PDF.
3. **Descargás el Excel actualizado** desde la barra lateral antes de cerrar.

Los datos viven solo durante la sesión. Si cerrás sin descargar, se pierden los cambios
(los PDF que hayas bajado quedan igual).

> Para aumentos grandes conviene usar la app **en tu computadora**: ahí el botón
> "Guardar en el archivo local" sí conserva los cambios y hace backup automático.


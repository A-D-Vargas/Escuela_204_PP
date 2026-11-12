import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración principal de la aplicación
st.set_page_config(
    page_title="Sistema Integrado de Gestión Escolar",
    page_icon="🏫",
    layout="wide"
)

# ID de la planilla compartida de Google Sheets principal
SHEET_ID = "1w4bE2GRG8UDYHkDEBNYpd22nDeX9D3MCVgALKDP8UJw"

# -------------------------------------------------------------------
# IDS DE PLANILLAS DE NOTAS POR MATERIA
# -------------------------------------------------------------------
SHEET_ID_LENGUA = "1PqxiHPEHtLtgyAXwRG60k-hex1F1NYR0YgJ3qIhJlo0"
SHEET_ID_MATEMATICA = "1qojneCkGcYNDadTV1kiNajMm0pLhMnGvZWxgjrb63MY"
SHEET_ID_EDFISICA = "1STBfC20E98khRVTZGBp15AjIeeRdK3i4-L3WBNVNcCY"

# -------------------------------------------------------------------
# 1. CARGA AUTOMÁTICA DE DATOS DESDE GOOGLE SHEETS
# -------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_all_data(sheet_id):
    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="
    
    df_alumnos = pd.read_csv(f"{base_url}BD_Alumnos", dtype=str)
    df_alumnos.columns = df_alumnos.columns.str.strip()
    
    df_asistencia = pd.read_csv(f"{base_url}Asistencia")
    df_reporte = pd.read_csv(f"{base_url}Reporte%20Gr%C3%A1fico%20Asistencia")
    df_alertas = pd.read_csv(f"{base_url}Alertas")
    
    try:
        df_usuarios = pd.read_csv(f"{base_url}Usuarios", dtype=str)
        df_usuarios.columns = df_usuarios.columns.str.strip()
    except Exception:
        df_usuarios = pd.DataFrame(columns=["Usuario", "Contraseña", "Rol", "Nombre", "DNI_Asociado"])
        
    return df_alumnos, df_asistencia, df_reporte, df_alertas, df_usuarios

# Función auxiliar para cargar notas desde la "Hoja 1" tabular de cada materia
@st.cache_data(ttl=300)
def load_notas_materias():
    materias_dfs = {}
    ids_materias = {
        "Lengua": SHEET_ID_LENGUA,
        "Matemática": SHEET_ID_MATEMATICA,
        "Educación Física": SHEET_ID_EDFISICA
    }
    
    base_url = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet=Hoja%201"
    
    for materia, sid in ids_materias.items():
        try:
            df = pd.read_csv(base_url.format(sid), dtype=str)
            df.columns = df.columns.str.strip()
            materias_dfs[materia] = df
        except Exception:
            materias_dfs[materia] = pd.DataFrame()
            
    return materias_dfs

# Cargar datos iniciales para validación de usuarios
try:
    _, _, _, _, df_usuarios_init = load_all_data(SHEET_ID)
except Exception:
    df_usuarios_init = pd.DataFrame()

# -------------------------------------------------------------------
# 2. FUNCIÓN AUXILIAR DE RENDERIZADO DE ESTUDIANTE (BOLETÍN Y ASISTENCIA)
# -------------------------------------------------------------------
def renderizar_consulta_estudiante(dni_ingresado, anio_sel, df_alumnos, df_asistencia):
    dni_limpio = str(dni_ingresado).replace('.0', '').strip()
    
    df_alumnos['DNI_Limpio'] = df_alumnos['DNI'].astype(str).str.replace('.0', '', regex=False).str.strip()
    alumno = df_alumnos[df_alumnos['DNI_Limpio'] == dni_limpio] if 'DNI' in df_alumnos.columns else pd.DataFrame()
    
    if not alumno.empty:
        nombre = alumno.iloc[0]['Apellido y Nombre']
        grado = alumno.iloc[0]['Grado y Sección Actual'] if 'Grado y Sección Actual' in alumno.columns else "Sin datos"
        estado = alumno.iloc[0]['Estado de Matrícula'] if 'Estado de Matrícula' in alumno.columns else "Sin datos"
        
        st.success(f"**Estudiante:** {nombre}")
        st.info(f"**Año Consultado:** {anio_sel} | **Grado:** {grado} | **Estado:** {estado}")
        
        # --- A. RESUMEN DE ASISTENCIA DINÁMICO ---
        st.subheader(f"📊 Resumen de Asistencia - Ciclo {anio_sel}")
        col_nombre_asist = df_asistencia.columns[1] if len(df_asistencia.columns) > 1 else df_asistencia.columns[0]
        asist_row = df_asistencia[df_asistencia[col_nombre_asist].astype(str).str.strip() == str(nombre).strip()]
        
        if not asist_row.empty:
            cols_fechas = [c for c in df_asistencia.columns if not str(c).startswith('Unnamed') and c != col_nombre_asist and "porcentaje" not in str(c).lower()]
            cols_fechas_anio = []
            for c in cols_fechas:
                str_f = c.strftime('%Y') if hasattr(c, 'strftime') else str(c)
                if str(anio_sel) in str_f:
                    cols_fechas_anio.append(c)

            if cols_fechas_anio:
                valores_asist = asist_row[cols_fechas_anio].values.flatten()
                valores_asist = [v for v in valores_asist if pd.notnull(v) and str(v).strip() != '']
                if valores_asist:
                    presentes = sum(1 for v in valores_asist if str(v).strip().lower() in ['presente', 'tardanza'])
                    ausentes = sum(1 for v in valores_asist if str(v).strip().lower() == 'ausente')
                    total_dias = presentes + ausentes
                    pct_final = (presentes / total_dias * 100) if total_dias > 0 else 0.0
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Asistencias Totales", f"{presentes} días")
                    m2.metric("Inasistencias", f"{ausentes} días", delta_color="inverse")
                    m3.metric("Total Días Registrados", f"{total_dias} días")
                    m4.metric("% Promedio Asistencia", f"{pct_final:.2f}%".replace('.', ','))
                else:
                    st.info(f"ℹ️ No se registraron asistencias para {nombre} en el año {anio_sel}.")
            else:
                st.info(f"ℹ️ El ciclo lectivo **{anio_sel}** no posee fechas registradas.")
        else:
            st.warning("No se encontró al estudiante en la planilla de asistencia.")

        st.markdown("---")

        # --- B. BOLETÍN DE CALIFICACIONES ---
        st.subheader(f"📝 Boletín de Calificaciones - Ciclo {anio_sel}")
        materias_dict = load_notas_materias()
        boletin_registros = []
        
        for materia, df_mat in materias_dict.items():
            if df_mat.empty:
                continue
            if 'Alumno' in df_mat.columns and 'Año' in df_mat.columns and 'Nota' in df_mat.columns:
                filtro_nota = df_mat[
                    (df_mat['Alumno'].astype(str).str.strip() == str(nombre).strip()) & 
                    (df_mat['Año'].astype(str).str.strip().str.replace('.0', '', regex=False) == str(anio_sel))
                ]
                for _, row in filtro_nota.iterrows():
                    trimestre = row.get('Trimestre', 'Trimestre')
                    calificacion = row.get('Nota', '')
                    if pd.notnull(calificacion) and str(calificacion).strip() != '':
                        boletin_registros.append({
                            "Asignatura / Período": f"{materia} ({trimestre})",
                            "Calificación": calificacion
                        })
        
        if boletin_registros:
            df_boletin = pd.DataFrame(boletin_registros)
            st.dataframe(df_boletin, use_container_width=True, hide_index=True)
        else:
            st.info(f"ℹ️ No se registran calificaciones en el boletín para el ciclo lectivo **{anio_sel}**.")
    else:
        st.warning(f"No se encontró ningún estudiante registrado con el DNI: {dni_ingresado}")

# -------------------------------------------------------------------
# 3. CONTROL DE SESIÓN Y AUTENTICACIÓN
# -------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.dni_vinculado = None

def login_form():
    st.title("🏫 Sistema de Gestión Escolar - Acceso")
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Iniciar Sesión")
        user_input = st.text_input("Usuario")
        pass_input = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", use_container_width=True):
            user_encontrado = False
            if not df_usuarios_init.empty:
                for _, row in df_usuarios_init.iterrows():
                    u_sheet = str(row.get('Usuario', '')).strip()
                    p_sheet = str(row.get('Contraseña', '')).strip()
                    
                    # Respeta estrictamente mayúsculas y minúsculas del usuario y contraseña
                    if u_sheet == str(user_input).strip() and p_sheet == str(pass_input).strip():
                        st.session_state.logged_in = True
                        st.session_state.user_role = str(row.get('Rol', '')).strip()
                        st.session_state.user_name = str(row.get('Nombre', '')).strip()
                        
                        # Captura segura de la celda DNI_Asociado por nombre exacto, parcial o índice
                        dni_val = "0"
                        for col_name in row.index:
                            if "dni" in col_name.lower():
                                val_celda = row.get(col_name)
                                if pd.notnull(val_celda):
                                    dni_val = str(val_celda)
                                    break
                        if (not dni_val or dni_val.lower() == 'nan' or dni_val == '0') and len(row) >= 5:
                            val_celda = row.iloc[4]
                            if pd.notnull(val_celda):
                                dni_val = str(val_celda)
                                
                        st.session_state.dni_vinculado = dni_val.strip()
                        user_encontrado = True
                        break
            
            if user_encontrado:
                st.success(f"Bienvenido/a, {st.session_state.user_name}")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

if not st.session_state.logged_in:
    login_form()
else:
    try:
        df_alumnos, df_asistencia, df_reporte, df_alertas, _ = load_all_data(SHEET_ID)
    except Exception as e:
        st.error(f"Error al conectar con la planilla de Google Sheets: {e}")
        st.stop()
        
    st.sidebar.markdown(f"👤 **{st.session_state.user_name}**")
    st.sidebar.caption(f"Rol: {st.session_state.user_role}")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.session_state.dni_vinculado = None
        st.rerun()
        
    st.sidebar.markdown("---")

    # -------------------------------------------------------------------
    # 4. RUTEO DE MENÚ SEGÚN ROL
    # -------------------------------------------------------------------
    es_rol_familia_menu = "familia" in str(st.session_state.user_role).lower() or "alumnado" in str(st.session_state.user_role).lower()

    if es_rol_familia_menu:
        opciones_menu = ["🔍 Consulta de Boletín / Legajo"]
    elif st.session_state.user_role.lower() == "docente":
        opciones_menu = [
            "📝 Cargar Asistencia / Notas", 
            "📅 Planilla de Asistencia", 
            "👥 Legajo de Alumnos"
        ]
    else:  # Director/a u otros roles administrativos
        opciones_menu = [
            "📊 Dashboard & Alertas", 
            "👥 Legajo de Alumnos", 
            "📅 Planilla de Asistencia", 
            "📝 Cargar Asistencia / Notas",
            "🔍 Consulta de Boletín / Legajo"
        ]

    menu_seleccionado = st.sidebar.radio("Navegación:", opciones_menu)

    # -------------------------------------------------------------------
    # 5. DESARROLLO DE MÓDULOS
    # -------------------------------------------------------------------
    
    if menu_seleccionado == "📊 Dashboard & Alertas":
        st.title("📊 Panel Institucional y Semáforo de Asistencia")
        
        df_alertas_limpio = df_alertas.dropna(subset=[df_alertas.columns[1]]).copy()
        df_alertas_limpio.columns = ['Apellido y Nombre', 'Porcentaje']
        df_alertas_limpio = df_alertas_limpio[df_alertas_limpio['Porcentaje'] != '% ASISTENCIA'].copy()
        
        if 'DNI' in df_alumnos.columns and 'Apellido y Nombre' in df_alumnos.columns:
            df_alertas_limpio = pd.merge(
                df_alertas_limpio, 
                df_alumnos[['DNI', 'Apellido y Nombre']], 
                on='Apellido y Nombre', 
                how='left'
            )
            df_alertas_limpio = df_alertas_limpio[['DNI', 'Apellido y Nombre', 'Porcentaje']]
            df_alertas_limpio['DNI'] = df_alertas_limpio['DNI'].fillna('-').astype(str).str.replace('.0', '', regex=False)

        df_alertas_limpio['% Asistencia'] = df_alertas_limpio['Porcentaje'].apply(
            lambda x: f"{float(x) * 100:.2f}%".replace('.', ',') if pd.notnull(x) and isinstance(x, (int, float, str)) and str(x).replace('.','',1).isdigit() and float(x) <= 1.0 
            else (f"{float(x):.2f}%".replace('.', ',') if pd.notnull(x) and isinstance(x, (int, float, str)) and str(x).replace('.','',1).isdigit() else str(x))
        )
        
        if 'Porcentaje' in df_alertas_limpio.columns:
            df_alertas_limpio = df_alertas_limpio.drop(columns=['Porcentaje'])

        c1, c2, c3 = st.columns(3)
        c1.metric("Matrícula Total", len(df_alumnos))
        cursando_count = len(df_alumnos[df_alumnos['Estado de Matrícula'] == 'Cursando']) if 'Estado de Matrícula' in df_alumnos.columns else len(df_alumnos)
        c2.metric("Alumnos Cursando", cursando_count)
        c3.metric("Casos Críticos (<60%)", len(df_alertas_limpio))
        
        st.markdown("---")
        st.subheader("🚦 Semáforo Institucional de Asistencia")
        
        if 'REPORTE GRAFICO' in df_reporte.columns and 'CANTIDAD DE ALUMNOS' in df_reporte.columns:
            df_rep = df_reporte.dropna(subset=['REPORTE GRAFICO']).copy()
            color_map = {
                'Verde (80% - 100%)': '#2ecc71',
                'Amarillo (60% - 79%)': '#f1c40f',
                'Rojo (Menor a 60%)': '#e74c3c'
            }
            
            col_g, col_y, col_r = st.columns(3)
            for _, row in df_rep.iterrows():
                cat = str(row['REPORTE GRAFICO'])
                cant = row['CANTIDAD DE ALUMNOS']
                if 'Verde' in cat:
                    col_g.metric("🟢 Alta Asistencia (80% - 100%)", f"{cant} Alumnos")
                elif 'Amarillo' in cat:
                    col_y.metric("🟡 Asistencia Media (60% - 79%)", f"{cant} Alumnos")
                elif 'Rojo' in cat:
                    col_r.metric("🔴 Riesgo Crítico (< 60%)", f"{cant} Alumnos")

            st.markdown("<br>", unsafe_allow_html=True)
            fig_semaforo = px.bar(
                df_rep,
                x='CANTIDAD DE ALUMNOS',
                y='REPORTE GRAFICO',
                orientation='h',
                color='REPORTE GRAFICO',
                color_discrete_map=color_map,
                text='CANTIDAD DE ALUMNOS',
                title="Distribución de Estudiantes según Nivel de Asistencia"
            )
            fig_semaforo.update_traces(textposition='outside')
            fig_semaforo.update_layout(showlegend=False, xaxis_title="Cantidad de Alumnos", yaxis_title="Rango de Asistencia", height=300)
            st.plotly_chart(fig_semaforo, use_container_width=True)

        st.markdown("---")
        st.subheader("⚠️ Estudiantes en Riesgo de Deserción")
        st.dataframe(df_alertas_limpio, use_container_width=True, hide_index=True)
            
    elif menu_seleccionado == "📝 Cargar Asistencia / Notas":
        st.title("📝 Gestión y Registro de Datos Escolares")
        tab_asistencia, tab_notas = st.tabs(["📋 Asistencia", "✏️ Calificaciones"])

        with tab_asistencia:
            st.subheader("Carga de asistencia")
            st.link_button("🔗 Abrir Formulario de Asistencia (Google Forms)", "https://docs.google.com/forms/d/e/1FAIpQLSc46TWUXwAdRfPggqiuhDhaEyrvpw1W04NdzpcZ7jGAOgDF5g/viewform?usp=dialog")
            st.markdown("---")

        with tab_notas:
            st.subheader("Carga de Calificaciones Trimestrales")
            st.link_button("🔗 Abrir Formulario de notas (Google Forms)", "https://docs.google.com/forms/d/e/1FAIpQLSdqJ8wLoft_ujZrcCfwymKZjj5SICRyn-hsEGsT7J5qnbr_tw/viewform?usp=dialog")
            st.markdown("---")
            
    elif menu_seleccionado == "👥 Legajo de Alumnos":
        st.title("👥 Base de Datos de Alumnos")
        columnas_padron = [c for c in df_alumnos.columns if not str(c).startswith('Unnamed') and c != 'DNI_Limpio']
        df_alumnos_limpio = df_alumnos[columnas_padron].copy()
        
        grados = ["Todos"] + list(df_alumnos_limpio['Grado y Sección Actual'].dropna().unique()) if 'Grado y Sección Actual' in df_alumnos_limpio.columns else ["Todos"]
        grado_sel = st.sidebar.selectbox("Filtrar por Grado:", grados)
        
        if grado_sel != "Todos":
            df_alumnos_limpio = df_alumnos_limpio[df_alumnos_limpio['Grado y Sección Actual'] == grado_sel]
            
        if 'Año de Ingreso' in df_alumnos_limpio.columns:
            df_alumnos_limpio['Año de Ingreso'] = df_alumnos_limpio['Año de Ingreso'].apply(
                lambda x: x.strftime('%d/%m/%Y') if hasattr(x, 'strftime') else str(x)
            )

        st.dataframe(df_alumnos_limpio, use_container_width=True, hide_index=True)

    elif menu_seleccionado == "📅 Planilla de Asistencia":
        st.title("📅 Planilla de Asistencia")
        col_nombre = df_asistencia.columns[1] if len(df_asistencia.columns) > 1 else df_asistencia.columns[0]
        cols_fechas = [c for c in df_asistencia.columns if not str(c).startswith('Unnamed') and c != col_nombre and "porcentaje" not in str(c).lower()]
        
        fechas_dict = {}
        for c in cols_fechas:
            nombre_f = c.strftime('%d/%m/%Y') if hasattr(c, 'strftime') else str(c).split()[0]
            fechas_dict[nombre_f] = c

        modo_vista = st.radio("Seleccione el modo de visualización vertical:", ["📅 Ver por Fecha", "👤 Ver por Estudiante", "📊 Planilla Completa"], horizontal=True)
        st.markdown("---")

        if modo_vista == "📅 Ver por Fecha":
            fecha_sel_nombre = st.selectbox("Seleccione la Fecha:", list(fechas_dict.keys()))
            col_fecha_real = fechas_dict[fecha_sel_nombre]
            df_vertical_fecha = df_asistencia[[col_nombre, col_fecha_real]].copy()
            df_vertical_fecha.columns = ["Estudiante", f"Estado de Asistencia ({fecha_sel_nombre})"]
            df_vertical_fecha = df_vertical_fecha.dropna(subset=["Estudiante"])
            
            presentes = len(df_vertical_fecha[df_vertical_fecha.iloc[:, 1].astype(str).str.lower().isin(['presente', 'tardanza'])])
            ausentes = len(df_vertical_fecha[df_vertical_fecha.iloc[:, 1].astype(str).str.lower() == 'ausente'])
            
            k1, k2 = st.columns(2)
            k1.metric("Presentes / Tardanzas", f"{presentes} Alumnos")
            k2.metric("Ausentes", f"{ausentes} Alumnos")
            st.dataframe(df_vertical_fecha, use_container_width=True, hide_index=True)

        elif modo_vista == "👤 Ver por Estudiante":
            alumnos_lista = df_asistencia[col_nombre].dropna().unique().tolist()
            estudiante_sel = st.selectbox("Seleccione el Estudiante:", alumnos_lista)
            row_est = df_asistencia[df_asistencia[col_nombre] == estudiante_sel]
            
            if not row_est.empty:
                registros = []
                for fecha_nom, col_f in fechas_dict.items():
                    val = row_est.iloc[0][col_f]
                    registros.append({"Fecha": fecha_nom, "Estado": val if pd.notnull(val) else "Sin registro"})
                df_vertical_est = pd.DataFrame(registros)
                st.dataframe(df_vertical_est, use_container_width=True, hide_index=True)

        else:
            col_porcentaje = df_asistencia.columns[-1]
            cols_finales = [col_nombre] + cols_fechas + [col_porcentaje]
            df_asistencia_limpio = df_asistencia[cols_finales].copy()
            df_asistencia_limpio[col_porcentaje] = df_asistencia_limpio[col_porcentaje].apply(
                lambda x: f"{float(x) * 100:.2f}%".replace('.', ',') if pd.notnull(x) and isinstance(x, (int, float)) and float(x) <= 1.0 
                else (f"{float(x):.2f}%".replace('.', ',') if pd.notnull(x) and isinstance(x, (int, float)) else str(x))
            )
            nuevos_encabezados = [col_nombre] + list(fechas_dict.keys()) + ["Porcentaje de asistencia"]
            df_asistencia_limpio.columns = nuevos_encabezados
            st.dataframe(df_asistencia_limpio, use_container_width=True, hide_index=True)
            
    elif menu_seleccionado == "🔍 Consulta de Boletín / Legajo":
        st.title("🔍 Consulta Individual de Estudiante e Historial")
        
        es_rol_familia = "familia" in str(st.session_state.user_role).lower() or "alumnado" in str(st.session_state.user_role).lower()
        
        if es_rol_familia:
            dni_raw = str(st.session_state.dni_vinculado).strip()
            
            # Limpieza robusta que soporta comas (,) y punto y coma (;)
            dnis_familia = []
            if dni_raw and dni_raw != '0' and dni_raw.lower() != 'nan':
                # Reemplazamos punto y coma por coma y separamos
                for parte in dni_raw.replace(';', ',').split(','):
                    parte_limpia = parte.replace('.0', '').strip()
                    if parte_limpia:
                        dnis_familia.append(parte_limpia)
            
            anio_sel = st.selectbox("Seleccione Año Lectivo:", ["2026", "2025", "2024"])
            
            if dnis_familia:
                nombres_hijos = []
                mapa_dnis = {}
                
                df_alumnos['DNI_Limpio'] = df_alumnos['DNI'].astype(str).str.replace('.0', '', regex=False).str.strip()
                
                for d in dnis_familia:
                    res_al = df_alumnos[df_alumnos['DNI_Limpio'] == str(d)]
                    if not res_al.empty:
                        nom = res_al.iloc[0]['Apellido y Nombre']
                        nombres_hijos.append(nom)
                        mapa_dnis[nom] = d
                
                if len(nombres_hijos

import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración principal de la aplicación
st.set_page_config(
    page_title="Sistema Integrado de Gestión Escolar",
    page_icon="🏫",
    layout="wide"
)

# ID de la planilla compartida de Google Sheets
SHEET_ID = "1w4bE2GRG8UDYHkDEBNYpd22nDeX9D3MCVgALKDP8UJw"

# -------------------------------------------------------------------
# 1. BASE DE DATOS DE USUARIOS Y ROLES
# -------------------------------------------------------------------
USUARIOS = {
    "director": {"pass": "dir123", "rol": "Director/a", "nombre": "Dirección Institucional"},
    "docente": {"pass": "doc123", "rol": "Docente", "nombre": "Prof. María González"},
    "familia": {"pass": "fam123", "rol": "Alumnado y Familias", "nombre": "Familia Estudiante"}
}

# -------------------------------------------------------------------
# 2. CARGA AUTOMÁTICA DE DATOS DESDE GOOGLE SHEETS
# -------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_all_data(sheet_id):
    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="
    
    df_alumnos = pd.read_csv(f"{base_url}BD_Alumnos")
    df_asistencia = pd.read_csv(f"{base_url}Asistencia")
    df_reporte = pd.read_csv(f"{base_url}Reporte%20Gr%C3%A1fico%20Asistencia")
    df_alertas = pd.read_csv(f"{base_url}Alertas")
    df_notas = pd.read_csv(f"{base_url}Notas")  # <--- Agrega la carga de la hoja de notas
    
    return df_alumnos, df_asistencia, df_reporte, df_alertas, df_notas
# -------------------------------------------------------------------
# 3. CONTROL DE SESIÓN Y AUTENTICACIÓN
# -------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None

def login_form():
    st.title("🏫 Sistema de Gestión Escolar - Acceso")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Iniciar Sesión")
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", use_container_width=True):
            if user in USUARIOS and USUARIOS[user]["pass"] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = USUARIOS[user]["rol"]
                st.session_state.user_name = USUARIOS[user]["nombre"]
                st.success(f"Bienvenido/a, {USUARIOS[user]['nombre']}")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

if not st.session_state.logged_in:
    login_form()
else:
    # Cargar datos desde Google Sheets
    try:
        df_alumnos, df_asistencia, df_reporte, df_alertas, df_notas = load_all_data(SHEET_ID)
    except Exception as e:
        st.error(f"Error al conectar con la planilla de Google Sheets: {e}")
        st.stop()
    # Panel lateral de control de usuario
    st.sidebar.markdown(f"👤 **{st.session_state.user_name}**")
    st.sidebar.caption(f"Rol: {st.session_state.user_role}")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.rerun()
        
    st.sidebar.markdown("---")

    # -------------------------------------------------------------------
    # 4. RUTEO DE MENÚ SEGÚN EL ROL DE USUARIO (Nombres sincronizados)
    # -------------------------------------------------------------------
    if st.session_state.user_role == "Director/a":
        opciones_menu = [
            "📊 Dashboard & Alertas", 
            "👥 Legajo de Alumnos", 
            "📅 Planilla de Asistencia", 
            "📝 Cargar Asistencia / Notas",
            "🔍 Consulta de Boletín / Legajo"
        ]
    elif st.session_state.user_role == "Docente":
        opciones_menu = [
            "📝 Cargar Asistencia / Notas", 
            "📅 Planilla de Asistencia", 
            "👥 Legajo de Alumnos"
        ]
    else:  # Alumnado y Familias
        opciones_menu = [
            "🔍 Consulta de Boletín / Legajo"
        ]

    menu_seleccionado = st.sidebar.radio("Navegación:", opciones_menu)

    # -------------------------------------------------------------------
    # 5. DESARROLLO DE MÓDULOS
    # -------------------------------------------------------------------
    
    # --- MÓDULO 1: DASHBOARD & ALERTAS TEMPRANAS ---
    if menu_seleccionado == "📊 Dashboard & Alertas":
        st.title("📊 Panel Institucional y Semáforo de Asistencia")
        
        # 1. Procesamiento y limpieza de Alertas
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

        # Indicadores generales
        c1, c2, c3 = st.columns(3)
        c1.metric("Matrícula Total", len(df_alumnos))
        cursando_count = len(df_alumnos[df_alumnos['Estado de Matrícula'] == 'Cursando']) if 'Estado de Matrícula' in df_alumnos.columns else len(df_alumnos)
        c2.metric("Alumnos Cursando", cursando_count)
        c3.metric("Casos Críticos (<60%)", len(df_alertas_limpio))
        
        st.markdown("---")
        
        # 2. SEMÁFORO DE ASISTENCIA (Gráfico de Barras con colores de semáforo)
        st.subheader("🚦 Semáforo Institucional de Asistencia")
        
        if 'REPORTE GRAFICO' in df_reporte.columns and 'CANTIDAD DE ALUMNOS' in df_reporte.columns:
            df_rep = df_reporte.dropna(subset=['REPORTE GRAFICO']).copy()
            
            # Asignación explícita de colores del semáforo
            color_map = {
                'Verde (80% - 100%)': '#2ecc71',   # Verde
                'Amarillo (60% - 79%)': '#f1c40f',  # Amarillo
                'Rojo (Menor a 60%)': '#e74c3c'     # Rojo
            }
            
            # Mostrar luces del semáforo en tarjetas superiores
            col_g, col_y, col_r = st.columns(3)
            
            for idx, row in df_rep.iterrows():
                cat = str(row['REPORTE GRAFICO'])
                cant = row['CANTIDAD DE ALUMNOS']
                if 'Verde' in cat:
                    col_g.metric("🟢 Alta Asistencia (80% - 100%)", f"{cant} Alumnos")
                elif 'Amarillo' in cat:
                    col_y.metric("🟡 Asistencia Media (60% - 79%)", f"{cant} Alumnos")
                elif 'Rojo' in cat:
                    col_r.metric("🔴 Riesgo Crítico (< 60%)", f"{cant} Alumnos")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Gráfico de barras horizontales tipo semáforo
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
            fig_semaforo.update_layout(
                showlegend=False,
                xaxis_title="Cantidad de Alumnos",
                yaxis_title="Rango de Asistencia",
                height=300
            )
            
            st.plotly_chart(fig_semaforo, use_container_width=True)

        st.markdown("---")
        
        # 3. TABLA DE ESTUDIANTES EN RIESGO CRÍTICO
        st.subheader("⚠️ Estudiantes en Riesgo de Deserción")
        st.dataframe(
            df_alertas_limpio, 
            use_container_width=True, 
            hide_index=True
        )
                
    # --- MÓDULO 2: CARGA DE ASISTENCIA Y CALIFICACIONES ---
    elif menu_seleccionado == "📝 Cargar Asistencia / Notas":
        st.title("📝 Gestión y Registro de Datos Escolares")
        
        tab_asistencia, tab_notas = st.tabs(["📋 Asistencia", "✏️ Calificaciones"])

        with tab_asistencia:
            st.subheader("Carga de asistencia")
            st.link_button("🔗 Abrir Formulario de Asistencia (Google Forms)", "https://docs.google.com/forms/d/e/1FAIpQLSc46TWUXwAdRfPggqiuhDhaEyrvpw1W04NdzpcZ7jGAOgDF5g/viewform?usp=dialog")
            st.markdown("---")

        with tab_notas:
            st.subheader("Carga de Calificaciones Trimestrales")
            col_m, col_t = st.columns(2)
            st.link_button("🔗 Abrir Formulario de notas (Google Forms)", "https://docs.google.com/forms/d/e/1FAIpQLSdqJ8wLoft_ujZrcCfwymKZjj5SICRyn-hsEGsT7J5qnbr_tw/viewform?usp=dialog")
            st.markdown("---")
            
    # --- MÓDULO 3: LEGAJO DE ALUMNOS ---
    elif menu_seleccionado == "👥 Legajo de Alumnos":
        st.title("👥 Base de Datos de Alumnos")
        
        # 1. Filtramos las columnas útiles hasta "Causa de Abandono" (eliminando las que empiezan por Unnamed)
        columnas_padron = [c for c in df_alumnos.columns if not str(c).startswith('Unnamed')]
        df_alumnos_limpio = df_alumnos[columnas_padron].copy()
        
        # 2. Filtro por Grado en la barra lateral
        grados = ["Todos"] + list(df_alumnos_limpio['Grado y Sección Actual'].dropna().unique()) if 'Grado y Sección Actual' in df_alumnos_limpio.columns else ["Todos"]
        grado_sel = st.sidebar.selectbox("Filtrar por Grado:", grados)
        
        if grado_sel != "Todos":
            df_alumnos_limpio = df_alumnos_limpio[df_alumnos_limpio['Grado y Sección Actual'] == grado_sel]
            
        # 3. Formatear la fecha 'Año de Ingreso' si se lee como timestamp
        if 'Año de Ingreso' in df_alumnos_limpio.columns:
            df_alumnos_limpio['Año de Ingreso'] = df_alumnos_limpio['Año de Ingreso'].apply(
                lambda x: x.strftime('%d/%m/%Y') if hasattr(x, 'strftime') else str(x)
            )

        # 4. Mostrar el padrón limpio en pantalla
        st.dataframe(
            df_alumnos_limpio, 
            use_container_width=True,
            hide_index=True
        )

    # --- MÓDULO 4: REGISTRO DE ASISTENCIA ---
    elif menu_seleccionado == "📅 Planilla de Asistencia":
        st.title("📅 Planilla de Asistencia")
        
        # 1. Identificar columna de estudiante y lista de fechas
        col_nombre = df_asistencia.columns[1] if len(df_asistencia.columns) > 1 else df_asistencia.columns[0]
        cols_fechas = [c for c in df_asistencia.columns if not str(c).startswith('Unnamed') and c != col_nombre and "porcentaje" not in str(c).lower()]
        
        # Diccionario con fechas formateadas a DD/MM/YYYY
        fechas_dict = {}
        for c in cols_fechas:
            nombre_f = c.strftime('%d/%m/%Y') if hasattr(c, 'strftime') else str(c).split()[0]
            fechas_dict[nombre_f] = c

        # 2. Selector del tipo de vista vertical
        modo_vista = st.radio(
            "Seleccione el modo de visualización vertical:",
            ["📅 Ver por Fecha", "👤 Ver por Estudiante", "📊 Planilla Completa"],
            horizontal=True
        )
        
        st.markdown("---")

        # VISTA 1: POR FECHA (Pase de Lista del día)
        if modo_vista == "📅 Ver por Fecha":
            fecha_sel_nombre = st.selectbox("Seleccione la Fecha:", list(fechas_dict.keys()))
            col_fecha_real = fechas_dict[fecha_sel_nombre]
            
            # Filtrar DataFrame vertical
            df_vertical_fecha = df_asistencia[[col_nombre, col_fecha_real]].copy()
            df_vertical_fecha.columns = ["Estudiante", f"Estado de Asistencia ({fecha_sel_nombre})"]
            df_vertical_fecha = df_vertical_fecha.dropna(subset=["Estudiante"])
            
            # Resumen del día
            presentes = len(df_vertical_fecha[df_vertical_fecha.iloc[:, 1].astype(str).str.lower().isin(['presente', 'tardanza'])])
            ausentes = len(df_vertical_fecha[df_vertical_fecha.iloc[:, 1].astype(str).str.lower() == 'ausente'])
            
            k1, k2 = st.columns(2)
            k1.metric("Presentes / Tardanzas", f"{presentes} Alumnos")
            k2.metric("Ausentes", f"{ausentes} Alumnos")
            
            st.dataframe(df_vertical_fecha, use_container_width=True, hide_index=True)

        # VISTA 2: POR ESTUDIANTE (Historial cronológico vertical)
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

        # VISTA 3: MATRIZ COMPLETA
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
            
    # --- MÓDULO 5: CONSULTA FAMILIAS / BOLETÍN ---
    elif menu_seleccionado == "🔍 Consulta de Boletín / Legajo":
        st.title("🔍 Consulta Individual de Estudiante")
        dni_ingresado = st.number_input("Ingrese DNI del Alumno:", step=1, value=0)
        
        if dni_ingresado > 0:
            alumno = df_alumnos[df_alumnos['DNI'] == dni_ingresado] if 'DNI' in df_alumnos.columns else pd.DataFrame()
            
            if not alumno.empty:
                nombre = alumno.iloc[0]['Apellido y Nombre']
                grado = alumno.iloc[0]['Grado y Sección Actual']
                estado = alumno.iloc[0]['Estado de Matrícula']
                
                st.success(f"**Estudiante:** {nombre}")
                st.info(f"**Grado:** {grado} | **Estado:** {estado}")
                
                # --- A. RESUMEN Y MÉTRICAS DE ASISTENCIA ---
                st.subheader("📊 Resumen Anual de Asistencia")
                
                col_nombre_asist = df_asistencia.columns[1] if len(df_asistencia.columns) > 1 else df_asistencia.columns[0]
                asist_row = df_asistencia[df_asistencia[col_nombre_asist] == nombre]
                
                if not asist_row.empty:
                    cols_fechas = [c for c in df_asistencia.columns if not str(c).startswith('Unnamed') and c != col_nombre_asist and "porcentaje" not in str(c).lower()]
                    
                    valores_asist = asist_row[cols_fechas].values.flatten()
                    
                    presentes = sum(1 for v in valores_asist if str(v).strip().lower() in ['presente', 'tardanza'])
                    ausentes = sum(1 for v in valores_asist if str(v).strip().lower() == 'ausente')
                    total_dias = presentes + ausentes
                    
                    pct_final = (presentes / total_dias * 100) if total_dias > 0 else 0.0
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Asistencias Totales", f"{presentes} días")
                    m2.metric("Inasistencias / Ausencias", f"{ausentes} días", delta_color="inverse")
                    m3.metric("Total Días Registrados", f"{total_dias} días")
                    m4.metric("% Promedio Anual Asistencia", f"{pct_final:.2f}%".replace('.', ','))
                else:
                    st.warning("No se encontraron registros de asistencia para este estudiante.")

                st.markdown("---")

                # --- B. BOLETÍN Y NOTAS ---
                st.subheader("📝 Boletín de Calificaciones")
                
                if 'df_notas' in locals() or 'df_notas' in globals():
                    col_alumno_notas = df_notas.columns[0]
                    notas_row = df_notas[df_notas[col_alumno_notas] == nombre]
                    
                    if not notas_row.empty:
                        materia_actual = None
                        cols_boletin = {}
                        
                        for col in df_notas.columns[1:]:
                            if not str(col).startswith('Unnamed'):
                                materia_actual = col
                            trimestre = df_notas.iloc[0][col] if pd.notnull(df_notas.iloc[0][col]) else ""
                            
                            val_nota = notas_row.iloc[0][col]
                            if pd.notnull(val_nota) and str(val_nota) != str(df_notas.iloc[0][col]):
                                nombre_campo = f"{materia_actual} ({trimestre})" if trimestre else str(materia_actual)
                                cols_boletin[nombre_campo] = val_nota

                        if cols_boletin:
                            df_boletin = pd.DataFrame(list(cols_boletin.items()), columns=["Asignatura / Período", "Calificación"])
                            st.dataframe(df_boletin, use_container_width=True, hide_index=True)
                        else:
                            st.info("No hay calificaciones cargadas aún para este período.")
                    else:
                        st.warning("No se registran calificaciones en el boletín para este alumno.")
                else:
                    st.error("No se pudo cargar la hoja de notas desde la planilla.")

            else:
                st.warning("No se encontró ningún estudiante con el DNI ingresado.")

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
# 1. BASE DE DATOS DE USUARIOS Y ROLES (Simulada para demostración)
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
    
    # Carga de hojas específicas
    df_alumnos = pd.read_csv(f"{base_url}BD_Alumnos")
    df_asistencia = pd.read_csv(f"{base_url}Asistencia")
    df_reporte = pd.read_csv(f"{base_url}Reporte%20Gr%C3%A1fico%20Asistencia")
    df_alertas = pd.read_csv(f"{base_url}Alertas")
    
    return df_alumnos, df_asistencia, df_reporte, df_alertas

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
        df_alumnos, df_asistencia, df_reporte, df_alertas = load_all_data(SHEET_ID)
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
    # 4. RUTEO DE MENÚ SEGÚN EL ROL DE USUARIO
    # -------------------------------------------------------------------
    if st.session_state.user_role == "Director/a":
        opciones_menu = [
            "📊 Dashboard & Alertas", 
            "👥 Padrón de Alumnos", 
            "📅 Registro de Asistencia", 
            "📝 Cargar Asistencia / Notas",
            "🔍 Consulta de Boletín / Legajo"
        ]
    elif st.session_state.user_role == "Docente":
        opciones_menu = [
            "📝 Cargar Asistencia / Notas", 
            "📅 Registro de Asistencia", 
            "👥 Padrón de Alumnos"
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
        st.title("📊 Panel Institucional y Alertas Tempranas")
        
        # Indicadores numéricos principales
        c1, c2, c3 = st.columns(3)
        c1.metric("Matrícula Total", len(df_alumnos))
        cursando_count = len(df_alumnos[df_alumnos['Estado de Matrícula'] == 'Cursando']) if 'Estado de Matrícula' in df_alumnos.columns else len(df_alumnos)
        c2.metric("Alumnos Cursando", cursando_count)
        
        # Filtro de alertas
        alertas_filtradas = df_alertas.dropna(how='all')
        c3.metric("Casos en Riesgo (<60%)", len(alertas_filtradas) - 2 if len(alertas_filtradas) > 2 else 0)
        
        st.markdown("---")
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("⚠️ Estudiantes en Riesgo de Deserción")
            st.dataframe(alertas_filtradas, use_container_width=True)
            
        with col_right:
            st.subheader("📈 Semáforo de Asistencia Global")
            if 'REPORTE GRAFICO' in df_reporte.columns and 'CANTIDAD DE ALUMNOS' in df_reporte.columns:
                fig = px.pie(
                    df_reporte, 
                    names='REPORTE GRAFICO', 
                    values='CANTIDAD DE ALUMNOS',
                    color_discrete_sequence=['#2ecc71', '#f1c40f', '#e74c3c'],
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)

    # --- MÓDULO 2: CARGA DE ASISTENCIA Y CALIFICACIONES ---
    elif menu_seleccionado == "📝 Cargar Asistencia / Notas":
        st.title("📝 Gestión y Registro de Datos Escolares")
        
        tab_asistencia, tab_notas = st.tabs(["📋 Toma de Asistencia", "✏️ Registro de Calificaciones"])
        
        with tab_asistencia:
            st.subheader("Carga de asistencia")
            #st.info("Puedes usar la carga directa desde la app o ingresar mediante el Google Form oficial de la institución.")
            
            # Enlace/acceso rápido al Google Forms institucional
            st.link_button("🔗 Abrir Formulario de Asistencia (Google Forms)", "https://docs.google.com/forms/d/e/1FAIpQLSc46TWUXwAdRfPggqiuhDhaEyrvpw1W04NdzpcZ7jGAOgDF5g/viewform?usp=dialog")
            st.markdown("---")
            
            '''with st.form("form_registro_asistencia"):
                fecha = st.date_input("Fecha de registro")
                grado = st.selectbox("Grado y Sección", ["1° A Mañana", "1° B Mañana", "1° C Tarde"])
                alumnos_ausentes = st.text_area("Estudiantes Ausentes / Observaciones", placeholder="Ej: Vargas Alex, Aguirre Alma...")
                
                if st.form_submit_button("Guardar Asistencia"):
                    st.success(f"Asistencia de {grado} guardada para la fecha {fecha}.")'''

        with tab_notas:
            st.subheader("Carga de Calificaciones Trimestrales")
            col_m, col_t = st.columns(2)
            materia = col_m.selectbox("Materia", ["Lengua", "Matemática", "Educación Física"])
            trimestre = col_t.selectbox("Trimestre", ["1er trimestre", "2do trimestre", "3er trimestre"])

            # Enlace/acceso rápido al Google Forms institucional
            st.link_button("🔗 Abrir Formulario de notas (Google Forms)", "https://docs.google.com/forms/d/e/1FAIpQLSdqJ8wLoft_ujZrcCfwymKZjj5SICRyn-hsEGsT7J5qnbr_tw/viewform?usp=dialog")
            st.markdown("---")
            
            # Formulario interactivo tipo planilla
            df_notas_grid = df_alumnos[['DNI', 'Apellido y Nombre', 'Grado y Sección Actual']].copy()
            df_notas_grid['Nota'] = "Muy bien"
            
            edited_df = st.data_editor(
                df_notas_grid,
                column_config={
                    "Nota": st.column_config.SelectboxColumn(
                        "Calificación",
                        options=["Excelente", "Muy bien", "Bien", "Regular", "Insuficiente"],
                        required=True
                    )
                },
                disabled=["DNI", "Apellido y Nombre", "Grado y Sección Actual"],
                hide_index=True,
                use_container_width=True
            )
            
            if st.button("💾 Guardar Calificaciones"):
                st.success(f"Notas guardadas con éxito para {materia} ({trimestre}).")

    # --- MÓDULO 3: PADRÓN DE ALUMNOS ---
    elif menu_seleccionado == "👥 Padrón de Alumnos":
        st.title("👥 Base de Datos General de Estudiantes")
        
        grados = ["Todos"] + list(df_alumnos['Grado y Sección Actual'].dropna().unique()) if 'Grado y Sección Actual' in df_alumnos.columns else ["Todos"]
        grado_sel = st.sidebar.selectbox("Filtrar por Grado:", grados)
        
        df_display = df_alumnos.copy()
        if grado_sel != "Todos":
            df_display = df_display[df_display['Grado y Sección Actual'] == grado_sel]
            
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- MÓDULO 4: REGISTRO DE ASISTENCIA ---
    elif menu_seleccionado == "📅 Registro de Asistencia":
        st.title("📅 Matriz General de Presentismo")
        st.dataframe(df_asistencia, use_container_width=True)

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
                
                if 'Porcentaje de asistencia' in df_asistencia.columns:
                    asist_row = df_asistencia[df_asistencia['Apellido y Nombre \\ Fecha'] == nombre]
                    if not asist_row.empty:
                        pct = asist_row.iloc[0]['Porcentaje de asistencia'] * 100
                        st.metric("Asistencia Acumulada", f"{pct:.1f}%")
            else:
                st.warning("No se encontró ningún estudiante con el DNI ingresado.")

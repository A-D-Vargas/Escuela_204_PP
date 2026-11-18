# 🏫 Sistema Integrado de Gestión Escolar

Plataforma web institucional desarrollada en **Python** y **Streamlit** para la automatización, control y análisis de datos escolares. El sistema centraliza la gestión académica, la asistencia diaria y el seguimiento de trayectorias estudiantiles mediante la integración con Google Sheets y Google Forms.

---

## 🚀 Características Principales

* **Panel Institucional & Semáforo de Asistencia:** 
  * Indicadores en tiempo real (Matrícula total, alumnos cursando y casos críticos).
  * Clasificación automática del rendimiento de asistencia por niveles (Verde, Amarillo y Rojo).
  * Identificación temprana de estudiantes en riesgo de deserción y guía visual de medidas sugeridas.
* **Control de Asistencia Inteligente:**
  * Visualización flexible por fecha, por estudiante individual o en formato de planilla completa con cálculo automático de porcentajes.
* **Boletín de Calificaciones Modular:**
  * Ingesta centralizada de notas unificadas por asignaturas con consulta histórica por ciclo lectivo.
* **Gestión de Legajos y Matrícula:**
  * Padrón de alumnos con filtros dinámicos por grado y sección.
* **Autenticación Basada en Roles (RBAC):**
  * Accesos diferenciados para **Directivos/Administradores**, **Docentes** y **Familias/Alumnos** (con soporte para múltiples vínculos de DNI por cuenta familiar).
* **Documentación Integrada:**
  * Acceso directo al formulario de carga institucional y descarga del Manual de Usuario en formato PDF.

---

## 🛠️ Stack Tecnológico

* **Frontend & Interfaz:** [Streamlit](https://streamlit.io/)
* **Procesamiento de Datos:** [Pandas](https://pandas.pydata.org/)
* **Visualización de Datos:** [Plotly](https://plotly.com/python/)
* **Base de Datos & Ingesta:** Google Sheets / Google Forms (Arquitectura en la nube)
* **Despliegue:** Streamlit Community Cloud & GitHub

---

## 📂 Estructura del Repositorio

```text
├── app.py                  # Código principal de la aplicación Streamlit
├── requirements.txt        # Dependencias y librerías del proyecto
├── manual_usuario.pdf      # Manual oficial para usuarios del sistema
├── medidas_sugeridas.jpg   # Infografía de abordaje institucional para el Dashboard
└── README.md               # Documentación del proyecto
```
---
# ⚙️ Instalación y Ejecución Local
1. Clona este repositorio en tu computadora:
* git clone [https://github.com/A-D-Vargas/Escuela_204_PP.git](https://github.com/A-D-Vargas/Escuela_204_PP.git)
2. Entra a la carpeta del proyecto:
* cd Escuela_204_PP
3. Instala las dependencias necesarias indicadas en el archivo requirements.txt:
* pip install -r requirements.txt
4. Ejecuta la aplicación de Streamlit:
* streamlit run app.py
---
# Autores:
* Sosa Ramiro
* Vargas Alex
* Galeano Mariela

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Inventario Cloud", layout="centered")

st.title("📦 Mi Inventario en Google Sheets")

# Tu URL compartida
url = "https://docs.google.com/spreadsheets/d/1rs3Ud8JPZOcIi445JaheKbkYCWR0nPieQS51AKXPTNY/edit?usp=sharing"

# Crear la conexión
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leer los datos de la hoja
    # ttl=0 sirve para que los datos se actualicen cada vez que recargas
    df = conn.read(spreadsheet=url, ttl=0)
    
    # Limpiar posibles errores de carga
    df = df.dropna(how="all") 

    st.subheader("Lista de Productos")
    st.dataframe(df, use_container_width=True)

    # Mostrar métricas rápidas
    if not df.empty:
        total_productos = len(df)
        stock_total = df['cantidad'].sum() if 'cantidad' in df.columns else 0
        
        col1, col2 = st.columns(2)
        col1.metric("Variedad de Productos", total_productos)
        col2.metric("Total Unidades en Stock", int(stock_total))

except Exception as e:
    st.error("No se pudo leer la hoja de cálculo.")
    st.info("Revisa que la hoja tenga los encabezados: nombre, cantidad, precio")
    st.write("Error técnico:", e)
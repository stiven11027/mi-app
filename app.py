import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- FUNCIONES DE BASE DE DATOS ---
def conectar():
    return sqlite3.connect('inventario.db')

def crear_db():
    conn = conectar()
    c = conn.cursor()
    # Tabla de Productos
    c.execute('''CREATE TABLE IF NOT EXISTS productos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT UNIQUE, 
                  cantidad INTEGER, 
                  precio REAL)''')
    # Tabla de Historial de Ventas
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  producto TEXT, 
                  cantidad INTEGER, 
                  total REAL, 
                  fecha TEXT)''')
    conn.commit()
    conn.close()

def registrar_venta(nombre, cantidad_vendida):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT cantidad, precio FROM productos WHERE nombre = ?", (nombre,))
    resultado = c.fetchone()
    
    if resultado and resultado[0] >= cantidad_vendida:
        precio_unitario = resultado[1]
        nuevo_stock = resultado[0] - cantidad_vendida
        total_venta = cantidad_vendida * precio_unitario
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Restar del inventario
        c.execute("UPDATE productos SET cantidad = ? WHERE nombre = ?", (nuevo_stock, nombre))
        # 2. Guardar en historial
        c.execute("INSERT INTO ventas (producto, cantidad, total, fecha) VALUES (?, ?, ?, ?)",
                  (nombre, cantidad_vendida, total_venta, fecha_actual))
        
        conn.commit()
        conn.close()
        return True, f"Venta exitosa: ${total_venta:.2f}"
    else:
        conn.close()
        return False, "Stock insuficiente."

# --- INTERFAZ ---
crear_db()
st.set_page_config(page_title="Punto de Venta", layout="wide")

st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Ir a:", ["📊 Tablero Principal", "📦 Inventario", "💰 Realizar Venta", "📜 Historial"])

if opcion == "📊 Tablero Principal":
    st.title("Resumen del Negocio")
    conn = conectar()
    df_v = pd.read_sql_query("SELECT * FROM ventas", conn)
    df_p = pd.read_sql_query("SELECT * FROM productos", conn)
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Ventas Totales", f"${df_v['total'].sum():.2f}")
    col2.metric("Productos en Stock", len(df_p))
    col3.metric("Unidades Vendidas", df_v['cantidad'].sum())

    st.subheader("Ventas por Día")
    if not df_v.empty:
        df_v['fecha'] = pd.to_datetime(df_v['fecha'])
        ventas_diarias = df_v.groupby(df_v['fecha'].dt.date)['total'].sum()
        st.line_chart(ventas_diarias)

elif opcion == "📦 Inventario":
    st.title("Gestión de Productos")
    # Formulario para agregar (como el anterior)
    with st.expander("➕ Agregar nuevo producto"):
        with st.form("add"):
            n = st.text_input("Nombre")
            c = st.number_input("Cantidad", min_value=1)
            p = st.number_input("Precio", min_value=0.1)
            if st.form_submit_button("Guardar"):
                conn = conectar()
                conn.execute("INSERT OR REPLACE INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)", (n, c, p))
                conn.commit()
                conn.close()
                st.success("Actualizado")
    
    df = pd.read_sql_query("SELECT * FROM productos", conectar())
    st.table(df)

elif opcion == "💰 Realizar Venta":
    st.title("Punto de Venta")
    df_p = pd.read_sql_query("SELECT nombre FROM productos WHERE cantidad > 0", conectar())
    if not df_p.empty:
        prod = st.selectbox("Producto", df_p['nombre'])
        cant = st.number_input("Cantidad", min_value=1)
        if st.button("Cobrar"):
            exito, msj = registrar_venta(prod, cant)
            if exito: st.success(msj)
            else: st.error(msj)
    else:
        st.warning("No hay mercancía.")

elif opcion == "📜 Historial":
    st.title("Historial de Ventas")
    df_v = pd.read_sql_query("SELECT * FROM ventas ORDER BY fecha DESC", conectar())
    st.dataframe(df_v, use_container_width=True)
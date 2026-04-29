import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuración de la página para móvil
st.set_page_config(page_title="Despacho Salvador Glez", layout="centered")

def conectar_db():
    conn = sqlite3.connect('despacho_juridico.db', check_same_thread=False)
    return conn

# Inicialización de tablas
conn = conectar_db()
conn.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY, nombre TEXT, rfc TEXT)')
conn.execute('CREATE TABLE IF NOT EXISTS expedientes (id INTEGER PRIMARY KEY, num TEXT, cliente_id INTEGER)')

# --- INTERFAZ MÓVIL ---
st.title("⚖️ Gestión Jurídica")
st.sidebar.header(f"Abogado: Salvador Gonzalez\nCédula: [Tu Cédula]")

menu = ["Buscador", "Nuevo Cliente", "Registrar Expediente"]
choice = st.sidebar.selectbox("Menú", menu)

if choice == "Buscador":
    st.subheader("🔍 Buscar Cliente o Caso")
    busqueda = st.text_input("Nombre o RFC")
    if busqueda:
        df = pd.read_sql_query(f"SELECT * FROM clientes WHERE nombre LIKE '%{busqueda}%'", conn)
        st.dataframe(df, use_container_width=True)

elif choice == "Nuevo Cliente":
    st.subheader("➕ Registro de Cliente")
    nombre = st.text_input("Nombre Completo")
    rfc = st.text_input("RFC")
    if st.button("Guardar"):
        conn.execute("INSERT INTO clientes (nombre, rfc) VALUES (?,?)", (nombre, rfc))
        conn.commit()
        st.success("Cliente guardado")
import pandas as pd # Para manejo de datos y Excel
from datetime import datetime

def generar_reporte_excel():
    conn = sqlite3.connect('despacho_juridico.db')
    
    # Consulta compleja que une Clientes, Expedientes y Agenda
    query = '''
        SELECT c.nombre AS Cliente, e.num_expediente AS Expediente, 
               e.juzgado AS Juzgado, a.evento AS Pendiente, a.fecha_vencimiento AS Fecha
        FROM clientes c
        JOIN expedientes e ON c.id = e.cliente_id
        LEFT JOIN agenda a ON e.id = a.expediente_id
        WHERE a.estado = 'Pendiente'
    '''
    
    df = pd.read_sql_query(query, conn)
    nombre_archivo = f"Reporte_Casos_{datetime.now().strftime('%d_%m_%Y')}.xlsx"
    
    # Exportación con formato
    df.to_excel(nombre_archivo, index=False)
    conn.close()
    print(f"Reporte generado exitosamente: {nombre_archivo}")
from datetime import datetime

def calcular_dias_restantes(fecha_vencimiento):
    hoy = datetime.now().date()
    vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
    delta = (vencimiento - hoy).days
    
    if delta < 0:
        return "VENCIDO", "#FF0000" # Rojo
    elif delta <= 3:
        return f"URGENTE ({delta} días)", "#FF8C00" # Naranja
    else:
        return f"{delta} días restantes", "#008000" # Verde
def actualizar_db_agenda():
    conn = sqlite3.connect('despacho_juridico.db')
    cursor = conn.cursor()
    # Tabla para términos legales y audiencias
    cursor.execute('''CREATE TABLE IF NOT EXISTS agenda (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        evento TEXT, 
                        fecha_vencimiento DATE, 
                        expediente_id INTEGER,
                        estado TEXT DEFAULT 'Pendiente',
                        FOREIGN KEY(expediente_id) REFERENCES expedientes(id))''')
    conn.commit()
    conn.close()
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# --- CONFIGURACIÓN E INICIALIZACIÓN DE DATOS ---
def inicializar_sistema():
    conn = sqlite3.connect('despacho_juridico.db')
    cursor = conn.cursor()
    
    # Tabla de Perfil (Abogado Patrono)
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfil (
                        id INTEGER PRIMARY KEY,
                        nombre TEXT, 
                        cedula TEXT)''')
    
    # Insertar datos iniciales del titular
    cursor.execute("INSERT OR IGNORE INTO perfil (id, nombre, cedula) VALUES (1, 'Salvador Gonzalez Zuazo', 'CEDULA_POR_DEFINIR')")
    
    # Tabla de Clientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL, rfc TEXT, curp TEXT, domicilio TEXT)''')
    
    # Tabla de Expedientes (Vinculada a Clientes)
    cursor.execute('''CREATE TABLE IF NOT EXISTS expedientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        num_expediente TEXT UNIQUE, juzgado TEXT, cliente_id INTEGER,
                        FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')
    
    conn.commit()
    conn.close()

# --- INTERFAZ PROFESIONAL ---
class AppLegal:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión Jurídica - Salvador Gonzalez Zuazo")
        self.root.geometry("900x700")
        
        # --- ENCABEZADO DE PERFIL ---
        self.frame_perfil = tk.Frame(root, bg="#f0f0f0", pading=10)
        self.frame_perfil.pack(fill=tk.X)
        self.actualizar_etiqueta_perfil()

        # --- BUSCADOR ---
        tk.Label(root, text="Buscar Cliente (Nombre o RFC):", font=("Arial", 10, "bold")).pack(pady=5)
        self.entry_busqueda = tk.Entry(root, width=60)
        self.entry_busqueda.pack(pady=5)
        tk.Button(root, text="🔍 Buscar", command=self.ejecutar_busqueda).pack(pady=5)

        # --- TABLA DE RESULTADOS ---
        self.tabla = ttk.Treeview(root, columns=("ID", "Nombre", "RFC", "CURP"), show='headings')
        self.tabla.heading("ID", text="ID"); self.tabla.heading("Nombre", text="Nombre")
        self.tabla.heading("RFC", text="RFC"); self.tabla.heading("CURP", text="CURP")
        self.tabla.pack(pady=10, fill=tk.BOTH, expand=True)

        # --- ACCIONES ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="➕ Nuevo Cliente", command=self.ventana_cliente, width=20).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="📂 Vincular Expediente", command=self.ventana_expediente, width=20, bg="#e1e1e1").grid(row=0, column=1, padx=5)

    def actualizar_etiqueta_perfil(self):
        conn = sqlite3.connect('despacho_juridico.db')
        res = conn.execute("SELECT nombre, cedula FROM perfil WHERE id=1").fetchone()
        conn.close()
        texto = f"Abogado Patrono: {res[0]} | Cédula: {res[1]}"
        tk.Label(self.frame_perfil, text=texto, font=("Arial", 9, "italic"), bg="#f0f0f0").pack(side=tk.LEFT)

    def ejecutar_busqueda(self):
        criterio = f"%{self.entry_busqueda.get()}%"
        conn = sqlite3.connect('despacho_juridico.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rfc, curp FROM clientes WHERE nombre LIKE ? OR rfc LIKE ?", (criterio, criterio))
        for item in self.tabla.get_children(): self.tabla.delete(item)
        for row in cursor.fetchall(): self.tabla.insert("", tk.END, values=row)
        conn.close()

    def ventana_cliente(self):
        v = tk.Toplevel(self.root); v.title("Registro de Cliente")
        campos = ["Nombre Completo", "RFC", "CURP", "Domicilio"]
        entradas = {}
        for campo in campos:
            tk.Label(v, text=campo).pack()
            e = tk.Entry(v, width=40); e.pack(); entradas[campo] = e
        
        def guardar():
            conn = sqlite3.connect('despacho_juridico.db')
            conn.execute("INSERT INTO clientes (nombre, rfc, curp, domicilio) VALUES (?,?,?,?)",
                         (entradas["Nombre Completo"].get(), entradas["RFC"].get(), entradas["CURP"].get(), entradas["Domicilio"].get()))
            conn.commit(); conn.close()
            v.destroy(); self.ejecutar_busqueda()
        
        tk.Button(v, text="Guardar Cliente", command=guardar, bg="green", fg="white").pack(pady=10)

    def ventana_expediente(self):
        item = self.tabla.selection()
        if not item: return messagebox.showwarning("Error", "Selecciona un cliente")
        c_id = self.tabla.item(item)['values'][0]
        
        v = tk.Toplevel(self.root); v.title("Nuevo Expediente")
        tk.Label(v, text="Número de Expediente:").pack()
        exp_e = tk.Entry(v); exp_e.pack()
        tk.Label(v, text="Juzgado / Autoridad:").pack()
        juz_e = tk.Entry(v); juz_e.pack()
        
        def guardar():
            conn = sqlite3.connect('despacho_juridico.db')
            conn.execute("INSERT INTO expedientes (num_expediente, juzgado, cliente_id) VALUES (?,?,?)",
                         (exp_e.get(), juz_e.get(), c_id))
            conn.commit(); conn.close()
            v.destroy(); messagebox.showinfo("Éxito", "Expediente vinculado.")
            
        tk.Button(v, text="Registrar", command=guardar).pack(pady=10)

if __name__ == "__main__":
    inicializar_sistema()
    root = tk.Tk()
    app = AppLegal(root)
    root.mainloop()
def obtener_datos_patrono():
    conn = sqlite3.connect('despacho_juridico.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_titular, cedula_profesional FROM perfil_abogado WHERE id = 1")
    perfil = cursor.fetchone()
    conn.close()
    return perfil # Retorna (Nombre, Cédula)

# Ejemplo de uso en la interfaz:
nombre, cedula = obtener_datos_patrono()
print(f"Abogado Patrono: {nombre}\nCédula Profesional: {cedula}")
def actualizar_db_perfil():
    conn = sqlite3.connect('despacho_juridico.db')
    cursor = conn.cursor()
    
    # Tabla para tus datos profesionales
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfil_abogado (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre_titular TEXT,
                        cedula_profesional TEXT,
                        despacho_nombre TEXT)''')
    
    # Insertar tus datos por defecto (puedes cambiarlos luego desde la app)
    cursor.execute("INSERT OR IGNORE INTO perfil_abogado (id, nombre_titular, cedula_profesional) VALUES (1, 'Salvador Gonzalez Zuazo', 'PENDIENTE')")
    
    conn.commit()
    conn.close()
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# --- LÓGICA DE BASE DE DATOS ---
def iniciar_db():
    conn = sqlite3.connect('despacho_juridico.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT, rfc TEXT, curp TEXT, domicilio TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS expedientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        num_expediente TEXT, juzgado TEXT, cliente_id INTEGER,
                        FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')
    conn.commit()
    conn.close()

# --- INTERFAZ GRÁFICA (GUI) ---
class AppDespacho:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Jurídica - Salvador Gonzalez")
        self.root.geometry("800x600")
        
        # Panel de Búsqueda
        tk.Label(root, text="Buscador de Clientes (Nombre o RFC):").pack(pady=5)
        self.entry_busqueda = tk.Entry(root, width=50)
        self.entry_busqueda.pack(pady=5)
        tk.Button(root, text="Buscar", command=self.buscar).pack(pady=5)
        
        # Tabla de Resultados
        self.tree = ttk.Treeview(root, columns=("ID", "Nombre", "RFC"), show='headings')
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("RFC", text="RFC")
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Botón para vincular expediente
        tk.Button(root, text="Vincular Nuevo Expediente a Selección", 
                  command=self.ventana_expediente, bg="#4CAF50", fg="white").pack(pady=10)

    def buscar(self):
        criterio = self.entry_busqueda.get()
        conn = sqlite3.connect('despacho_juridico.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rfc FROM clientes WHERE nombre LIKE ? OR rfc LIKE ?", 
                       (f'%{criterio}%', f'%{criterio}%'))
        for i in self.tree.get_children(): self.tree.delete(i)
        for row in cursor.fetchall(): self.tree.insert("", tk.END, values=row)
        conn.close()

    def ventana_expediente(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona un cliente primero")
            return
        
        cliente_id = self.tree.item(seleccion)['values'][0]
        ventana = tk.Toplevel(self.root)
        ventana.title("Nuevo Expediente")
        
        tk.Label(ventana, text="Número de Expediente:").pack()
        exp_ent = tk.Entry(ventana)
        exp_ent.pack()
        
        tk.Label(ventana, text="Juzgado:").pack()
        juz_ent = tk.Entry(ventana)
        juz_ent.pack()
        
        def guardar():
            conn = sqlite3.connect('despacho_juridico.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO expedientes (num_expediente, juzgado, cliente_id) VALUES (?, ?, ?)",
                           (exp_ent.get(), juz_ent.get(), cliente_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Expediente vinculado correctamente")
            ventana.destroy()

        tk.Button(ventana, text="Guardar Registro", command=guardar).pack(pady=10)

if __name__ == "__main__":
    iniciar_db()
    root = tk.Tk()
    app = AppDespacho(root)
    root.mainloop()
import sqlite3

def buscar_cliente(criterio):
    """Busca clientes por nombre o RFC."""
    conexion = sqlite3.connect('despacho.db')
    cursor = conexion.cursor()
    # Buscamos coincidencias parciales en nombre o RFC
    query = "SELECT * FROM clientes WHERE nombre_completo LIKE ? OR rfc LIKE ?"
    cursor.execute(query, (f'%{criterio}%', f'%{criterio}%'))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def registrar_expediente(cliente_id, num_expediente, juzgado, tipo_juicio):
    """Vincula un nuevo proceso legal a un cliente existente."""
    try:
        conexion = sqlite3.connect('despacho.db')
        cursor = conexion.cursor()
        query = '''INSERT INTO casos (expediente, juzgado, tipo_juicio, cliente_id) 
                   VALUES (?, ?, ?, ?)'''
        cursor.execute(query, (num_expediente, juzgado, tipo_juicio, cliente_id))
        conexion.commit()
        print(f"Expediente {num_expediente} registrado correctamente.")
    except sqlite3.IntegrityError:
        print("Error: El número de expediente ya existe en el sistema.")
    finally:
        conexion.close()
import sqlite3

def registrar_cliente(nombre, rfc, curp, domicilio):
    try:
        conexion = sqlite3.connect('despacho.db')
        cursor = conexion.cursor()
        
        query = '''INSERT INTO clientes (nombre_completo, rfc, curp, domicilio) 
                   VALUES (?, ?, ?, ?)'''
        cursor.execute(query, (nombre, rfc, curp, domicilio))
        
        conexion.commit()
        print(f"Cliente '{nombre}' registrado con éxito.")
    except sqlite3.IntegrityError:
        print("Error: El RFC o CURP ya se encuentra registrado.")
    finally:
        conexion.close()

def listar_clientes():
    conexion = sqlite3.connect('despacho.db')
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id, nombre_completo, rfc FROM clientes")
    clientes = cursor.fetchall()
    
    conexion.close()
    return clientes
import sqlite3

def configurar_base_de_datos():
    # Creamos la conexión (se generará el archivo 'despacho.db')
    conexion = sqlite3.connect('despacho.db')
    cursor = conexion.cursor()

    # Tabla de Clientes con campos legales específicos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            rfc TEXT UNIQUE,
            curp TEXT UNIQUE,
            domicilio TEXT
        )
    ''')

    # Tabla de Casos para seguimiento judicial
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS casos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediente TEXT UNIQUE,
            juzgado TEXT,
            tipo_juicio TEXT,
            estado TEXT DEFAULT 'Activo',
            cliente_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')

    conexion.commit()
    conexion.close()
    print("Conexión establecida y tablas creadas exitosamente.")

configurar_base_de_datos()
class AppCore:
    def __init__(self):
        self.data = []

    def add_item(self, name, description):
        item = {"id": len(self.data) + 1, "name": name, "description": description}
        self.data.append(item)
        return item

    def get_all(self):
        return self.data

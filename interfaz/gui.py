from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from parser_sql import parsear_sql, tablas_cargadas
import csv
from tkinter import filedialog

# Diccionario acumulativo por tipo de índice
accesos_acumulados = {
    "SEQ": {"lecturas": 0, "escrituras": 0},
    "ISAM": {"lecturas": 0, "escrituras": 0},
    "HASH": {"lecturas": 0, "escrituras": 0},
    "BTREE": {"lecturas": 0, "escrituras": 0},
    "RTREE": {"lecturas": 0, "escrituras": 0}
}

tipo_actual_var = None  # Global para actualizar el estilo dinámicamente

def cargar_csv(area_sql):
    ruta = filedialog.askopenfilename(title="Selecciona un archivo CSV", filetypes=[("CSV files", "*.csv")])
    if not ruta:
        return

    with open(ruta, newline='', encoding='utf-8') as archivo:
        lector = csv.reader(archivo)
        filas = list(lector)

        if not filas:
            messagebox.showwarning("Vacío", "El archivo CSV no contiene datos.")
            return

        nombre_tabla = filas[0][0].split(":")[-1].strip()
        filas = filas[1:]  # saltamos la primera fila (cabecera)

        for fila in filas:
            valores = ",".join([f"'{val.strip()}'" for val in fila])
            sentencia = f"INSERT INTO {nombre_tabla} VALUES ({valores});"
            parsear_sql(sentencia)

        messagebox.showinfo("Listo", f"Se insertaron {len(filas)} registros en {nombre_tabla}.")
        
def actualizar_grafico(figura, canvas, accesos):
    figura.clf()
    ax = figura.add_subplot(111)
    ax.set_title("Accesos acumulados por estructura")
    tipos = list(accesos.keys())
    lecturas = [accesos[t]["lecturas"] for t in tipos]
    escrituras = [accesos[t]["escrituras"] for t in tipos]

    x = range(len(tipos))
    ax.bar(x, lecturas, label="Lecturas", color="skyblue")
    ax.bar(x, escrituras, bottom=lecturas, label="Escrituras", color="salmon")
    ax.set_xticks(x)
    ax.set_xticklabels(tipos)
    ax.set_ylabel("Cantidad")
    ax.legend()
    canvas.draw()


def ejecutar_sql(area_sql, tabla, figura, canvas, tipo_var):
    sentencia = area_sql.get("1.0", tk.END).strip()
    if not sentencia:
        messagebox.showwarning("Atención", "Escribe una sentencia SQL.")
        return

    respuesta = parsear_sql(sentencia)
    tabla.delete(*tabla.get_children())

    if respuesta["status"] == "ok":
        if "datos" in respuesta:
            datos = respuesta["datos"]
            if isinstance(datos, list) and datos:
                columnas = list(datos[0].keys())
            elif isinstance(datos, dict):
                columnas = list(datos.keys())
                datos = [respuesta["datos"]]
            else:
                columnas = ["Resultado"]
                datos = [{"Resultado": str(respuesta["datos"])}]

            tabla["columns"] = columnas
            for col in columnas:
                tabla.heading(col, text=col)
                tabla.column(col, width=120)

            for r in datos:
                tabla.insert("", "end", values=[r[col] for col in columnas])

        else:
            messagebox.showinfo("Éxito", respuesta["mensaje"])

        # Detectar tipo de índice desde la tabla afectada
        for tabla_nombre, info in tablas_cargadas.items():
            if tabla_nombre in sentencia:
                tipo = info["tipo"]
                tipo_var.set(f"Estilo actual: {tipo}")
                if "INSERT" in sentencia.upper():
                    accesos_acumulados[tipo]["escrituras"] += 1
                elif "SELECT" in sentencia.upper():
                    accesos_acumulados[tipo]["lecturas"] += 1
                elif "DELETE" in sentencia.upper():
                    accesos_acumulados[tipo]["escrituras"] += 1
                actualizar_grafico(figura, canvas, accesos_acumulados)
                break

    else:
        messagebox.showerror("Error", respuesta["mensaje"])


def iniciar_gui():
    global tipo_actual_var
    ventana = tk.Tk()
    ventana.title("Mini SGBD con Indexación")
    ventana.geometry("1200x720")
    ventana.config(bg="#f0f5f5")

    etiqueta = tk.Label(ventana, text="Mini Gestor de Archivos", font=("Segoe UI", 18, "bold"), bg="#f0f5f5")
    etiqueta.pack(pady=10)

    tipo_actual_var = tk.StringVar(value="Estilo actual: Ninguno")
    tipo_actual_label = tk.Label(ventana, textvariable=tipo_actual_var, font=("Segoe UI", 11), fg="gray25", bg="#f0f5f5")
    tipo_actual_label.pack()

    area_sql = scrolledtext.ScrolledText(ventana, width=120, height=8, font=("Consolas", 11))
    area_sql.pack(pady=10)

    tabla = ttk.Treeview(ventana, columns=("A", "B", "C"), show="headings", height=12)
    tabla.pack(fill="both", expand=True, padx=20, pady=10)

    # Botón ejecutar
    figura = Figure(figsize=(5, 3))
    canvas = FigureCanvasTkAgg(figura, master=ventana)
    canvas.get_tk_widget().pack(pady=10)

    boton = ttk.Button(ventana, text="Ejecutar SQL", command=lambda: ejecutar_sql(area_sql, tabla, figura, canvas, tipo_actual_var))
    boton_cargar_csv = ttk.Button(ventana, text="Cargar CSV", command=lambda: cargar_csv(area_sql))
    boton_cargar_csv.pack(pady=5)

    boton.pack(pady=5)

    ventana.mainloop()


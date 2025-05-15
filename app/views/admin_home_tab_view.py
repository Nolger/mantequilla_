# app/views/admin_home_tab_view.py
import tkinter as tk
from tkinter import ttk, messagebox

# Importar modelos necesarios
try:
    from ..models import table_model, order_model, stock_model
except ImportError:
    # Fallback para ejecución directa o estructura diferente
    try:
        from models import table_model, order_model, stock_model
    except ImportError:
        print("Error crítico: No se pudieron importar los modelos en AdminHomeTabView.")
        table_model = order_model = stock_model = None

class AdminHomeTabView(ttk.Frame):
    def __init__(self, parent_container, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container

        if not all([table_model, order_model, stock_model]):
            ttk.Label(self, text="Error: No se pueden cargar los datos del resumen (modelos no disponibles).", foreground="red").pack(pady=20)
            return

        # Variables para los labels dinámicos
        self.tables_summary_vars = {
            'libre': tk.StringVar(value="..."),
            'ocupada': tk.StringVar(value="..."),
            'reservada': tk.StringVar(value="..."),
            'mantenimiento': tk.StringVar(value="...")
        }
        self.orders_summary_vars = {
            'abierta': tk.StringVar(value="..."),
            'en preparacion': tk.StringVar(value="..."),
            'lista para servir': tk.StringVar(value="...")
        }
        self.low_stock_count_var = tk.StringVar(value="...")
        self.low_stock_items_var = tk.StringVar(value="Cargando ítems...")


        self._create_widgets()
        self.refresh_data() # Cargar datos al iniciar

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(0, weight=1) # Para que los LabelFrames se expandan
        main_frame.columnconfigure(1, weight=1)

        # --- Sección Estado de Mesas ---
        tables_lf = ttk.LabelFrame(main_frame, text="Estado Actual de Mesas", padding="10")
        tables_lf.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(tables_lf, text="Libres:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(tables_lf, textvariable=self.tables_summary_vars['libre'], font=("Arial", 11, "bold")).grid(row=0, column=1, sticky="e", pady=2, padx=5)
        ttk.Label(tables_lf, text="Ocupadas:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(tables_lf, textvariable=self.tables_summary_vars['ocupada'], font=("Arial", 11, "bold")).grid(row=1, column=1, sticky="e", pady=2, padx=5)
        ttk.Label(tables_lf, text="Reservadas:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(tables_lf, textvariable=self.tables_summary_vars['reservada'], font=("Arial", 11, "bold")).grid(row=2, column=1, sticky="e", pady=2, padx=5)
        ttk.Label(tables_lf, text="Mantenimiento:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Label(tables_lf, textvariable=self.tables_summary_vars['mantenimiento'], font=("Arial", 11, "bold")).grid(row=3, column=1, sticky="e", pady=2, padx=5)


        # --- Sección Comandas Activas ---
        orders_lf = ttk.LabelFrame(main_frame, text="Comandas Activas", padding="10")
        orders_lf.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ttk.Label(orders_lf, text="Abiertas:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(orders_lf, textvariable=self.orders_summary_vars['abierta'], font=("Arial", 11, "bold")).grid(row=0, column=1, sticky="e", pady=2, padx=5)
        ttk.Label(orders_lf, text="En Preparación:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(orders_lf, textvariable=self.orders_summary_vars['en preparacion'], font=("Arial", 11, "bold")).grid(row=1, column=1, sticky="e", pady=2, padx=5)
        ttk.Label(orders_lf, text="Listas para Servir:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(orders_lf, textvariable=self.orders_summary_vars['lista para servir'], font=("Arial", 11, "bold")).grid(row=2, column=1, sticky="e", pady=2, padx=5)

        # --- Sección Alertas de Stock Bajo ---
        stock_lf = ttk.LabelFrame(main_frame, text="Alertas de Stock", padding="10")
        stock_lf.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        ttk.Label(stock_lf, text="Ingredientes con Stock Bajo/Mínimo:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(stock_lf, textvariable=self.low_stock_count_var, font=("Arial", 11, "bold")).grid(row=0, column=1, sticky="e", pady=2, padx=5)
        
        items_label = ttk.Label(stock_lf, text="Ítems específicos:", font=("Arial", 9, "italic"))
        items_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5,0))
        
        # Usar un Text widget para mostrar la lista de ítems, ya que puede ser multilínea y con scroll
        self.low_stock_items_text = tk.Text(stock_lf, height=5, width=60, wrap=tk.WORD, relief=tk.FLAT, state=tk.DISABLED, font=("Consolas", 9))
        self.low_stock_items_text.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)
        # Opcional: Añadir un scrollbar si la lista puede ser larga
        # stock_scrollbar = ttk.Scrollbar(stock_lf, orient=tk.VERTICAL, command=self.low_stock_items_text.yview)
        # self.low_stock_items_text.configure(yscrollcommand=stock_scrollbar.set)
        # stock_scrollbar.grid(row=2, column=2, sticky="ns")


        # --- Botón de Refrescar ---
        refresh_button = ttk.Button(main_frame, text="Refrescar Datos", command=self.refresh_data)
        refresh_button.grid(row=2, column=0, columnspan=2, pady=20)


    def refresh_data(self):
        # Actualizar Resumen de Mesas
        if table_model:
            tables_data = table_model.get_tables_status_summary()
            if tables_data:
                for status, var in self.tables_summary_vars.items():
                    var.set(str(tables_data.get(status, 0)))
            else:
                for var in self.tables_summary_vars.values(): var.set("Error")
        
        # Actualizar Resumen de Comandas
        if order_model:
            orders_data = order_model.get_active_orders_summary()
            if orders_data:
                for status, var in self.orders_summary_vars.items():
                    var.set(str(orders_data.get(status, 0)))
            else:
                 for var in self.orders_summary_vars.values(): var.set("Error")

        # Actualizar Resumen de Stock Bajo
        if stock_model:
            stock_data = stock_model.get_low_stock_ingredients_summary(limit=5) # Mostrar hasta 5 ítems
            if stock_data:
                self.low_stock_count_var.set(str(stock_data.get('count', 0)))
                
                items_text_content = ""
                if stock_data['items']:
                    for item in stock_data['items']:
                        items_text_content += f"- {item['nombre_producto']}: {item['cantidad_disponible']:.2f} / {item['stock_minimo']:.2f} {item['unidad_medida']}\n"
                else:
                    items_text_content = "No hay ingredientes con stock bajo actualmente."
                
                self.low_stock_items_text.config(state=tk.NORMAL) # Habilitar para modificar
                self.low_stock_items_text.delete("1.0", tk.END)
                self.low_stock_items_text.insert("1.0", items_text_content)
                self.low_stock_items_text.config(state=tk.DISABLED) # Deshabilitar de nuevo
            else:
                self.low_stock_count_var.set("Error")
                self.low_stock_items_text.config(state=tk.NORMAL)
                self.low_stock_items_text.delete("1.0", tk.END)
                self.low_stock_items_text.insert("1.0", "Error al cargar ítems.")
                self.low_stock_items_text.config(state=tk.DISABLED)

# Para probar esta vista de forma aislada
if __name__ == '__main__':
    if not all([table_model, order_model, stock_model]):
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico", "No se pueden cargar los modelos para probar AdminHomeTabView.")
        root_error.destroy()
    else:
        root = tk.Tk()
        root.title("Prueba Pestaña Inicio Admin")
        root.geometry("700x550")
        
        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes: style.theme_use('clam')

        home_tab_view = AdminHomeTabView(root)
        home_tab_view.pack(expand=True, fill=tk.BOTH)
        root.mainloop()
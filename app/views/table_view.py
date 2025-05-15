# app/views/table_view.py
import tkinter as tk
from tkinter import ttk, messagebox # simpledialog ya no es necesario aquí para el inicio

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from ..models import table_model # Si table_model.py está en app/models/
except ImportError:
    try:
        from models import table_model # Si 'models' es un paquete accesible
    except ImportError:
        print("Error: No se pudo importar el módulo table_model.py. Verifica tu estructura y PYTHONPATH.")
        table_model = None

# Constantes para el canvas
TABLE_WIDTH = 80
TABLE_HEIGHT = 50
CANVAS_PADDING = 20
STATUS_COLORS = {
    "libre": "lightgreen",
    "ocupada": "salmon",
    "reservada": "lightblue",
    "mantenimiento": "lightgrey",
    "default": "white"
}

class TableView(ttk.Frame):
    def __init__(self, parent_container, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container
        # self.configure(padding=(10, 5)) # Padding general del frame principal

        if not table_model:
            error_label = ttk.Label(self, text="Error crítico: El modelo de mesas no está disponible.", foreground="red")
            error_label.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
            return

        # Variables para los campos del formulario
        self.table_id_var = tk.StringVar()
        self.capacity_var = tk.IntVar(value=2) # Valor inicial por defecto para capacidad
        self.location_desc_var = tk.StringVar() # Descripción textual
        self.status_var = tk.StringVar()
        self.pos_x_var = tk.IntVar(value=50) # Valor inicial por defecto
        self.pos_y_var = tk.IntVar(value=50) # Valor inicial por defecto

        self._selected_canvas_item_id = None # Para rastrear el ID del objeto de canvas seleccionado
        self._table_canvas_objects = {} # Diccionario para mapear id_mesa a IDs de objetos de canvas

        self._create_layout()
        self._load_tables_to_ui()
        # Llamar a _clear_form_fields() aquí para establecer el estado inicial del formulario,
        # pero la versión modificada ya no usará simpledialog.
        self._clear_form_fields(ask_for_position=False) # No preguntar por posición al inicio

    def _create_layout(self):
        # Frame principal que se divide en dos: izquierda (CRUD) y derecha (Canvas)
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(expand=True, fill=tk.BOTH)

        # --- Panel Izquierdo: Formulario y Lista ---
        left_panel_frame = ttk.Frame(main_paned_window, padding=(10,5))
        main_paned_window.add(left_panel_frame, weight=1) 

        self._create_form_widgets(left_panel_frame)
        self._create_treeview_widget(left_panel_frame)
        self._create_action_buttons(left_panel_frame)

        # --- Panel Derecho: Canvas Gráfico ---
        right_panel_frame = ttk.Frame(main_paned_window, padding=(10,5))
        main_paned_window.add(right_panel_frame, weight=2) 

        self._create_canvas_widget(right_panel_frame)


    def _create_form_widgets(self, parent_frame):
        form_frame = ttk.LabelFrame(parent_frame, text="Detalles de la Mesa", padding=(15, 10))
        form_frame.pack(pady=(0,10), fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="ID Mesa:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.id_entry = ttk.Entry(form_frame, textvariable=self.table_id_var, width=35)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Capacidad:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.capacity_spinbox = ttk.Spinbox(form_frame, from_=1, to=20, textvariable=self.capacity_var, width=33)
        self.capacity_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.capacity_var.set(2) # Establecer valor inicial

        ttk.Label(form_frame, text="Ubicación (Desc.):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.location_desc_entry = ttk.Entry(form_frame, textvariable=self.location_desc_var, width=35)
        self.location_desc_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Estado:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.status_combobox = ttk.Combobox(form_frame, textvariable=self.status_var,
                                            values=["libre", "ocupada", "reservada", "mantenimiento"], state="readonly", width=33)
        self.status_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.status_var.set("libre") # Establecer valor inicial

        ttk.Label(form_frame, text="Posición X:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.pos_x_spinbox = ttk.Spinbox(form_frame, from_=0, to=2000, increment=10, textvariable=self.pos_x_var, width=33)
        self.pos_x_spinbox.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.pos_x_var.set(50) # Establecer valor inicial

        ttk.Label(form_frame, text="Posición Y:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.pos_y_spinbox = ttk.Spinbox(form_frame, from_=0, to=2000, increment=10, textvariable=self.pos_y_var, width=33)
        self.pos_y_spinbox.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        self.pos_y_var.set(50) # Establecer valor inicial

    def _create_treeview_widget(self, parent_frame):
        tree_frame = ttk.LabelFrame(parent_frame, text="Listado de Mesas", padding=(10,5))
        tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        columns = ("id_mesa", "capacidad", "estado", "ubicacion", "pos_x", "pos_y")
        self.tables_treeview = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tables_treeview.heading("id_mesa", text="ID")
        self.tables_treeview.heading("capacidad", text="Cap.")
        self.tables_treeview.heading("estado", text="Estado")
        self.tables_treeview.heading("ubicacion", text="Ubicación")
        self.tables_treeview.heading("pos_x", text="X")
        self.tables_treeview.heading("pos_y", text="Y")

        self.tables_treeview.column("id_mesa", width=60, anchor="w")
        self.tables_treeview.column("capacidad", width=40, anchor="center")
        self.tables_treeview.column("estado", width=80, anchor="w")
        self.tables_treeview.column("ubicacion", width=120, anchor="w")
        self.tables_treeview.column("pos_x", width=40, anchor="center")
        self.tables_treeview.column("pos_y", width=40, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tables_treeview.yview)
        self.tables_treeview.configure(yscroll=scrollbar.set)
        
        self.tables_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tables_treeview.bind("<<TreeviewSelect>>", self._on_table_select_treeview)

    def _create_action_buttons(self, parent_frame):
        buttons_frame = ttk.Frame(parent_frame, padding=(0, 10))
        buttons_frame.pack(fill=tk.X, pady=(5,0))
        
        # El comando para "Nuevo" ahora llama a _clear_form_fields con ask_for_position=True
        ttk.Button(buttons_frame, text="Nuevo", command=lambda: self._clear_form_fields(ask_for_position=True), width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Guardar", command=self._save_table, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar", command=self._delete_selected_table, width=12).pack(side=tk.LEFT, padx=5)


    def _create_canvas_widget(self, parent_frame):
        canvas_label_frame = ttk.LabelFrame(parent_frame, text="Distribución de Mesas", padding=(10,5))
        canvas_label_frame.pack(fill=tk.BOTH, expand=True)

        self.tables_canvas = tk.Canvas(canvas_label_frame, bg="white", scrollregion=(0,0,2000,2000))
        
        hbar = ttk.Scrollbar(canvas_label_frame, orient=tk.HORIZONTAL, command=self.tables_canvas.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar = ttk.Scrollbar(canvas_label_frame, orient=tk.VERTICAL, command=self.tables_canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tables_canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.tables_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tables_canvas.bind("<Button-1>", self._on_canvas_click)

    def _draw_tables_on_canvas(self):
        if not table_model: return
        self.tables_canvas.delete("all") 
        self._table_canvas_objects.clear() 

        tables_list = table_model.get_all_tables_list()
        if tables_list:
            for table_data in tables_list:
                self._draw_single_table_representation(table_data)
        elif tables_list is None:
            messagebox.showerror("Error de Carga", "No se pudieron cargar las mesas para el canvas.")

    def _draw_single_table_representation(self, table_data):
        table_id = table_data.get("id_mesa")
        pos_x = table_data.get("pos_x", 50)
        pos_y = table_data.get("pos_y", 50)
        status = table_data.get("estado", "libre")
        capacity = table_data.get("capacidad", 0)

        fill_color = STATUS_COLORS.get(status, STATUS_COLORS["default"])
        outline_color = "black"
        
        canvas_table_tag = f"table_{table_id}"

        rect_id = self.tables_canvas.create_rectangle(
            pos_x, pos_y, 
            pos_x + TABLE_WIDTH, pos_y + TABLE_HEIGHT,
            fill=fill_color, outline=outline_color, width=2, tags=(canvas_table_tag, "table_visual")
        )
        text_content = f"{table_id}\nCap: {capacity}\n{status.capitalize()}"
        text_id = self.tables_canvas.create_text(
            pos_x + TABLE_WIDTH / 2, pos_y + TABLE_HEIGHT / 2,
            text=text_content, justify=tk.CENTER, font=("Arial", 8), tags=(canvas_table_tag, "table_text")
        )
        self._table_canvas_objects[table_id] = {'rect': rect_id, 'text': text_id, 'tag': canvas_table_tag}

    def _on_canvas_click(self, event):
        canvas_x = self.tables_canvas.canvasx(event.x) 
        canvas_y = self.tables_canvas.canvasy(event.y)
        
        items_found = self.tables_canvas.find_closest(canvas_x, canvas_y, halo=5)
        
        self._selected_canvas_item_id = None 

        if items_found:
            item_id = items_found[0]
            tags = self.tables_canvas.gettags(item_id)
            
            table_specific_tag = None
            for tag in tags:
                if tag.startswith("table_") and tag != "table_visual" and tag != "table_text":
                    table_specific_tag = tag
                    break
            
            if table_specific_tag:
                self._selected_canvas_item_id = table_specific_tag 
                table_db_id = table_specific_tag.split("table_")[1] 
                
                self._load_table_data_to_form(table_db_id)
                self._select_table_in_treeview(table_db_id)
                self._highlight_canvas_selection(table_specific_tag)
            else:
                self._highlight_canvas_selection(None) 
        else:
            self._highlight_canvas_selection(None)

    def _highlight_canvas_selection(self, canvas_table_tag_to_highlight):
        for table_id, canvas_objs in self._table_canvas_objects.items():
            rect_item = canvas_objs['rect']
            if canvas_objs['tag'] == canvas_table_tag_to_highlight:
                self.tables_canvas.itemconfig(rect_item, outline="blue", width=3)
            else:
                self.tables_canvas.itemconfig(rect_item, outline="black", width=2)

    def _load_tables_to_ui(self):
        self._load_tables_to_treeview()
        self._draw_tables_on_canvas()

    def _load_tables_to_treeview(self):
        if not table_model: return
        for item in self.tables_treeview.get_children():
            self.tables_treeview.delete(item)
        
        tables_list = table_model.get_all_tables_list()
        if tables_list:
            for tbl in tables_list:
                self.tables_treeview.insert("", tk.END, values=(
                    tbl.get("id_mesa", ""), tbl.get("capacidad", 0),
                    tbl.get("estado", ""), tbl.get("ubicacion", ""),
                    tbl.get("pos_x", 0), tbl.get("pos_y", 0)
                ))
        elif tables_list is None:
             messagebox.showerror("Error de Carga", "No se pudieron cargar las mesas al listado.")
    
    def _select_table_in_treeview(self, table_id_to_select):
        for item_id_in_tree in self.tables_treeview.get_children(): # Renombrada la variable de bucle
            values = self.tables_treeview.item(item_id_in_tree, "values")
            if values and values[0] == table_id_to_select:
                self.tables_treeview.selection_set(item_id_in_tree)
                self.tables_treeview.focus(item_id_in_tree) 
                self.tables_treeview.see(item_id_in_tree)   
                return

    def _on_table_select_treeview(self, event=None):
        selected_items = self.tables_treeview.selection()
        if not selected_items: return

        item_values = self.tables_treeview.item(selected_items[0], "values")
        if item_values:
            table_db_id = item_values[0]
            self._load_table_data_to_form(table_db_id)
            if table_db_id in self._table_canvas_objects:
                canvas_tag = self._table_canvas_objects[table_db_id]['tag']
                self._highlight_canvas_selection(canvas_tag)
                self._selected_canvas_item_id = canvas_tag 
    
    def _load_table_data_to_form(self, table_id_from_db):
        if not table_model: return
        table_data = table_model.get_table_by_id(table_id_from_db)
        if table_data:
            self.table_id_var.set(table_data.get("id_mesa", ""))
            self.capacity_var.set(table_data.get("capacidad", 0))
            self.location_desc_var.set(table_data.get("ubicacion", ""))
            self.status_var.set(table_data.get("estado", "libre"))
            self.pos_x_var.set(table_data.get("pos_x", 50))
            self.pos_y_var.set(table_data.get("pos_y", 50))
            
            self.id_entry.configure(state='readonly') 
        else:
            messagebox.showwarning("Carga Fallida", f"No se encontraron datos para la mesa ID: {table_id_from_db}")
            self._clear_form_fields(ask_for_position=False) # No preguntar al fallar la carga

    def _clear_form_fields(self, ask_for_position=False): # Nuevo parámetro
        """ Limpia los campos del formulario. Opcionalmente pregunta por posición si es para una mesa nueva. """
        self.table_id_var.set("")
        self.capacity_var.set(2) 
        self.location_desc_var.set("")
        self.status_var.set("libre")
        
        if ask_for_position:
            # Solo preguntar por posición si se indica explícitamente (ej. botón "Nuevo")
            # Usamos simpledialog aquí porque es una acción iniciada por el usuario para una nueva mesa.
            # Necesitamos importar simpledialog al inicio del archivo.
            from tkinter import simpledialog # Importar aquí o al inicio del archivo
            
            new_pos_x = simpledialog.askinteger("Posición X", "Posición X inicial para nueva mesa:", 
                                                initialvalue=50, minvalue=0, parent=self)
            self.pos_x_var.set(new_pos_x if new_pos_x is not None else 50) # Usar 50 si el usuario cancela

            new_pos_y = simpledialog.askinteger("Posición Y", "Posición Y inicial para nueva mesa:", 
                                                initialvalue=50, minvalue=0, parent=self)
            self.pos_y_var.set(new_pos_y if new_pos_y is not None else 50)
        else:
            # Simplemente resetear a valores por defecto sin diálogo
            self.pos_x_var.set(50)
            self.pos_y_var.set(50)
        
        self.id_entry.configure(state='normal')
        self._selected_canvas_item_id = None
        self._highlight_canvas_selection(None) 

        if self.tables_treeview.selection():
            self.tables_treeview.selection_remove(self.tables_treeview.selection()[0])
        self.id_entry.focus()

    def _validate_inputs(self):
        table_id = self.table_id_var.get().strip()
        capacity = self.capacity_var.get()

        if not table_id:
            messagebox.showerror("Error de Validación", "El ID de Mesa es obligatorio.")
            return False
        if capacity <= 0:
            messagebox.showerror("Error de Validación", "La capacidad debe ser mayor que cero.")
            return False
        if not self.status_var.get(): # Asegurar que el estado tenga un valor
            messagebox.showerror("Error de Validación", "El Estado es obligatorio.")
            return False
        # Validar que pos_x y pos_y sean números (Spinbox ya lo fuerza un poco)
        try:
            int(self.pos_x_var.get())
            int(self.pos_y_var.get())
        except ValueError:
            messagebox.showerror("Error de Validación", "Las posiciones X e Y deben ser números enteros.")
            return False
            
        return True

    def _save_table(self):
        if not table_model:
            messagebox.showerror("Error Crítico", "El modelo de mesas no está cargado.")
            return
        if not self._validate_inputs():
            return

        table_data_payload = {
            'id_mesa': self.table_id_var.get().strip(),
            'capacidad': self.capacity_var.get(),
            'ubicacion': self.location_desc_var.get().strip(),
            'estado': self.status_var.get(),
            'pos_x': self.pos_x_var.get(),
            'pos_y': self.pos_y_var.get()
        }
        
        id_for_operation = table_data_payload['id_mesa']
        is_update_mode = self.id_entry.cget('state') == 'readonly'

        if is_update_mode: 
            result = table_model.update_table_details(id_for_operation, table_data_payload)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Mesa '{id_for_operation}' actualizada exitosamente.")
            elif result == 0:
                messagebox.showinfo("Información", f"No se realizaron cambios en la mesa '{id_for_operation}'.")
            else:
                messagebox.showerror("Error de Actualización", f"No se pudo actualizar la mesa '{id_for_operation}'.")
        else: 
            if table_model.get_table_by_id(id_for_operation):
                messagebox.showerror("Error de Creación", f"El ID de mesa '{id_for_operation}' ya existe.")
                return
            
            result = table_model.create_table(table_data_payload)
            if result is not None:
                messagebox.showinfo("Éxito", f"Mesa '{id_for_operation}' creada exitosamente.")
            else:
                messagebox.showerror("Error de Creación", f"No se pudo crear la mesa '{id_for_operation}'.")
        
        self._load_tables_to_ui() 
        self._clear_form_fields(ask_for_position=False) # No preguntar después de guardar


    def _delete_selected_table(self):
        if not table_model:
            messagebox.showerror("Error Crítico", "El modelo de mesas no está cargado.")
            return

        id_to_delete = self.table_id_var.get().strip()
        # Si el campo ID está habilitado, significa que no hay una mesa cargada para editar/eliminar
        if not id_to_delete or self.id_entry.cget('state') == 'normal': 
            selected_tree_items = self.tables_treeview.selection()
            if selected_tree_items:
                id_to_delete = self.tables_treeview.item(selected_tree_items[0], "values")[0]
            else:
                messagebox.showwarning("Sin Selección", "Por favor, seleccione una mesa para eliminar (desde la lista o el mapa).")
                return

        confirm = messagebox.askyesno("Confirmar Eliminación", 
                                      f"¿Está seguro de que desea eliminar la mesa ID: {id_to_delete}?\n¡Esta acción es permanente!")
        if confirm:
            result = table_model.delete_table_by_id(id_to_delete)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Mesa '{id_to_delete}' eliminada exitosamente.")
            else:
                messagebox.showerror("Error de Eliminación", f"No se pudo eliminar la mesa '{id_to_delete}'.\nPuede que tenga comandas asociadas o no exista.")
            
            self._load_tables_to_ui()
            self._clear_form_fields(ask_for_position=False) # No preguntar después de eliminar

# --- Para probar esta vista de forma aislada ---
if __name__ == '__main__':
    if not table_model:
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico de Módulo", 
                             "No se pudo cargar 'table_model' para probar la vista de mesas.")
        root_error.destroy()
    else:
        root = tk.Tk()
        root.title("Gestión de Mesas (Prueba Aislada)")
        root.geometry("1000x700") 

        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes: style.theme_use('clam')
        
        table_view_frame = TableView(root)
        table_view_frame.pack(fill=tk.BOTH, expand=True)

        root.mainloop()

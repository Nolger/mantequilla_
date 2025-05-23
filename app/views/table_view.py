# app/views/table_view.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    # Asumiendo que table_view.py está en app/views/ y table_model.py está en app/models/
    # y que 'app' es un paquete reconocido (ej. main.py está un nivel arriba)
    from app.models import table_model
except ImportError:
    # Fallback si la estructura es diferente o se ejecuta directamente
    # y 'models' es un paquete hermano o accesible
    try:
        from ..models import table_model
    except ImportError:
        # Fallback si 'models' está en el mismo nivel (menos común para esta estructura)
        try:
            from models import table_model
        except ImportError:
            print("Error CRÍTICO: No se pudo importar el módulo table_model.py en TableView. Verifica tu estructura y PYTHONPATH.")
            table_model = None

# Constantes para el canvas
TABLE_WIDTH = 80
TABLE_HEIGHT = 50
CANVAS_PADDING = 20
STATUS_COLORS = {
    "libre": "#90EE90",
    "ocupada": "#FA8072",
    "reservada": "#ADD8E6",
    "mantenimiento": "#D3D3D3",
    "default": "#FFFFFF"
}
SELECTED_OUTLINE_COLOR = "blue"
DEFAULT_OUTLINE_COLOR = "black"

class TableView(ttk.Frame):
    def __init__(self, parent_container, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container

        if not table_model:
            error_label = ttk.Label(self, text="Error crítico: El modelo de mesas no está disponible.", foreground="red")
            error_label.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
            return

        # Variables para los campos del formulario
        self.table_id_var = tk.StringVar()
        self.capacity_var = tk.IntVar(value=2)
        self.location_desc_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.pos_x_var = tk.IntVar(value=50)
        self.pos_y_var = tk.IntVar(value=50)

        # Para arrastrar y soltar en el canvas
        self._drag_data = {"x": 0, "y": 0, "item_tag_group": None, "table_id": None} # item_tag_group en lugar de item
        self._selected_canvas_tag = None

        self._table_canvas_objects = {}

        # Variable para rastrear si estamos en modo "creación"
        self._is_new_table_mode = False

        self._create_layout()
        self._load_tables_to_ui()
        self._clear_form_fields(ask_for_position=False) # Estado inicial, no es modo nuevo aún

    def _create_layout(self):
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        left_panel_frame = ttk.Frame(main_paned_window, padding=(10,5))
        main_paned_window.add(left_panel_frame, weight=1)
        self._create_form_widgets(left_panel_frame)
        self._create_treeview_widget(left_panel_frame)
        self._create_action_buttons(left_panel_frame)

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

        ttk.Label(form_frame, text="Ubicación (Desc.):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.location_desc_entry = ttk.Entry(form_frame, textvariable=self.location_desc_var, width=35)
        self.location_desc_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Estado:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.status_combobox = ttk.Combobox(form_frame, textvariable=self.status_var,
                                            values=["libre", "ocupada", "reservada", "mantenimiento"], state="readonly", width=33)
        self.status_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Posición X:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.pos_x_spinbox = ttk.Spinbox(form_frame, from_=0, to=2000, increment=10, textvariable=self.pos_x_var, width=33)
        self.pos_x_spinbox.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Posición Y:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.pos_y_spinbox = ttk.Spinbox(form_frame, from_=0, to=2000, increment=10, textvariable=self.pos_y_var, width=33)
        self.pos_y_spinbox.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

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

        self.tables_treeview.column("id_mesa", width=60, anchor="w", stretch=tk.NO)
        self.tables_treeview.column("capacidad", width=40, anchor="center", stretch=tk.NO)
        self.tables_treeview.column("estado", width=80, anchor="w")
        self.tables_treeview.column("ubicacion", width=120, anchor="w")
        self.tables_treeview.column("pos_x", width=40, anchor="center", stretch=tk.NO)
        self.tables_treeview.column("pos_y", width=40, anchor="center", stretch=tk.NO)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tables_treeview.yview)
        self.tables_treeview.configure(yscroll=scrollbar.set)
        
        self.tables_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tables_treeview.bind("<<TreeviewSelect>>", self._on_table_select_treeview)

    def _create_action_buttons(self, parent_frame):
        buttons_frame = ttk.Frame(parent_frame, padding=(0, 10))
        buttons_frame.pack(fill=tk.X, pady=(5,0))
        
        ttk.Button(buttons_frame, text="Nuevo", command=self._prepare_for_new_table, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Guardar", command=self._save_table, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar", command=self._delete_selected_table, width=12).pack(side=tk.LEFT, padx=5)

    def _create_canvas_widget(self, parent_frame):
        canvas_label_frame = ttk.LabelFrame(parent_frame, text="Distribución de Mesas (Clic para seleccionar, Arrastrar para mover)", padding=(10,5))
        canvas_label_frame.pack(fill=tk.BOTH, expand=True)

        self.tables_canvas = tk.Canvas(canvas_label_frame, bg="ivory", scrollregion=(0,0,2000,2000))
        
        hbar = ttk.Scrollbar(canvas_label_frame, orient=tk.HORIZONTAL, command=self.tables_canvas.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar = ttk.Scrollbar(canvas_label_frame, orient=tk.VERTICAL, command=self.tables_canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tables_canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.tables_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tables_canvas.bind("<ButtonPress-1>", self._on_canvas_button_press)
        self.tables_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.tables_canvas.bind("<ButtonRelease-1>", self._on_canvas_button_release)

    def _draw_tables_on_canvas(self):
        if not table_model: return
        self.tables_canvas.delete("all_tables_group")
        self._table_canvas_objects.clear()

        tables_list = table_model.get_all_tables_list()
        if tables_list:
            for table_data in tables_list:
                # Determinar si esta mesa es la actualmente seleccionada en el canvas
                is_selected_on_canvas = (self._selected_canvas_tag == f"tablegroup_{table_data.get('id_mesa')}")
                self._draw_single_table_representation(table_data, is_selected=is_selected_on_canvas)
        elif tables_list is None:
            messagebox.showerror("Error de Carga", "No se pudieron cargar las mesas para el canvas.")
        
        # Si _selected_canvas_tag está definido (porque se seleccionó algo antes de un redibujo),
        # la lógica de is_selected_on_canvas dentro del bucle ya debería manejar el resaltado.
        # No es necesario llamar a _highlight_canvas_selection aquí explícitamente si _draw_single_table_representation lo maneja.

    def _draw_single_table_representation(self, table_data, is_selected=False):
        table_id = table_data.get("id_mesa")
        pos_x = int(table_data.get("pos_x", 50))
        pos_y = int(table_data.get("pos_y", 50))
        status = table_data.get("estado", "libre")
        capacity = table_data.get("capacidad", 0)

        fill_color = STATUS_COLORS.get(status, STATUS_COLORS["default"])
        outline_color = SELECTED_OUTLINE_COLOR if is_selected else DEFAULT_OUTLINE_COLOR
        outline_width = 3 if is_selected else 2
        
        canvas_table_group_tag = f"tablegroup_{table_id}"
        rect_tag = f"tablerect_{table_id}"
        text_tag = f"tabletext_{table_id}"

        self.tables_canvas.delete(canvas_table_group_tag) # Borrar si ya existe para redibujar

        rect_id = self.tables_canvas.create_rectangle(
            pos_x, pos_y, 
            pos_x + TABLE_WIDTH, pos_y + TABLE_HEIGHT,
            fill=fill_color, outline=outline_color, width=outline_width, 
            tags=(canvas_table_group_tag, rect_tag, "all_tables_group")
        )
        text_content = f"{table_id}\nCap: {capacity}\n{status.capitalize()}"
        text_id = self.tables_canvas.create_text(
            pos_x + TABLE_WIDTH / 2, pos_y + TABLE_HEIGHT / 2,
            text=text_content, justify=tk.CENTER, font=("Arial", 8, "bold"),
            tags=(canvas_table_group_tag, text_tag, "all_tables_group")
        )
        self._table_canvas_objects[table_id] = {'rect': rect_id, 'text': text_id, 'tag': canvas_table_group_tag}

    def _get_table_id_from_canvas_item(self, canvas_item_id):
        tags = self.tables_canvas.gettags(canvas_item_id)
        for tag in tags:
            if tag.startswith("tablegroup_"): return tag.split("tablegroup_")[1]
            if tag.startswith("tablerect_"): return tag.split("tablerect_")[1]
            if tag.startswith("tabletext_"): return tag.split("tabletext_")[1]
        return None

    def _on_canvas_button_press(self, event):
        canvas_x = self.tables_canvas.canvasx(event.x)
        canvas_y = self.tables_canvas.canvasy(event.y)
        
        items_found = self.tables_canvas.find_overlapping(canvas_x -1, canvas_y -1, canvas_x +1, canvas_y+1)
        clicked_on_table = False

        if items_found:
            table_db_id_of_item = None
            for item_id in items_found: # Renombrar item a item_id para claridad
                # Priorizar rectángulos para la selección
                tags = self.tables_canvas.gettags(item_id)
                if any(t.startswith("tablerect_") for t in tags):
                    table_db_id_of_item = self._get_table_id_from_canvas_item(item_id)
                    break # Encontramos el rectángulo de una mesa
            
            if table_db_id_of_item:
                clicked_on_table = True
                self._is_new_table_mode = False # Seleccionando una existente
                new_selected_tag = self._table_canvas_objects[table_db_id_of_item]['tag']
                if self._selected_canvas_tag != new_selected_tag:
                    self._highlight_canvas_selection(new_selected_tag) # Resaltar la nueva
                self._selected_canvas_tag = new_selected_tag
                
                self._load_table_data_to_form(table_db_id_of_item)
                self._select_table_in_treeview(table_db_id_of_item)

                self._drag_data["item_tag_group"] = self._selected_canvas_tag
                self._drag_data["table_id"] = table_db_id_of_item
                self._drag_data["x"] = canvas_x
                self._drag_data["y"] = canvas_y
        
        if not clicked_on_table: # Si se hizo clic en espacio vacío
            self._clear_selection_and_form()


    def _on_canvas_drag(self, event):
        if self._drag_data.get("item_tag_group"):
            canvas_x = self.tables_canvas.canvasx(event.x)
            canvas_y = self.tables_canvas.canvasy(event.y)
            delta_x = canvas_x - self._drag_data["x"]
            delta_y = canvas_y - self._drag_data["y"]

            self.tables_canvas.move(self._drag_data["item_tag_group"], delta_x, delta_y)

            self._drag_data["x"] = canvas_x
            self._drag_data["y"] = canvas_y

            current_coords = self.tables_canvas.coords(self._table_canvas_objects[self._drag_data["table_id"]]['rect'])
            self.pos_x_var.set(int(current_coords[0]))
            self.pos_y_var.set(int(current_coords[1]))

    def _on_canvas_button_release(self, event):
        if self._drag_data.get("item_tag_group") and self._drag_data.get("table_id"):
            table_id_dragged = self._drag_data["table_id"]
            print(f"Mesa {table_id_dragged} movida a X:{self.pos_x_var.get()}, Y:{self.pos_y_var.get()}. Presione Guardar para confirmar.")
        
        self._drag_data = {"x": 0, "y": 0, "item_tag_group": None, "table_id": None}

    def _highlight_canvas_selection(self, canvas_table_group_tag_to_highlight):
        for table_id, canvas_objs in self._table_canvas_objects.items():
            rect_item = canvas_objs.get('rect')
            if rect_item and self.tables_canvas.winfo_exists(): # Chequear si el canvas existe
                try:
                    if canvas_objs.get('tag') == canvas_table_group_tag_to_highlight:
                        self.tables_canvas.itemconfig(rect_item, outline=SELECTED_OUTLINE_COLOR, width=3)
                    else:
                        self.tables_canvas.itemconfig(rect_item, outline=DEFAULT_OUTLINE_COLOR, width=2)
                except tk.TclError: # Puede ocurrir si el item fue borrado
                    pass


    def _load_tables_to_ui(self):
        self._load_tables_to_treeview()
        self._draw_tables_on_canvas()

    def _load_tables_to_treeview(self):
        if not table_model: return
        current_selection_tree_id = None
        if self.tables_treeview.selection():
            current_selection_tree_id = self.tables_treeview.selection()[0]
        
        for item in self.tables_treeview.get_children():
            self.tables_treeview.delete(item)
        
        tables_list = table_model.get_all_tables_list()
        if tables_list:
            for tbl in tables_list:
                self.tables_treeview.insert("", tk.END, iid=tbl.get("id_mesa"), values=(
                    tbl.get("id_mesa", ""), tbl.get("capacidad", 0),
                    tbl.get("estado", ""), tbl.get("ubicacion", ""),
                    tbl.get("pos_x", 0), tbl.get("pos_y", 0)
                ))
        elif tables_list is None:
             messagebox.showerror("Error de Carga", "No se pudieron cargar las mesas al listado.")
        
        if current_selection_tree_id and self.tables_treeview.exists(current_selection_tree_id):
            self.tables_treeview.selection_set(current_selection_tree_id)
            self.tables_treeview.focus(current_selection_tree_id)
            self.tables_treeview.see(current_selection_tree_id)

    def _select_table_in_treeview(self, table_id_to_select):
        if self.tables_treeview.exists(table_id_to_select):
            if not self.tables_treeview.selection() or self.tables_treeview.selection()[0] != table_id_to_select:
                self.tables_treeview.selection_set(table_id_to_select)
            self.tables_treeview.focus(table_id_to_select)
            self.tables_treeview.see(table_id_to_select)
        else:
            if self.tables_treeview.selection():
                self.tables_treeview.selection_remove(self.tables_treeview.selection()[0])

    def _on_table_select_treeview(self, event=None):
        selected_items = self.tables_treeview.selection()
        if not selected_items:
            # No llamar a _clear_selection_and_form() aquí directamente
            # para evitar bucles si el deseleccionar es programático.
            # Si el usuario deselecciona, el formulario debería limpiarse.
            # Esto podría necesitar una lógica más fina o un flag.
            # Por ahora, si no hay selección, no hacemos nada aquí para evitar
            # que un _clear_form_fields llame a deseleccionar y cree un bucle.
            return

        self._is_new_table_mode = False # Seleccionando una existente
        table_db_id = selected_items[0]
        self._load_table_data_to_form(table_db_id)
        
        if table_db_id in self._table_canvas_objects:
            canvas_tag = self._table_canvas_objects[table_db_id]['tag']
            if self._selected_canvas_tag != canvas_tag: # Solo resaltar si es diferente
                 self._highlight_canvas_selection(canvas_tag)
            self._selected_canvas_tag = canvas_tag
        else:
            if self._selected_canvas_tag: # Si había algo seleccionado en canvas, quitar resaltado
                self._highlight_canvas_selection(None)
            self._selected_canvas_tag = None
    
    def _load_table_data_to_form(self, table_id_from_db):
        self._is_new_table_mode = False
        if not table_model: return
        table_data = table_model.get_table_by_id(table_id_from_db)
        if table_data:
            self.table_id_var.set(table_data.get("id_mesa", ""))
            self.capacity_var.set(int(table_data.get("capacidad", 0)))
            self.location_desc_var.set(table_data.get("ubicacion", ""))
            self.status_var.set(table_data.get("estado", "libre"))
            self.pos_x_var.set(int(table_data.get("pos_x", 50)))
            self.pos_y_var.set(int(table_data.get("pos_y", 50)))
            self.id_entry.configure(state='readonly')
        else:
            messagebox.showwarning("Carga Fallida", f"No se encontraron datos para la mesa ID: {table_id_from_db}")
            self._clear_form_fields(ask_for_position=False)

    def _clear_selection_and_form(self):
        self._is_new_table_mode = False
        self._selected_canvas_tag = None
        self._highlight_canvas_selection(None)
        if self.tables_treeview.selection():
            self.tables_treeview.selection_remove(self.tables_treeview.selection()[0])
        self._clear_form_fields(ask_for_position=False) # No preguntar posición aquí

    def _prepare_for_new_table(self):
        self._is_new_table_mode = True
        # Limpiar selecciones antes de limpiar el formulario
        self._selected_canvas_tag = None
        self._highlight_canvas_selection(None)
        if self.tables_treeview.selection():
            self.tables_treeview.selection_remove(self.tables_treeview.selection()[0])
        
        self._clear_form_fields(ask_for_position=True)
        self.id_entry.focus()


    def _clear_form_fields(self, ask_for_position=False):
        self.table_id_var.set("")
        self.capacity_var.set(2)
        self.location_desc_var.set("")
        self.status_var.set("libre")
        
        if ask_for_position and self._is_new_table_mode: # Solo pedir si es modo nuevo
            new_pos_x = simpledialog.askinteger("Posición X", "Posición X inicial para nueva mesa (en canvas):",
                                                initialvalue=50, minvalue=0, parent=self.parent_container)
            self.pos_x_var.set(new_pos_x if new_pos_x is not None else 50)

            new_pos_y = simpledialog.askinteger("Posición Y", "Posición Y inicial para nueva mesa (en canvas):",
                                                initialvalue=50, minvalue=0, parent=self.parent_container)
            self.pos_y_var.set(new_pos_y if new_pos_y is not None else 50)
        else: # Si no se pide posición (ej. al cargar, o al limpiar después de seleccionar)
            self.pos_x_var.set(50)
            self.pos_y_var.set(50)
        
        # El estado del ID entry depende de si estamos en modo nuevo o no
        if self._is_new_table_mode:
            self.id_entry.configure(state='normal')
            self.id_entry.focus()
        else: # Si no es modo nuevo (ej. se limpió después de una selección, o al inicio)
            self.id_entry.configure(state='normal') # Dejarlo normal para que el usuario pueda escribir si quiere,
                                                    # pero _load_table_data_to_form lo pondrá readonly si se carga una mesa.
                                                    # O, si se limpia sin selección, debería estar normal.
            # No deseleccionar aquí para evitar bucles, _clear_selection_and_form lo maneja.

    def _validate_inputs(self):
        table_id = self.table_id_var.get().strip()
        try:
            capacity = self.capacity_var.get()
        except tk.TclError:
             messagebox.showerror("Error de Validación", "La capacidad debe ser un número entero.")
             return False

        if not table_id:
            messagebox.showerror("Error de Validación", "El ID de Mesa es obligatorio.")
            return False
        if not isinstance(capacity, int) or capacity <= 0:
            messagebox.showerror("Error de Validación", "La capacidad debe ser un número entero mayor que cero.")
            return False
        if not self.status_var.get():
            messagebox.showerror("Error de Validación", "El Estado es obligatorio.")
            return False
        try:
            int(self.pos_x_var.get())
            int(self.pos_y_var.get())
        except (tk.TclError, ValueError):
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
        
        if self._is_new_table_mode:
            if table_model.get_table_by_id(id_for_operation):
                messagebox.showerror("Error de Creación", f"El ID de mesa '{id_for_operation}' ya existe.")
                return 
            
            result = table_model.create_table(table_data_payload)
            if result is not None:
                messagebox.showinfo("Éxito", f"Mesa '{id_for_operation}' creada exitosamente.")
                self._is_new_table_mode = False 
                # No es necesario poner id_entry readonly aquí, _select_table_in_treeview lo hará indirectamente
            else:
                messagebox.showerror("Error de Creación", f"No se pudo crear la mesa '{id_for_operation}'.")
                return 
        else: 
            if self.id_entry.cget('state') != 'readonly':
                # Esto podría pasar si el usuario presionó "Nuevo", escribió un ID existente,
                # y luego presionó "Guardar" sin que el sistema detectara que es una actualización.
                # La verificación de ID existente en el bloque de creación debería manejar esto.
                # Si llegamos aquí y el ID es editable, es un estado inesperado.
                # Podríamos forzar una verificación de si existe para decidir si crear o actualizar.
                # Por ahora, asumimos que si no es _is_new_table_mode, es una actualización.
                print("Advertencia: Guardando en modo actualización pero el ID es editable.")
                # No hacer nada drástico, la lógica de abajo debería funcionar si el ID ya existe.

            result = table_model.update_table_details(id_for_operation, table_data_payload)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Mesa '{id_for_operation}' actualizada exitosamente.")
            elif result == 0:
                messagebox.showinfo("Información", f"No se realizaron cambios en la mesa '{id_for_operation}'.")
            else:
                messagebox.showerror("Error de Actualización", f"No se pudo actualizar la mesa '{id_for_operation}'.")
                return
        
        self._load_tables_to_ui()
        self._select_table_in_treeview(id_for_operation) # Esto debería cargarla en el form y poner ID readonly

    def _delete_selected_table(self):
        self._is_new_table_mode = False
        if not table_model:
            messagebox.showerror("Error Crítico", "El modelo de mesas no está cargado.")
            return

        id_to_delete = self.table_id_var.get().strip()
        if not id_to_delete or self.id_entry.cget('state') == 'normal': 
            selected_tree_items = self.tables_treeview.selection()
            if selected_tree_items:
                id_to_delete = selected_tree_items[0]
            else:
                messagebox.showwarning("Sin Selección", "Por favor, seleccione una mesa para eliminar.")
                return

        if not id_to_delete:
            messagebox.showwarning("Sin Selección", "No se pudo determinar la mesa a eliminar.")
            return

        confirm = messagebox.askyesno("Confirmar Eliminación", 
                                      f"¿Está seguro de que desea eliminar la mesa ID: {id_to_delete}?\n¡Esta acción es permanente!")
        if confirm:
            result = table_model.delete_table_by_id(id_to_delete)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Mesa '{id_to_delete}' eliminada exitosamente.")
            else:
                messagebox.showerror("Error de Eliminación", f"No se pudo eliminar la mesa '{id_to_delete}'.\nPuede que tenga comandas asociadas activas o no exista.")
            
            self._load_tables_to_ui()
            self._clear_form_fields(ask_for_position=False) # Limpiar después de eliminar

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
        root.geometry("1100x700")

        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes: style.theme_use('clam')
        
        table_view_frame = TableView(root)
        table_view_frame.pack(fill=tk.BOTH, expand=True)

        root.mainloop()
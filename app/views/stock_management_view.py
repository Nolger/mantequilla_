# app/views/stock_management_view.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from ..models import stock_model # Si stock_model.py está en app/models/
except ImportError:
    try:
        from models import stock_model # Si 'models' es un paquete accesible
    except ImportError:
        print("Error: No se pudo importar el módulo stock_model.py. Verifica tu estructura y PYTHONPATH.")
        stock_model = None

class StockManagementView(ttk.Frame):
    def __init__(self, parent_container, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container

        if not stock_model:
            error_label = ttk.Label(self, text="Error crítico: El modelo de stock no está disponible.", foreground="red")
            error_label.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
            return

        # Variables para el formulario de Producto
        self.product_id_var = tk.StringVar()
        self.product_name_var = tk.StringVar()
        self.product_description_var = tk.StringVar()
        self.product_unit_var = tk.StringVar()
        self.product_min_stock_var = tk.DoubleVar(value=0.0)
        self.product_supplier_ref_var = tk.StringVar() # Asumimos que es un ID o nombre
        self.product_cost_var = tk.DoubleVar(value=0.0)
        self.product_is_perishable_var = tk.BooleanVar(value=False)
        self.product_expiry_date_var = tk.StringVar() # Formato YYYY-MM-DD

        # Variables para el formulario de ajuste de stock de Ingrediente
        self.selected_ingredient_id_stock_var = tk.StringVar() # Para el ingrediente a ajustar
        self.stock_adjustment_quantity_var = tk.DoubleVar(value=0.0)
        self.stock_adjustment_reason_var = tk.StringVar(value="Recepción de Proveedor")

        self._create_layout()
        self._load_products_to_treeview()
        self._load_ingredients_to_treeview()
        self._clear_product_form_fields()

    def _create_layout(self):
        # Notebook para organizar las secciones de Productos e Ingredientes
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # --- Pestaña de Gestión de Productos (Insumos) ---
        self.products_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.products_tab, text='Productos (Insumos)')
        self._create_products_tab_content(self.products_tab)

        # --- Pestaña de Gestión de Stock de Ingredientes (Cocina) ---
        self.ingredients_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.ingredients_tab, text='Ingredientes (Stock Cocina)')
        self._create_ingredients_tab_content(self.ingredients_tab)

    # --- Contenido de la Pestaña de Productos ---
    def _create_products_tab_content(self, parent_tab_frame):
        # PanedWindow para dividir formulario y lista de productos
        products_pw = ttk.PanedWindow(parent_tab_frame, orient=tk.HORIZONTAL)
        products_pw.pack(expand=True, fill=tk.BOTH)

        form_panel = ttk.Frame(products_pw, padding=5)
        products_pw.add(form_panel, weight=1)
        self._create_product_form_widgets(form_panel)
        self._create_product_action_buttons(form_panel)

        list_panel = ttk.Frame(products_pw, padding=5)
        products_pw.add(list_panel, weight=2)
        self._create_product_list_treeview(list_panel)

    def _create_product_form_widgets(self, parent_frame):
        form_frame = ttk.LabelFrame(parent_frame, text="Detalles del Producto", padding=(15,10))
        form_frame.pack(pady=10, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="ID Producto:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.product_id_entry = ttk.Entry(form_frame, textvariable=self.product_id_var, width=35)
        self.product_id_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Nombre:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.product_name_entry = ttk.Entry(form_frame, textvariable=self.product_name_var, width=35)
        self.product_name_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")
        
        ttk.Label(form_frame, text="Descripción:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.product_desc_entry = ttk.Entry(form_frame, textvariable=self.product_description_var, width=35)
        self.product_desc_entry.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Unidad Medida:").grid(row=3, column=0, padx=5, pady=3, sticky="w")
        self.product_unit_combobox = ttk.Combobox(form_frame, textvariable=self.product_unit_var,
                                                 values=["kg", "g", "litros", "ml", "unidades", "botella", "lata", "paquete"],
                                                 width=33)
        self.product_unit_combobox.grid(row=3, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Stock Mínimo:").grid(row=4, column=0, padx=5, pady=3, sticky="w")
        self.product_min_stock_spinbox = ttk.Spinbox(form_frame, from_=0.0, to=1000.0, increment=1.0, format="%.2f",
                                                    textvariable=self.product_min_stock_var, width=33)
        self.product_min_stock_spinbox.grid(row=4, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Ref. Proveedor:").grid(row=5, column=0, padx=5, pady=3, sticky="w")
        self.product_supplier_entry = ttk.Entry(form_frame, textvariable=self.product_supplier_ref_var, width=35)
        self.product_supplier_entry.grid(row=5, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Costo Unitario: $").grid(row=6, column=0, padx=5, pady=3, sticky="w")
        self.product_cost_spinbox = ttk.Spinbox(form_frame, from_=0.0, to=10000.0, increment=0.1, format="%.2f",
                                               textvariable=self.product_cost_var, width=33)
        self.product_cost_spinbox.grid(row=6, column=1, padx=5, pady=3, sticky="ew")

        self.product_perishable_check = ttk.Checkbutton(form_frame, text="Es Perecedero", variable=self.product_is_perishable_var,
                                                        command=self._toggle_expiry_date_field)
        self.product_perishable_check.grid(row=7, column=0, padx=5, pady=5, sticky="w", columnspan=1)
        
        self.expiry_date_label = ttk.Label(form_frame, text="Fecha Cad. (YYYY-MM-DD):")
        self.expiry_date_label.grid(row=8, column=0, padx=5, pady=3, sticky="w")
        self.product_expiry_entry = ttk.Entry(form_frame, textvariable=self.product_expiry_date_var, width=35)
        self.product_expiry_entry.grid(row=8, column=1, padx=5, pady=3, sticky="ew")
        self._toggle_expiry_date_field() # Llamar para establecer estado inicial

    def _toggle_expiry_date_field(self):
        if self.product_is_perishable_var.get():
            self.expiry_date_label.grid()
            self.product_expiry_entry.grid()
            self.product_expiry_entry.configure(state='normal')
        else:
            self.expiry_date_label.grid_remove()
            self.product_expiry_entry.grid_remove()
            self.product_expiry_date_var.set("") # Limpiar si no es perecedero
            self.product_expiry_entry.configure(state='disabled')


    def _create_product_list_treeview(self, parent_frame):
        tree_frame = ttk.LabelFrame(parent_frame, text="Listado de Productos", padding=(10,5))
        tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        cols = ("id_producto", "nombre", "unidad_medida", "costo_unitario", "perecedero", "stock_minimo")
        self.products_treeview = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse", height=15)
        self.products_treeview.heading("id_producto", text="ID")
        self.products_treeview.heading("nombre", text="Nombre")
        self.products_treeview.heading("unidad_medida", text="Unidad")
        self.products_treeview.heading("costo_unitario", text="Costo")
        self.products_treeview.heading("perecedero", text="Perecedero")
        self.products_treeview.heading("stock_minimo", text="Stock Mín.")

        self.products_treeview.column("id_producto", width=100, anchor="w")
        self.products_treeview.column("nombre", width=200, anchor="w")
        self.products_treeview.column("unidad_medida", width=80, anchor="w")
        self.products_treeview.column("costo_unitario", width=80, anchor="e")
        self.products_treeview.column("perecedero", width=80, anchor="center")
        self.products_treeview.column("stock_minimo", width=80, anchor="e")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.products_treeview.yview)
        self.products_treeview.configure(yscrollcommand=scrollbar.set)
        self.products_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.products_treeview.bind("<<TreeviewSelect>>", self._on_product_selected)

    def _create_product_action_buttons(self, parent_frame):
        buttons_frame = ttk.Frame(parent_frame, padding=(0,10))
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="Nuevo Producto", command=self._clear_product_form_fields, width=18).pack(side=tk.LEFT, padx=3, pady=5)
        ttk.Button(buttons_frame, text="Guardar Producto", command=self._save_product, width=18).pack(side=tk.LEFT, padx=3, pady=5)
        ttk.Button(buttons_frame, text="Eliminar Producto", command=self._delete_selected_product, width=18).pack(side=tk.LEFT, padx=3, pady=5)
        ttk.Button(buttons_frame, text="Marcar como Ingrediente", command=self._mark_as_ingredient, width=22).pack(side=tk.LEFT, padx=3, pady=5)


    # --- Contenido de la Pestaña de Ingredientes (Stock Cocina) ---
    def _create_ingredients_tab_content(self, parent_tab_frame):
        # PanedWindow para dividir lista de ingredientes y formulario de ajuste
        ingredients_pw = ttk.PanedWindow(parent_tab_frame, orient=tk.HORIZONTAL)
        ingredients_pw.pack(expand=True, fill=tk.BOTH)

        ing_list_panel = ttk.Frame(ingredients_pw, padding=5)
        ingredients_pw.add(ing_list_panel, weight=2) # Más espacio para la lista
        self._create_ingredient_list_treeview(ing_list_panel)

        ing_actions_panel = ttk.Frame(ingredients_pw, padding=5)
        ingredients_pw.add(ing_actions_panel, weight=1)
        self._create_ingredient_stock_adjustment_form(ing_actions_panel)
        
    def _create_ingredient_list_treeview(self, parent_frame):
        tree_frame = ttk.LabelFrame(parent_frame, text="Stock de Ingredientes para Cocina", padding=(10,5))
        tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        cols = ("id_ingrediente", "nombre_producto", "cantidad_disponible", "unidad_medida", "ultima_actualizacion")
        self.ingredients_treeview = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse", height=15)
        self.ingredients_treeview.heading("id_ingrediente", text="ID Ingred.")
        self.ingredients_treeview.heading("nombre_producto", text="Nombre")
        self.ingredients_treeview.heading("cantidad_disponible", text="Cant. Disp.")
        self.ingredients_treeview.heading("unidad_medida", text="Unidad Stock")
        self.ingredients_treeview.heading("ultima_actualizacion", text="Últ. Act.")

        self.ingredients_treeview.column("id_ingrediente", width=100, anchor="w")
        self.ingredients_treeview.column("nombre_producto", width=200, anchor="w")
        self.ingredients_treeview.column("cantidad_disponible", width=100, anchor="e")
        self.ingredients_treeview.column("unidad_medida", width=100, anchor="w")
        self.ingredients_treeview.column("ultima_actualizacion", width=150, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.ingredients_treeview.yview)
        self.ingredients_treeview.configure(yscrollcommand=scrollbar.set)
        self.ingredients_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.ingredients_treeview.bind("<<TreeviewSelect>>", self._on_ingredient_selected_for_adjustment)


    def _create_ingredient_stock_adjustment_form(self, parent_frame):
        adj_form_frame = ttk.LabelFrame(parent_frame, text="Ajustar Stock de Ingrediente", padding=(15,10))
        adj_form_frame.pack(pady=10, fill=tk.X)
        adj_form_frame.columnconfigure(1, weight=1)

        ttk.Label(adj_form_frame, text="Ingrediente ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.selected_ingredient_label = ttk.Label(adj_form_frame, textvariable=self.selected_ingredient_id_stock_var, font=("Arial", 10, "bold"))
        self.selected_ingredient_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(adj_form_frame, text="Cantidad a Ajustar:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.stock_adj_qty_spinbox = ttk.Spinbox(adj_form_frame, from_=-10000.0, to=10000.0, increment=0.1, format="%.2f",
                                                textvariable=self.stock_adjustment_quantity_var, width=33)
        self.stock_adj_qty_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(adj_form_frame, text="Motivo/Razón:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.stock_adj_reason_entry = ttk.Entry(adj_form_frame, textvariable=self.stock_adjustment_reason_var, width=35)
        self.stock_adj_reason_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.adjust_stock_button = ttk.Button(adj_form_frame, text="Aplicar Ajuste de Stock", command=self._apply_stock_adjustment, state=tk.DISABLED)
        self.adjust_stock_button.grid(row=3, column=0, columnspan=2, pady=10, padx=5)


    # --- Lógica de Carga y Limpieza ---
    def _load_products_to_treeview(self):
        if not stock_model: return
        for item in self.products_treeview.get_children():
            self.products_treeview.delete(item)
        products = stock_model.get_all_products_list()
        if products:
            for prod in products:
                self.products_treeview.insert("", tk.END, iid=prod['id_producto'], values=(
                    prod.get("id_producto"), prod.get("nombre"), prod.get("unidad_medida"),
                    f"{prod.get('costo_unitario', 0.0):.2f}", "Sí" if prod.get("perecedero") else "No",
                    f"{prod.get('stock_minimo', 0.0):.2f}"
                ))
        elif products is None:
            messagebox.showerror("Error", "No se pudieron cargar los productos.")

    def _load_ingredients_to_treeview(self):
        if not stock_model: return
        for item in self.ingredients_treeview.get_children():
            self.ingredients_treeview.delete(item)
        ingredients = stock_model.get_all_ingredients_list()
        if ingredients:
            for ingr in ingredients:
                self.ingredients_treeview.insert("", tk.END, iid=ingr['id_ingrediente'], values=(
                    ingr.get("id_ingrediente"), ingr.get("nombre_producto"), 
                    f"{ingr.get('cantidad_disponible', 0.0):.3f}", # Más precisión para stock
                    ingr.get("unidad_medida"),
                    ingr.get("ultima_actualizacion", "").strftime('%Y-%m-%d %H:%M') if ingr.get("ultima_actualizacion") else ""
                ))
        elif ingredients is None:
            messagebox.showerror("Error", "No se pudieron cargar los ingredientes de stock.")
        self.selected_ingredient_id_stock_var.set("") # Limpiar selección
        self.adjust_stock_button.config(state=tk.DISABLED)


    def _clear_product_form_fields(self):
        self.product_id_var.set("")
        self.product_name_var.set("")
        self.product_description_var.set("")
        self.product_unit_var.set("")
        self.product_min_stock_var.set(0.0)
        self.product_supplier_ref_var.set("")
        self.product_cost_var.set(0.0)
        self.product_is_perishable_var.set(False)
        self.product_expiry_date_var.set("")
        self._toggle_expiry_date_field()
        
        self.product_id_entry.configure(state='normal')
        if self.products_treeview.selection():
            self.products_treeview.selection_remove(self.products_treeview.selection()[0])
        self.product_id_entry.focus()

    def _clear_ingredient_adjustment_form(self):
        self.selected_ingredient_id_stock_var.set("")
        self.stock_adjustment_quantity_var.set(0.0)
        self.stock_adjustment_reason_var.set("Recepción de Proveedor")
        self.adjust_stock_button.config(state=tk.DISABLED)
        if self.ingredients_treeview.selection():
            self.ingredients_treeview.selection_remove(self.ingredients_treeview.selection()[0])


    # --- Lógica de Eventos y Acciones ---
    def _on_product_selected(self, event=None):
        selected_items = self.products_treeview.selection()
        if not selected_items: return

        product_id = self.products_treeview.selection()[0] # iid es el id_producto
        product_data = stock_model.get_product_by_id(product_id)
        if product_data:
            self.product_id_var.set(product_data.get("id_producto", ""))
            self.product_name_var.set(product_data.get("nombre", ""))
            self.product_description_var.set(product_data.get("descripcion", ""))
            self.product_unit_var.set(product_data.get("unidad_medida", ""))
            self.product_min_stock_var.set(product_data.get("stock_minimo", 0.0))
            self.product_supplier_ref_var.set(product_data.get("proveedor_principal_ref", ""))
            self.product_cost_var.set(product_data.get("costo_unitario", 0.0))
            self.product_is_perishable_var.set(bool(product_data.get("perecedero", False)))
            self.product_expiry_date_var.set(str(product_data.get("fecha_caducidad", "")))
            self._toggle_expiry_date_field()
            self.product_id_entry.configure(state='readonly')
        else:
            self._clear_product_form_fields()

    def _on_ingredient_selected_for_adjustment(self, event=None):
        selected_items = self.ingredients_treeview.selection()
        if not selected_items:
            self.selected_ingredient_id_stock_var.set("")
            self.adjust_stock_button.config(state=tk.DISABLED)
            return
        
        ingredient_id = self.ingredients_treeview.selection()[0] # iid es id_ingrediente
        self.selected_ingredient_id_stock_var.set(ingredient_id)
        self.adjust_stock_button.config(state=tk.NORMAL)
        self.stock_adjustment_quantity_var.set(0.0) # Resetear cantidad
        self.stock_adjustment_reason_var.set("Recepción de Proveedor") # Resetear razón


    def _validate_product_inputs(self):
        if not self.product_id_var.get().strip(): messagebox.showerror("Error Producto", "ID Producto es obligatorio."); return False
        if not self.product_name_var.get().strip(): messagebox.showerror("Error Producto", "Nombre es obligatorio."); return False
        if not self.product_unit_var.get(): messagebox.showerror("Error Producto", "Unidad de Medida es obligatoria."); return False
        try:
            if self.product_cost_var.get() < 0: messagebox.showerror("Error Producto", "Costo no puede ser negativo."); return False
            if self.product_min_stock_var.get() < 0: messagebox.showerror("Error Producto", "Stock Mínimo no puede ser negativo."); return False
        except tk.TclError: messagebox.showerror("Error Producto", "Costo y Stock Mínimo deben ser números."); return False
        if self.product_is_perishable_var.get() and not self.product_expiry_date_var.get().strip():
            messagebox.showerror("Error Producto", "Fecha de caducidad es obligatoria para productos perecederos."); return False
        # Aquí podrías añadir validación de formato de fecha si es necesario
        return True

    def _save_product(self):
        if not stock_model or not self._validate_product_inputs(): return

        product_data = {
            'id_producto': self.product_id_var.get().strip(),
            'nombre': self.product_name_var.get().strip(),
            'descripcion': self.product_description_var.get().strip(),
            'unidad_medida': self.product_unit_var.get(),
            'stock_minimo': self.product_min_stock_var.get(),
            'proveedor_principal_ref': self.product_supplier_ref_var.get().strip() or None,
            'costo_unitario': self.product_cost_var.get(),
            'perecedero': self.product_is_perishable_var.get(),
            'fecha_caducidad': self.product_expiry_date_var.get().strip() if self.product_is_perishable_var.get() else None
        }
        
        is_update = self.product_id_entry.cget('state') == 'readonly'
        if is_update:
            result = stock_model.update_product_details(product_data['id_producto'], product_data)
            if result is not None and result > 0: messagebox.showinfo("Éxito", "Producto actualizado.")
            elif result == 0: messagebox.showinfo("Información", "No se realizaron cambios.")
            else: messagebox.showerror("Error", "No se pudo actualizar el producto.")
        else: # Crear
            if stock_model.get_product_by_id(product_data['id_producto']):
                messagebox.showerror("Error", f"ID de Producto '{product_data['id_producto']}' ya existe.")
                return
            result = stock_model.create_product(product_data)
            if result is not None: messagebox.showinfo("Éxito", "Producto creado.")
            else: messagebox.showerror("Error", "No se pudo crear el producto.")
        
        self._load_products_to_treeview()
        self._clear_product_form_fields()

    def _delete_selected_product(self):
        selected_items = self.products_treeview.selection()
        if not selected_items: messagebox.showwarning("Sin Selección", "Seleccione un producto para eliminar."); return
        
        product_id = self.products_treeview.selection()[0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar producto ID: {product_id}?\nEsto podría fallar si es un ingrediente activo o tiene dependencias."):
            if stock_model:
                result = stock_model.delete_product_by_id(product_id)
                if result is not None and result > 0: messagebox.showinfo("Éxito", "Producto eliminado.")
                else: messagebox.showerror("Error", "No se pudo eliminar el producto. Verifique si es un ingrediente o tiene stock asociado.")
                self._load_products_to_treeview()
                self._load_ingredients_to_treeview() # Recargar ingredientes por si acaso
                self._clear_product_form_fields()

    def _mark_as_ingredient(self):
        selected_items = self.products_treeview.selection()
        if not selected_items: messagebox.showwarning("Sin Selección", "Seleccione un producto para marcarlo como ingrediente."); return
        
        product_id = self.products_treeview.selection()[0]
        
        if stock_model.get_ingredient_by_id(product_id): # Verificar si ya es ingrediente
            messagebox.showinfo("Información", f"El producto '{product_id}' ya está registrado como ingrediente.")
            self.notebook.select(self.ingredients_tab) # Cambiar a la pestaña de ingredientes
            # Seleccionar el ingrediente en el treeview de ingredientes
            for item_id in self.ingredients_treeview.get_children():
                if self.ingredients_treeview.item(item_id, "values")[0] == product_id:
                    self.ingredients_treeview.selection_set(item_id)
                    self.ingredients_treeview.focus(item_id)
                    self._on_ingredient_selected_for_adjustment() # Cargar para ajuste
                    break
            return

        initial_qty_str = simpledialog.askstring("Stock Inicial", 
                                                 f"Ingrese la cantidad inicial de stock para el ingrediente '{product_id}':",
                                                 parent=self)
        if initial_qty_str is not None:
            try:
                initial_qty = float(initial_qty_str)
                if initial_qty < 0:
                    messagebox.showerror("Error", "La cantidad inicial no puede ser negativa.")
                    return
                
                if stock_model:
                    result = stock_model.add_or_update_ingredient_as_product(product_id, initial_qty)
                    if result is not None:
                        messagebox.showinfo("Éxito", f"Producto '{product_id}' marcado como ingrediente con stock inicial de {initial_qty}.")
                        self._load_ingredients_to_treeview() # Recargar lista de ingredientes
                        self.notebook.select(self.ingredients_tab) # Cambiar a la pestaña de ingredientes
                    else:
                        messagebox.showerror("Error", f"No se pudo marcar '{product_id}' como ingrediente.")
            except ValueError:
                messagebox.showerror("Error de Entrada", "La cantidad inicial debe ser un número.")


    def _apply_stock_adjustment(self):
        ingredient_id = self.selected_ingredient_id_stock_var.get()
        if not ingredient_id:
            messagebox.showwarning("Sin Selección", "Seleccione un ingrediente de la lista para ajustar su stock.")
            return
        
        try:
            quantity_adj = self.stock_adjustment_quantity_var.get()
        except tk.TclError:
            messagebox.showerror("Error de Cantidad", "La cantidad de ajuste no es válida.")
            return
        
        reason = self.stock_adjustment_reason_var.get().strip()
        if not reason:
            messagebox.showerror("Error de Motivo", "Por favor, ingrese un motivo para el ajuste de stock.")
            return

        if stock_model:
            is_deduction = quantity_adj < 0
            actual_change_amount = abs(quantity_adj)

            result = stock_model.update_ingredient_stock(ingredient_id, actual_change_amount, is_deduction, reason)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Stock para '{ingredient_id}' ajustado correctamente.")
            elif result == 0 and not is_deduction: # Podría ser 0 si se añade 0
                 messagebox.showinfo("Información", f"No se realizó ningún cambio en el stock para '{ingredient_id}'.")
            else: # result es None (ej. stock insuficiente para deducción) o error
                # El modelo ya imprime el error específico (ej. stock insuficiente)
                messagebox.showerror("Error de Ajuste", f"No se pudo ajustar el stock para '{ingredient_id}'. Verifique la consola para detalles.")
            
            self._load_ingredients_to_treeview()
            self._clear_ingredient_adjustment_form()


# --- Para probar esta vista de forma aislada ---
if __name__ == '__main__':
    if not stock_model:
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico de Módulo", "No se pudo cargar 'stock_model'.")
        root_error.destroy()
    else:
        root = tk.Tk()
        root.title("Gestión de Stock (Prueba Aislada)")
        root.geometry("1100x700")

        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes: style.theme_use('clam')
        
        stock_view_frame = StockManagementView(root)
        stock_view_frame.pack(fill=tk.BOTH, expand=True)

        root.mainloop()

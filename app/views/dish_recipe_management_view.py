# app/views/dish_recipe_management_view.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import traceback # Para imprimir tracebacks completos

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from app.models import menu_model, recipe_model, stock_model
except ImportError:
    # Fallback si la estructura es diferente o se ejecuta directamente
    print("Advertencia: Falló la importación principal en DishRecipeManagementView. Intentando fallback...")
    try:
        from ..models import menu_model, recipe_model, stock_model
    except ImportError:
        try:
            from models import menu_model, recipe_model, stock_model
        except ImportError as e:
            print(f"Error CRÍTICO: No se pudieron importar modelos en DishRecipeManagementView: {e}")
            menu_model = recipe_model = stock_model = None

class DishRecipeManagementView(ttk.Frame):
    def __init__(self, parent_container, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container

        if not all([menu_model, recipe_model, stock_model]):
            error_label = ttk.Label(self, text="Error crítico: Módulos de modelo esenciales no disponibles.", foreground="red")
            error_label.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
            return

        # Variables para el formulario del Plato
        self.dish_id_var = tk.StringVar()
        self.dish_name_var = tk.StringVar()
        self.dish_description_var = tk.StringVar()
        self.dish_category_var = tk.StringVar()
        self.dish_price_var = tk.DoubleVar(value=0.0)
        self.dish_prep_time_var = tk.IntVar(value=0)
        self.dish_is_active_var = tk.BooleanVar(value=True)

        self._selected_dish_id_for_edit = None 

        # Variables para el formulario de Ingrediente de Receta
        self.selected_ingredient_for_recipe_var = tk.StringVar()
        self.recipe_ingredient_quantity_var = tk.DoubleVar(value=1.0)
        self.recipe_ingredient_unit_var = tk.StringVar()
        # self.recipe_instructions_var no se usa, se accede directo al Text widget

        self.selected_recipe_entry_id = None

        self._create_layout()
        self._load_all_dishes_to_treeview()
        self._load_available_ingredients_to_combobox()
        self._clear_dish_form_fields() # Estado inicial

    def _create_layout(self):
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        dish_management_frame = ttk.Frame(main_paned_window, padding=10)
        main_paned_window.add(dish_management_frame, weight=1)
        self._create_dish_form_widgets(dish_management_frame)
        self._create_dish_list_treeview(dish_management_frame) # <--- LLAMADA AL MÉTODO
        self._create_dish_action_buttons(dish_management_frame)

        recipe_management_frame = ttk.Frame(main_paned_window, padding=10)
        main_paned_window.add(recipe_management_frame, weight=2)
        self._create_recipe_display_treeview(recipe_management_frame)
        self._create_recipe_ingredient_form_widgets(recipe_management_frame)
        self._create_recipe_action_buttons(recipe_management_frame)

    def _create_dish_form_widgets(self, parent_frame):
        form_frame = ttk.LabelFrame(parent_frame, text="Detalles del Plato", padding=(15,10))
        form_frame.pack(pady=10, fill=tk.X)
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="ID Plato:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.dish_id_display_label = ttk.Label(form_frame, textvariable=self.dish_id_var, width=40, font=("Arial", 10, "italic"), anchor="w")
        self.dish_id_display_label.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Nombre Plato*:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.dish_name_entry = ttk.Entry(form_frame, textvariable=self.dish_name_var, width=40)
        self.dish_name_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Descripción:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.dish_desc_entry = ttk.Entry(form_frame, textvariable=self.dish_description_var, width=40)
        self.dish_desc_entry.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Categoría*:").grid(row=3, column=0, padx=5, pady=3, sticky="w")
        self.dish_category_combobox = ttk.Combobox(form_frame, textvariable=self.dish_category_var,
                                                   values=["entrada", "principal", "postre", "bebida", "acompañamiento", "snack"],
                                                   state="readonly", width=38)
        self.dish_category_combobox.grid(row=3, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="Precio Venta*: $").grid(row=4, column=0, padx=5, pady=3, sticky="w")
        self.dish_price_spinbox = ttk.Spinbox(form_frame, from_=0.0, to=1000.0, increment=0.01, format="%.2f",
                                             textvariable=self.dish_price_var, width=38)
        self.dish_price_spinbox.grid(row=4, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(form_frame, text="T. Prep (min):").grid(row=5, column=0, padx=5, pady=3, sticky="w")
        self.dish_prep_time_spinbox = ttk.Spinbox(form_frame, from_=0, to=120, increment=1,
                                                 textvariable=self.dish_prep_time_var, width=38)
        self.dish_prep_time_spinbox.grid(row=5, column=1, padx=5, pady=3, sticky="ew")
        
        self.dish_active_checkbutton = ttk.Checkbutton(form_frame, text="Plato Activo", variable=self.dish_is_active_var)
        self.dish_active_checkbutton.grid(row=6, column=1, padx=5, pady=5, sticky="w")

    # ESTA ES LA FUNCIÓN QUE FALTABA O ESTABA MAL NOMBRADA EN LA LLAMADA
    def _create_dish_list_treeview(self, parent_frame):
        tree_frame = ttk.LabelFrame(parent_frame, text="Listado de Platos del Menú", padding=(10,5))
        tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        cols = ("id_plato", "nombre_plato", "categoria", "precio_venta", "activo")
        self.dishes_treeview = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse", height=10)
        self.dishes_treeview.heading("id_plato", text="ID")
        self.dishes_treeview.heading("nombre_plato", text="Nombre")
        self.dishes_treeview.heading("categoria", text="Categoría")
        self.dishes_treeview.heading("precio_venta", text="Precio")
        self.dishes_treeview.heading("activo", text="Activo")

        self.dishes_treeview.column("id_plato", width=100, anchor="w", stretch=tk.NO) # Ajustado ancho
        self.dishes_treeview.column("nombre_plato", width=200, anchor="w")
        self.dishes_treeview.column("categoria", width=100, anchor="w")
        self.dishes_treeview.column("precio_venta", width=70, anchor="e")
        self.dishes_treeview.column("activo", width=60, anchor="center", stretch=tk.NO) # Ajustado ancho

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.dishes_treeview.yview)
        self.dishes_treeview.configure(yscrollcommand=scrollbar.set)
        self.dishes_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.dishes_treeview.bind("<<TreeviewSelect>>", self._on_dish_selected_from_list)

    def _create_dish_action_buttons(self, parent_frame):
        buttons_frame = ttk.Frame(parent_frame, padding=(0,5))
        buttons_frame.pack(fill=tk.X)
        ttk.Button(buttons_frame, text="Nuevo/Limpiar", command=self._clear_dish_form_fields, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Guardar Plato", command=self._save_dish, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar Plato", command=self._delete_selected_dish, width=15).pack(side=tk.LEFT, padx=5)

    def _create_recipe_display_treeview(self, parent_frame):
        recipe_display_frame = ttk.LabelFrame(parent_frame, text="Receta del Plato Seleccionado", padding=(10,5))
        recipe_display_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        recipe_cols = ("id_receta", "nombre_ingrediente", "cantidad_necesaria", "unidad_medida_receta", "instrucciones") # Añadir instrucciones
        self.recipe_treeview = ttk.Treeview(recipe_display_frame, columns=recipe_cols, show="headings", selectmode="browse", height=8)
        self.recipe_treeview.heading("id_receta", text="ID Receta")
        self.recipe_treeview.heading("nombre_ingrediente", text="Ingrediente")
        self.recipe_treeview.heading("cantidad_necesaria", text="Cantidad")
        self.recipe_treeview.heading("unidad_medida_receta", text="Unidad")
        self.recipe_treeview.heading("instrucciones", text="Instrucciones")


        self.recipe_treeview.column("id_receta", width=70, anchor="center", stretch=tk.NO)
        self.recipe_treeview.column("nombre_ingrediente", width=180, anchor="w")
        self.recipe_treeview.column("cantidad_necesaria", width=80, anchor="e")
        self.recipe_treeview.column("unidad_medida_receta", width=100, anchor="w")
        self.recipe_treeview.column("instrucciones", width=200, anchor="w") # Nueva columna

        self.recipe_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recipe_scrollbar = ttk.Scrollbar(recipe_display_frame, orient=tk.VERTICAL, command=self.recipe_treeview.yview)
        self.recipe_treeview.configure(yscrollcommand=recipe_scrollbar.set)
        recipe_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recipe_treeview.bind("<<TreeviewSelect>>", self._on_recipe_ingredient_selected)

    def _create_recipe_ingredient_form_widgets(self, parent_frame):
        recipe_form_frame = ttk.LabelFrame(parent_frame, text="Añadir/Editar Ingrediente en Receta", padding=(15,10))
        recipe_form_frame.pack(pady=10, fill=tk.X)
        recipe_form_frame.columnconfigure(1, weight=1)

        ttk.Label(recipe_form_frame, text="Ingrediente:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.recipe_ingredient_combobox = ttk.Combobox(recipe_form_frame, textvariable=self.selected_ingredient_for_recipe_var,
                                                       state="readonly", width=38)
        self.recipe_ingredient_combobox.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(recipe_form_frame, text="Cantidad*:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.recipe_qty_spinbox = ttk.Spinbox(recipe_form_frame, from_=0.001, to=10000.0, increment=0.01, format="%.3f", # .3f para ingredientes
                                              textvariable=self.recipe_ingredient_quantity_var, width=38)
        self.recipe_qty_spinbox.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(recipe_form_frame, text="Unidad Receta*:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.recipe_unit_combobox = ttk.Combobox(recipe_form_frame, textvariable=self.recipe_ingredient_unit_var,
                                                 values=["g", "kg", "ml", "L", "unidades", "cucharada", "pizca", "taza", "pieza"], # Más opciones
                                                 width=38) 
        self.recipe_unit_combobox.grid(row=2, column=1, padx=5, pady=3, sticky="ew")
        
        ttk.Label(recipe_form_frame, text="Instrucciones (Paso):").grid(row=3, column=0, padx=5, pady=3, sticky="nw")
        self.recipe_instr_text = tk.Text(recipe_form_frame, height=3, width=30, relief=tk.SUNKEN, borderwidth=1)
        self.recipe_instr_text.grid(row=3, column=1, padx=5, pady=3, sticky="ew")

    def _create_recipe_action_buttons(self, parent_frame):
        buttons_frame = ttk.Frame(parent_frame, padding=(0,5))
        buttons_frame.pack(fill=tk.X)
        self.add_recipe_ing_btn = ttk.Button(buttons_frame, text="Añadir Ingrediente", command=self._add_ingredient_to_current_recipe, width=20, state=tk.DISABLED)
        self.add_recipe_ing_btn.pack(side=tk.LEFT, padx=5)
        self.update_recipe_ing_btn = ttk.Button(buttons_frame, text="Actualizar Ingrediente", command=self._update_selected_recipe_ingredient, width=20, state=tk.DISABLED)
        self.update_recipe_ing_btn.pack(side=tk.LEFT, padx=5)
        self.remove_recipe_ing_btn = ttk.Button(buttons_frame, text="Quitar Ingrediente", command=self._remove_selected_recipe_ingredient, width=20, state=tk.DISABLED)
        self.remove_recipe_ing_btn.pack(side=tk.LEFT, padx=5)

    def _load_all_dishes_to_treeview(self):
        if not menu_model: return
        current_selection_id = None
        if self.dishes_treeview.selection():
            current_selection_id = self.dishes_treeview.selection()[0]

        for item in self.dishes_treeview.get_children():
            self.dishes_treeview.delete(item)
        
        dishes = menu_model.get_all_dishes_list()
        if dishes:
            for dish in dishes:
                self.dishes_treeview.insert("", tk.END, iid=dish['id_plato'], values=(
                    dish.get("id_plato", ""), dish.get("nombre_plato", ""),
                    dish.get("categoria", ""), f"{dish.get('precio_venta', 0.0):.2f}",
                    "Sí" if dish.get("activo") else "No"
                ))
        elif dishes is None:
            messagebox.showerror("Error", "No se pudieron cargar los platos del menú.")

        if current_selection_id and self.dishes_treeview.exists(current_selection_id):
            self.dishes_treeview.selection_set(current_selection_id)
            self.dishes_treeview.focus(current_selection_id)

    def _load_available_ingredients_to_combobox(self):
        if not stock_model: return
        ingredients = stock_model.get_all_ingredients_list()
        ingredient_names_with_ids = []
        self.ingredient_name_to_id_map = {} # Reiniciar mapeo
        if ingredients:
            for ing in ingredients:
                display_name = f"{ing['nombre_producto']} ({ing['unidad_medida']}) [{ing['id_ingrediente']}]"
                ingredient_names_with_ids.append(display_name)
                self.ingredient_name_to_id_map[display_name] = ing['id_ingrediente']
        
        self.recipe_ingredient_combobox['values'] = ingredient_names_with_ids
        if ingredient_names_with_ids:
            self.recipe_ingredient_combobox.current(0)
        else:
            self.selected_ingredient_for_recipe_var.set("")

    def _clear_dish_form_fields(self):
        self._selected_dish_id_for_edit = None
        self.dish_id_var.set("(Nuevo Plato - ID se autogenerará)")
        self.dish_name_var.set("")
        self.dish_description_var.set("")
        self.dish_category_var.set("")
        self.dish_price_var.set(0.0)
        self.dish_prep_time_var.set(0)
        self.dish_is_active_var.set(True)
        
        if self.dishes_treeview.selection():
            self.dishes_treeview.selection_remove(self.dishes_treeview.selection()[0])
        
        self._clear_recipe_section()
        self._update_recipe_buttons_state()
        self.dish_name_entry.focus()

    def _clear_recipe_ingredient_form(self):
        self.selected_ingredient_for_recipe_var.set("")
        if hasattr(self, 'recipe_ingredient_combobox') and self.recipe_ingredient_combobox.cget('values'): # Chequear si hay valores
             self.recipe_ingredient_combobox.set('') 
             if self.recipe_ingredient_combobox.cget('values'): # Si aún hay, seleccionar el primero
                self.recipe_ingredient_combobox.current(0)
        self.recipe_ingredient_quantity_var.set(1.0)
        self.recipe_ingredient_unit_var.set("")
        if hasattr(self, 'recipe_instr_text'): self.recipe_instr_text.delete("1.0", tk.END)
        self.selected_recipe_entry_id = None
        # El estado de los botones se actualiza en _update_recipe_buttons_state

    def _clear_recipe_section(self):
        if hasattr(self, 'recipe_treeview'):
            for item in self.recipe_treeview.get_children():
                self.recipe_treeview.delete(item)
        self._clear_recipe_ingredient_form()
        # No llamar a _update_recipe_buttons_state aquí directamente, se llama desde el contexto superior

    def _update_recipe_buttons_state(self):
        can_add_ingredient = bool(self._selected_dish_id_for_edit)
        self.add_recipe_ing_btn.config(state=tk.NORMAL if can_add_ingredient else tk.DISABLED)

        can_modify_ingredient = bool(self.selected_recipe_entry_id)
        self.update_recipe_ing_btn.config(state=tk.NORMAL if can_modify_ingredient else tk.DISABLED)
        self.remove_recipe_ing_btn.config(state=tk.NORMAL if can_modify_ingredient else tk.DISABLED)

    def _on_dish_selected_from_list(self, event=None):
        selected_items = self.dishes_treeview.selection()
        if not selected_items: 
            if self._selected_dish_id_for_edit is not None: # Solo limpiar si antes había algo seleccionado
                self._clear_dish_form_fields()
            return

        self._selected_dish_id_for_edit = selected_items[0]
        dish_data = menu_model.get_dish_by_id(self._selected_dish_id_for_edit)
        if dish_data:
            self.dish_id_var.set(dish_data.get("id_plato", ""))
            self.dish_name_var.set(dish_data.get("nombre_plato", ""))
            self.dish_description_var.set(dish_data.get("descripcion", ""))
            self.dish_category_var.set(dish_data.get("categoria", ""))
            self.dish_price_var.set(dish_data.get("precio_venta", 0.0))
            self.dish_prep_time_var.set(dish_data.get("tiempo_preparacion_min", 0))
            self.dish_is_active_var.set(dish_data.get("activo", True))
            self._load_recipe_for_selected_dish()
            self.dish_name_entry.focus()
        else:
            messagebox.showerror("Error", f"No se pudieron cargar los detalles del plato {self._selected_dish_id_for_edit}.")
            self._clear_dish_form_fields()
        self._update_recipe_buttons_state()

    def _load_recipe_for_selected_dish(self):
        self._clear_recipe_section()
        if not self._selected_dish_id_for_edit or not recipe_model:
            self._update_recipe_buttons_state()
            return
        
        recipe_items = recipe_model.get_recipe_for_dish(self._selected_dish_id_for_edit)
        if recipe_items:
            for item in recipe_items:
                self.recipe_treeview.insert("", tk.END, iid=item['id_receta'], values=(
                    item.get('id_receta'), item.get('nombre_ingrediente', 'Desconocido'),
                    f"{item.get('cantidad_necesaria', 0.0):.3f}", # Formato para decimales
                    item.get('unidad_medida_receta'),
                    item.get('instrucciones_paso', '') # Añadir instrucciones al treeview
                ))
        elif recipe_items is None:
            messagebox.showerror("Error", f"No se pudo cargar la receta para el plato {self._selected_dish_id_for_edit}.")
        self._update_recipe_buttons_state()

    def _on_recipe_ingredient_selected(self, event=None):
        selected_items = self.recipe_treeview.selection()
        if not selected_items:
            self._clear_recipe_ingredient_form()
            self._update_recipe_buttons_state()
            return

        self.selected_recipe_entry_id = self.recipe_treeview.item(selected_items[0], "values")[0]
        
        full_recipe = recipe_model.get_recipe_for_dish(self._selected_dish_id_for_edit)
        selected_recipe_item_data = None
        if full_recipe:
            for item_data in full_recipe:
                if str(item_data.get('id_receta')) == str(self.selected_recipe_entry_id):
                    selected_recipe_item_data = item_data
                    break
        
        if selected_recipe_item_data:
            ingredient_id_from_recipe = selected_recipe_item_data.get('id_ingrediente')
            display_name_to_select = ""
            if hasattr(self, 'ingredient_name_to_id_map'):
                for dn, i_id in self.ingredient_name_to_id_map.items():
                    if i_id == ingredient_id_from_recipe:
                        display_name_to_select = dn
                        break
            self.selected_ingredient_for_recipe_var.set(display_name_to_select)
            self.recipe_ingredient_quantity_var.set(selected_recipe_item_data.get('cantidad_necesaria', 1.0))
            self.recipe_ingredient_unit_var.set(selected_recipe_item_data.get('unidad_medida_receta', ""))
            self.recipe_instr_text.delete("1.0", tk.END)
            self.recipe_instr_text.insert("1.0", selected_recipe_item_data.get('instrucciones_paso', ""))
        else:
            self._clear_recipe_ingredient_form()
        self._update_recipe_buttons_state()

    def _validate_dish_inputs(self):
        if not self.dish_name_var.get().strip():
            messagebox.showerror("Error Plato", "Nombre del Plato es obligatorio.")
            return False
        if not self.dish_category_var.get():
            messagebox.showerror("Error Plato", "Categoría es obligatoria.")
            return False
        try:
            price = self.dish_price_var.get()
            if price < 0:
                messagebox.showerror("Error Plato", "Precio no puede ser negativo.")
                return False
        except tk.TclError:
            messagebox.showerror("Error Plato", "Precio debe ser un número válido.")
            return False
        return True

    def _save_dish(self):
        if not menu_model or not self._validate_dish_inputs():
            return

        dish_data = {
            'nombre_plato': self.dish_name_var.get().strip(),
            'descripcion': self.dish_description_var.get().strip() or None,
            'categoria': self.dish_category_var.get(),
            'precio_venta': self.dish_price_var.get(),
            'tiempo_preparacion_min': self.dish_prep_time_var.get() if self.dish_prep_time_var.get() > 0 else None,
            'activo': self.dish_is_active_var.get()
        }
        
        saved_or_updated_id = None

        if self._selected_dish_id_for_edit: # Modo Actualización
            id_for_operation = self._selected_dish_id_for_edit
            result = menu_model.update_dish_details(id_for_operation, dish_data)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Plato '{id_for_operation}' actualizado.")
                saved_or_updated_id = id_for_operation
            elif result == 0:
                messagebox.showinfo("Información", "No se realizaron cambios en el plato.")
                saved_or_updated_id = id_for_operation
            else:
                messagebox.showerror("Error", f"No se pudo actualizar el plato '{id_for_operation}'.")
                return
        else: # Modo Creación
            created_id = menu_model.create_dish(dish_data)
            if created_id:
                messagebox.showinfo("Éxito", f"Plato '{dish_data['nombre_plato']}' creado con ID: {created_id}. Ahora puede añadirle ingredientes a su receta.")
                self._selected_dish_id_for_edit = created_id
                saved_or_updated_id = created_id
            else:
                messagebox.showerror("Error", f"No se pudo crear el plato '{dish_data['nombre_plato']}'.")
                return
        
        self._load_all_dishes_to_treeview()
        if saved_or_updated_id and self.dishes_treeview.exists(saved_or_updated_id):
            self.dishes_treeview.selection_set(saved_or_updated_id)
            self.dishes_treeview.focus(saved_or_updated_id)
            self._on_dish_selected_from_list() # Esto cargará los datos y la receta
        else:
            self._clear_dish_form_fields()
        self._update_recipe_buttons_state()


    def _delete_selected_dish(self):
        if not self._selected_dish_id_for_edit:
            messagebox.showwarning("Sin Selección", "Seleccione un plato para eliminar.")
            return
        
        dish_id_to_delete = self._selected_dish_id_for_edit
        confirm_text = (f"¿Está seguro de que desea eliminar el plato ID: {dish_id_to_delete}?\n"
                        "Esto también eliminará su receta asociada (si existe).\n"
                        "¡Esta acción es permanente!")
        if messagebox.askyesno("Confirmar Eliminación", confirm_text):
            if menu_model:
                result = menu_model.delete_dish_by_id(dish_id_to_delete)
                if result is not None and result > 0:
                    messagebox.showinfo("Éxito", f"Plato '{dish_id_to_delete}' y su receta eliminados.")
                else:
                    messagebox.showerror("Error", f"No se pudo eliminar el plato '{dish_id_to_delete}'.\nPuede estar en uso en comandas no finalizadas.")
                self._load_all_dishes_to_treeview()
                self._clear_dish_form_fields()

    def _validate_recipe_ingredient_inputs(self):
        if not self.selected_ingredient_for_recipe_var.get():
            messagebox.showerror("Error Receta", "Seleccione un ingrediente del stock.")
            return False
        try:
            qty = self.recipe_ingredient_quantity_var.get()
            if qty <= 0: # Cantidad debe ser > 0
                messagebox.showerror("Error Receta", "La cantidad debe ser mayor que cero.")
                return False
        except tk.TclError:
            messagebox.showerror("Error Receta", "Cantidad de ingrediente inválida.")
            return False
        if not self.recipe_ingredient_unit_var.get().strip():
            messagebox.showerror("Error Receta", "La unidad de medida para la receta es obligatoria.")
            return False
        return True

    def _add_ingredient_to_current_recipe(self):
        if not self._selected_dish_id_for_edit:
            messagebox.showwarning("Sin Plato", "Seleccione o guarde un plato primero para añadirle ingredientes a su receta.")
            return
        if not recipe_model or not self._validate_recipe_ingredient_inputs():
            return

        display_name_selected = self.selected_ingredient_for_recipe_var.get()
        ingredient_id_from_stock = None
        if hasattr(self, 'ingredient_name_to_id_map'):
            ingredient_id_from_stock = self.ingredient_name_to_id_map.get(display_name_selected)

        if not ingredient_id_from_stock:
            messagebox.showerror("Error", "Ingrediente seleccionado no válido o no encontrado en el mapeo.")
            return

        quantity = self.recipe_ingredient_quantity_var.get()
        unit = self.recipe_ingredient_unit_var.get().strip()
        instructions = self.recipe_instr_text.get("1.0", tk.END).strip()

        result = recipe_model.add_ingredient_to_recipe(
            self._selected_dish_id_for_edit, ingredient_id_from_stock, quantity, unit, instructions
        )
        if result:
            messagebox.showinfo("Éxito", "Ingrediente añadido a la receta.")
            self._load_recipe_for_selected_dish()
            self._clear_recipe_ingredient_form()
        else:
            messagebox.showerror("Error", "No se pudo añadir el ingrediente a la receta.\nVerifique que el ingrediente no esté ya en la receta para este plato.")

    def _update_selected_recipe_ingredient(self):
        if not self.selected_recipe_entry_id:
            messagebox.showwarning("Sin Selección", "Seleccione un ingrediente de la receta para actualizar.")
            return
        if not recipe_model or not self._validate_recipe_ingredient_inputs():
            return
        
        quantity = self.recipe_ingredient_quantity_var.get()
        unit = self.recipe_ingredient_unit_var.get().strip()
        instructions = self.recipe_instr_text.get("1.0", tk.END).strip()

        result = recipe_model.update_recipe_ingredient(
            self.selected_recipe_entry_id,
            new_quantity=quantity, new_unit=unit, new_instructions=instructions
        )
        if result is not None and result > 0:
            messagebox.showinfo("Éxito", "Ingrediente de la receta actualizado.")
            self._load_recipe_for_selected_dish()
            self._clear_recipe_ingredient_form()
        elif result == 0:
            messagebox.showinfo("Información", "No se realizaron cambios en el ingrediente de la receta.")
        else:
            messagebox.showerror("Error", "No se pudo actualizar el ingrediente de la receta.")

    def _remove_selected_recipe_ingredient(self):
        if not self.selected_recipe_entry_id:
            messagebox.showwarning("Sin Selección", "Seleccione un ingrediente de la receta para eliminar.")
            return
        if not recipe_model: return

        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea quitar este ingrediente de la receta?"):
            result = recipe_model.remove_ingredient_from_recipe(self.selected_recipe_entry_id)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", "Ingrediente eliminado de la receta.")
                self._load_recipe_for_selected_dish()
                self._clear_recipe_ingredient_form()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el ingrediente de la receta.")

# --- Para probar esta vista de forma aislada ---
if __name__ == '__main__':
    if not all([menu_model, recipe_model, stock_model]):
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico de Módulo", 
                             "No se pudieron cargar módulos de modelo esenciales para probar la vista de gestión de menú/recetas.")
        root_error.destroy()
    else:
        root = tk.Tk()
        root.title("Gestión de Menú y Recetas (Prueba Aislada)")
        root.geometry("1250x750") # Un poco más ancho

        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes: style.theme_use('clam')
        elif 'vista' in available_themes: style.theme_use('vista')
        
        management_view_frame = DishRecipeManagementView(root)
        management_view_frame.pack(fill=tk.BOTH, expand=True)
        root.mainloop()
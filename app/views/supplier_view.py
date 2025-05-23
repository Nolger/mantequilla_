# app/views/supplier_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import traceback # Para imprimir tracebacks completos

# Ajusta la ruta de importación según tu estructura de proyecto.
try:
    from app.models import supplier_model 
except ImportError:
    try:
        from ..models import supplier_model
    except ImportError:
        try:
            from models import supplier_model
        except ImportError as e:
            print(f"Error CRÍTICO: No se pudo importar el módulo supplier_model.py en SupplierView: {e}")
            supplier_model = None

class SupplierView(ttk.Frame):
    def __init__(self, parent_container, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container
        
        if not supplier_model:
            error_label = ttk.Label(self, text="Error crítico: El modelo de proveedores no está disponible.", foreground="red")
            error_label.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
            return

        # Variables para los campos del formulario
        self.supplier_id_var = tk.StringVar() # Almacena el ID del proveedor seleccionado/creado
        self.supplier_name_var = tk.StringVar()
        self.supplier_phone_var = tk.StringVar()
        self.supplier_email_var = tk.StringVar()
        # No se necesita self.supplier_products_var si se accede directamente al Text widget

        # Variable para rastrear el ID del proveedor actualmente seleccionado para edición/actualización
        self._selected_supplier_id_for_edit = None 

        self._create_widgets()
        self.load_suppliers_to_treeview()
        self.clear_form_fields() # Establece el estado inicial del formulario

    def _create_widgets(self):
        # Frame para el formulario
        form_frame = ttk.LabelFrame(self, text="Datos del Proveedor", padding=(15, 10))
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew") # sticky="nsew" para que se expanda
        form_frame.columnconfigure(1, weight=1)

        # ID Proveedor (Ahora solo un Label para mostrarlo)
        ttk.Label(form_frame, text="ID Proveedor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.id_display_label = ttk.Label(form_frame, textvariable=self.supplier_id_var, width=40, font=("Arial", 10, "italic"), anchor="w")
        self.id_display_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Nombre
        ttk.Label(form_frame, text="Nombre*:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ttk.Entry(form_frame, textvariable=self.supplier_name_var, width=40)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Teléfono
        ttk.Label(form_frame, text="Teléfono:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.phone_entry = ttk.Entry(form_frame, textvariable=self.supplier_phone_var, width=40)
        self.phone_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Correo
        ttk.Label(form_frame, text="Correo Electrónico:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.email_entry = ttk.Entry(form_frame, textvariable=self.supplier_email_var, width=40)
        self.email_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Productos que Suministra
        ttk.Label(form_frame, text="Productos Suministra:").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
        self.products_text = tk.Text(form_frame, height=4, width=30, wrap=tk.WORD, relief=tk.SUNKEN, borderwidth=1)
        self.products_text.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        products_text_scrollbar = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=self.products_text.yview)
        products_text_scrollbar.grid(row=4, column=2, padx=(0,5), pady=5, sticky="ns")
        self.products_text.configure(yscrollcommand=products_text_scrollbar.set)

        # Frame para los botones de acción
        buttons_frame = ttk.Frame(self, padding=(0, 10))
        buttons_frame.grid(row=1, column=0, pady=10, sticky="ew")
        
        ttk.Button(buttons_frame, text="Nuevo/Limpiar", command=self.clear_form_fields, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="Guardar", command=self.save_supplier, width=12).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="Eliminar", command=self.delete_selected_supplier, width=12).pack(side=tk.LEFT, padx=10)

        # Treeview para mostrar la lista de proveedores
        tree_frame = ttk.LabelFrame(self, text="Listado de Proveedores", padding=(10,5))
        tree_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        columns = ("id_proveedor", "nombre", "telefono", "correo", "producto_suministra")
        self.suppliers_treeview = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.suppliers_treeview.heading("id_proveedor", text="ID")
        self.suppliers_treeview.heading("nombre", text="Nombre")
        self.suppliers_treeview.heading("telefono", text="Teléfono")
        self.suppliers_treeview.heading("correo", text="Correo")
        self.suppliers_treeview.heading("producto_suministra", text="Productos")

        self.suppliers_treeview.column("id_proveedor", width=120, anchor="w", stretch=tk.NO)
        self.suppliers_treeview.column("nombre", width=200, anchor="w")
        self.suppliers_treeview.column("telefono", width=100, anchor="w")
        self.suppliers_treeview.column("correo", width=180, anchor="w")
        self.suppliers_treeview.column("producto_suministra", width=250, anchor="w")

        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.suppliers_treeview.yview)
        self.suppliers_treeview.configure(yscroll=tree_scrollbar.set)
        
        self.suppliers_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.suppliers_treeview.bind("<<TreeviewSelect>>", self.on_supplier_select)

    def load_suppliers_to_treeview(self):
        if not supplier_model: return
        
        current_selection_id = None
        if self.suppliers_treeview.selection():
            try:
                current_selection_id = self.suppliers_treeview.selection()[0]
            except IndexError: # Puede pasar si la selección se borra mientras se procesa
                current_selection_id = None

        for item in self.suppliers_treeview.get_children():
            self.suppliers_treeview.delete(item)
        
        suppliers_list = supplier_model.get_all_suppliers_list()
        if suppliers_list:
            for sup in suppliers_list:
                self.suppliers_treeview.insert("", tk.END, iid=sup['id_proveedor'], values=(
                    sup.get("id_proveedor", ""), sup.get("nombre", ""),
                    sup.get("telefono", ""), sup.get("correo", ""),
                    sup.get("producto_suministra", "")
                ))
        elif suppliers_list is None:
             messagebox.showerror("Error de Carga", "No se pudieron cargar los proveedores desde la base de datos.")
        
        if current_selection_id and self.suppliers_treeview.exists(current_selection_id):
            self.suppliers_treeview.selection_set(current_selection_id)
            self.suppliers_treeview.focus(current_selection_id)
            self.suppliers_treeview.see(current_selection_id) # Asegurar que sea visible

    def on_supplier_select(self, event=None):
        selected_items = self.suppliers_treeview.selection()
        if not selected_items:
            # Si no hay selección, y el formulario no está ya en modo "nuevo", limpiar.
            # Esto evita limpiar si el usuario acaba de presionar "Nuevo/Limpiar".
            if self._selected_supplier_id_for_edit is not None: # Solo limpiar si antes había algo seleccionado
                self.clear_form_fields()
            return 

        self._selected_supplier_id_for_edit = selected_items[0]
        supplier_data = supplier_model.get_supplier_by_id(self._selected_supplier_id_for_edit)

        if supplier_data:
            self.supplier_id_var.set(supplier_data.get("id_proveedor", ""))
            self.supplier_name_var.set(supplier_data.get("nombre", ""))
            self.supplier_phone_var.set(supplier_data.get("telefono", ""))
            self.supplier_email_var.set(supplier_data.get("correo", ""))
            self.products_text.delete("1.0", tk.END)
            self.products_text.insert("1.0", supplier_data.get("producto_suministra", ""))
            self.name_entry.focus()
        else:
            messagebox.showwarning("Carga Fallida", f"No se encontraron datos para el proveedor ID: {self._selected_supplier_id_for_edit}")
            self.clear_form_fields() # Limpiar si falla la carga del proveedor seleccionado

    def clear_form_fields(self):
        """ Limpia los campos del formulario y lo prepara para un nuevo proveedor. """
        self._selected_supplier_id_for_edit = None
        self.supplier_id_var.set("(Nuevo Proveedor - ID se autogenerará)")
        self.supplier_name_var.set("")
        self.supplier_phone_var.set("")
        self.supplier_email_var.set("")
        self.products_text.delete("1.0", tk.END)
        
        # Deseleccionar del Treeview si hay algo seleccionado
        if self.suppliers_treeview.selection():
            self.suppliers_treeview.selection_remove(self.suppliers_treeview.selection()[0])
        
        self.name_entry.focus()

    def validate_inputs(self):
        supplier_name = self.supplier_name_var.get().strip()
        if not supplier_name:
            messagebox.showerror("Error de Validación", "El Nombre del Proveedor es obligatorio.")
            return False
        # Aquí podrías añadir más validaciones (ej. formato de correo, teléfono)
        return True

    def save_supplier(self):
        if not supplier_model:
            messagebox.showerror("Error Crítico", "El modelo de proveedores no está cargado.")
            return
        if not self.validate_inputs():
            return

        products_supplied = self.products_text.get("1.0", tk.END).strip()
        supplier_data_payload = {
            'nombre': self.supplier_name_var.get().strip(),
            'telefono': self.supplier_phone_var.get().strip() or None,
            'correo': self.supplier_email_var.get().strip() or None,
            'producto_suministra': products_supplied or None
        }
        
        saved_or_updated_id = None

        if self._selected_supplier_id_for_edit: # Modo Actualización
            id_for_operation = self._selected_supplier_id_for_edit
            result = supplier_model.update_supplier_details(id_for_operation, supplier_data_payload)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Proveedor '{id_for_operation}' actualizado exitosamente.")
                saved_or_updated_id = id_for_operation
            elif result == 0:
                messagebox.showinfo("Información", f"No se realizaron cambios en el proveedor '{id_for_operation}'.")
                saved_or_updated_id = id_for_operation # Aún queremos re-seleccionar
            else:
                messagebox.showerror("Error de Actualización", f"No se pudo actualizar el proveedor '{id_for_operation}'.")
                return 
        
        else: # Modo Creación
            created_id = supplier_model.create_supplier(supplier_data_payload)
            if created_id: 
                messagebox.showinfo("Éxito", f"Proveedor '{supplier_data_payload['nombre']}' creado con ID: {created_id}.")
                self._selected_supplier_id_for_edit = created_id # Guardar para re-selección
                saved_or_updated_id = created_id
            else:
                messagebox.showerror("Error de Creación", f"No se pudo crear el proveedor '{supplier_data_payload['nombre']}'.")
                return 
        
        self.load_suppliers_to_treeview()
        if saved_or_updated_id and self.suppliers_treeview.exists(saved_or_updated_id):
            self.suppliers_treeview.selection_set(saved_or_updated_id)
            self.suppliers_treeview.focus(saved_or_updated_id)
            self.on_supplier_select() # Cargar datos del proveedor guardado/actualizado
        else:
            self.clear_form_fields()


    def delete_selected_supplier(self):
        if not self._selected_supplier_id_for_edit:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor de la lista para eliminar.")
            return
        
        supplier_id_to_delete = self._selected_supplier_id_for_edit

        confirm = messagebox.askyesno("Confirmar Eliminación", 
                                      f"¿Está seguro de que desea eliminar al proveedor ID: {supplier_id_to_delete}?\n"
                                      "Esta acción es permanente y podría afectar a productos que lo referencien.")
        if confirm:
            result = supplier_model.delete_supplier_by_id(supplier_id_to_delete)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Proveedor '{supplier_id_to_delete}' eliminado exitosamente.")
            else:
                messagebox.showerror("Error de Eliminación", 
                                     f"No se pudo eliminar el proveedor '{supplier_id_to_delete}'.\n"
                                     "Puede que esté referenciado en productos u órdenes de compra, o no exista.")
            
            self.load_suppliers_to_treeview()
            self.clear_form_fields() # Limpiar el formulario y la selección

# --- Para probar esta vista de forma aislada ---
if __name__ == '__main__':
    if not supplier_model:
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico de Módulo", 
                             "No se pudo cargar 'supplier_model' para probar la vista de proveedores.")
        root_error.destroy()
    else:
        root = tk.Tk()
        root.title("Gestión de Proveedores (Prueba Aislada)")
        root.geometry("950x650") # Un poco más ancho para el treeview

        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes: 
            style.theme_use('clam')
        elif 'vista' in available_themes: # Para Windows
            style.theme_use('vista')
        elif 'aqua' in available_themes: # Para macOS
            style.theme_use('aqua')
        
        supplier_view_frame = SupplierView(root)
        supplier_view_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        root.mainloop()
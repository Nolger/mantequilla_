# app/views/supplier_view.py
import tkinter as tk
from tkinter import ttk, messagebox

# Ajusta la ruta de importación según tu estructura de proyecto.
# Asume que este archivo está en app/views/ y supplier_model.py está en app/models/
try:
    from ..models import supplier_model
except ImportError:
    # Fallback si la estructura es diferente o se ejecuta directamente
    try:
        from models import supplier_model
    except ImportError:
        print("Error CRÍTICO: No se pudo importar el módulo supplier_model.py en supplier_view.py.")
        print("Asegúrate de que el archivo exista en app/models/ y que las importaciones sean correctas.")
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
        self.supplier_id_var = tk.StringVar()
        self.supplier_name_var = tk.StringVar()
        self.supplier_phone_var = tk.StringVar()
        self.supplier_email_var = tk.StringVar()
        self.supplier_products_var = tk.StringVar() # Para el campo de texto de productos

        self._create_widgets()
        self.load_suppliers_to_treeview()
        self.clear_form_fields()

    def _create_widgets(self):
        # Frame para el formulario
        form_frame = ttk.LabelFrame(self, text="Datos del Proveedor", padding=(15, 10))
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        form_frame.columnconfigure(1, weight=1) # Hace que los Entry se expandan

        # ID Proveedor
        ttk.Label(form_frame, text="ID Proveedor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.id_entry = ttk.Entry(form_frame, textvariable=self.supplier_id_var, width=40)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Nombre
        ttk.Label(form_frame, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
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

        # Productos que Suministra (usaremos un Text widget para múltiples líneas)
        ttk.Label(form_frame, text="Productos Suministra:").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
        self.products_text = tk.Text(form_frame, height=4, width=30, wrap=tk.WORD) # tk.Text estándar
        self.products_text.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        # Scrollbar para el widget Text
        products_text_scrollbar = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=self.products_text.yview)
        products_text_scrollbar.grid(row=4, column=2, padx=(0,5), pady=5, sticky="ns")
        self.products_text.configure(yscrollcommand=products_text_scrollbar.set)


        # Frame para los botones de acción
        buttons_frame = ttk.Frame(self, padding=(0, 10))
        buttons_frame.grid(row=1, column=0, pady=10, sticky="ew")
        
        ttk.Button(buttons_frame, text="Nuevo", command=self.clear_form_fields, width=12).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="Guardar", command=self.save_supplier, width=12).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="Eliminar", command=self.delete_selected_supplier, width=12).pack(side=tk.LEFT, padx=10)

        # Treeview para mostrar la lista de proveedores
        tree_frame = ttk.LabelFrame(self, text="Listado de Proveedores", padding=(10,5))
        tree_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1) # Permite que el treeview se expanda verticalmente
        self.grid_columnconfigure(0, weight=1) # Permite que el treeview se expanda horizontalmente

        columns = ("id_proveedor", "nombre", "telefono", "correo", "producto_suministra")
        self.suppliers_treeview = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.suppliers_treeview.heading("id_proveedor", text="ID")
        self.suppliers_treeview.heading("nombre", text="Nombre")
        self.suppliers_treeview.heading("telefono", text="Teléfono")
        self.suppliers_treeview.heading("correo", text="Correo")
        self.suppliers_treeview.heading("producto_suministra", text="Productos")

        self.suppliers_treeview.column("id_proveedor", width=100, anchor="w")
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
        """ Carga o recarga los proveedores desde el modelo al Treeview. """
        if not supplier_model: return

        for item in self.suppliers_treeview.get_children():
            self.suppliers_treeview.delete(item)
        
        suppliers_list = supplier_model.get_all_suppliers_list()
        if suppliers_list:
            for sup in suppliers_list:
                self.suppliers_treeview.insert("", tk.END, iid=sup['id_proveedor'], values=(
                    sup.get("id_proveedor", ""),
                    sup.get("nombre", ""),
                    sup.get("telefono", ""),
                    sup.get("correo", ""),
                    sup.get("producto_suministra", "")
                ))
        elif suppliers_list is None: # Indica un error del modelo
             messagebox.showerror("Error de Carga", "No se pudieron cargar los proveedores desde la base de datos.")

    def on_supplier_select(self, event=None):
        """ Maneja la selección de un proveedor en el Treeview y carga sus datos en el formulario. """
        selected_items = self.suppliers_treeview.selection()
        if not selected_items:
            return 

        supplier_id = self.suppliers_treeview.selection()[0] # El iid es el id_proveedor
        
        # Obtener todos los datos del proveedor seleccionado usando el modelo
        supplier_data = supplier_model.get_supplier_by_id(supplier_id)

        if supplier_data:
            self.supplier_id_var.set(supplier_data.get("id_proveedor", ""))
            self.supplier_name_var.set(supplier_data.get("nombre", ""))
            self.supplier_phone_var.set(supplier_data.get("telefono", ""))
            self.supplier_email_var.set(supplier_data.get("correo", ""))
            
            self.products_text.delete("1.0", tk.END) # Limpiar campo de texto
            self.products_text.insert("1.0", supplier_data.get("producto_suministra", ""))
            
            self.id_entry.configure(state='readonly') # ID no editable al seleccionar
        else:
            messagebox.showwarning("Carga Fallida", f"No se encontraron datos para el proveedor ID: {supplier_id}")
            self.clear_form_fields()

    def clear_form_fields(self):
        """ Limpia los campos del formulario y los prepara para un nuevo proveedor. """
        self.supplier_id_var.set("")
        self.supplier_name_var.set("")
        self.supplier_phone_var.set("")
        self.supplier_email_var.set("")
        self.products_text.delete("1.0", tk.END)
        
        self.id_entry.configure(state='normal') # Habilitar ID para nuevo proveedor
        
        if self.suppliers_treeview.selection():
            self.suppliers_treeview.selection_remove(self.suppliers_treeview.selection()[0])
        
        self.id_entry.focus()

    def validate_inputs(self):
        """ Valida los campos de entrada antes de guardar. """
        supplier_id = self.supplier_id_var.get().strip()
        supplier_name = self.supplier_name_var.get().strip()

        if not supplier_id:
            messagebox.showerror("Error de Validación", "El ID de Proveedor es obligatorio.")
            return False
        if not supplier_name:
            messagebox.showerror("Error de Validación", "El Nombre del Proveedor es obligatorio.")
            return False
        # Se podrían añadir más validaciones (ej. formato de correo, teléfono)
        return True

    def save_supplier(self):
        """ Guarda el proveedor actual (nuevo o existente). """
        if not supplier_model:
            messagebox.showerror("Error Crítico", "El modelo de proveedores no está cargado.")
            return
        if not self.validate_inputs():
            return

        # Obtener el contenido del widget Text para 'producto_suministra'
        products_supplied = self.products_text.get("1.0", tk.END).strip()

        supplier_data_payload = {
            'id_proveedor': self.supplier_id_var.get().strip(),
            'nombre': self.supplier_name_var.get().strip(),
            'telefono': self.supplier_phone_var.get().strip() or None, # Guardar None si está vacío
            'correo': self.supplier_email_var.get().strip() or None,   # Guardar None si está vacío
            'producto_suministra': products_supplied or None         # Guardar None si está vacío
        }
        
        id_for_operation = supplier_data_payload['id_proveedor']
        is_update_mode = self.id_entry.cget('state') == 'readonly'

        if is_update_mode: 
            result = supplier_model.update_supplier_details(id_for_operation, supplier_data_payload)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Proveedor '{id_for_operation}' actualizado exitosamente.")
            elif result == 0:
                messagebox.showinfo("Información", f"No se realizaron cambios en el proveedor '{id_for_operation}'.")
            else:
                messagebox.showerror("Error de Actualización", f"No se pudo actualizar el proveedor '{id_for_operation}'.")
        else: # Modo Creación
            if supplier_model.get_supplier_by_id(id_for_operation):
                messagebox.showerror("Error de Creación", f"El ID de proveedor '{id_for_operation}' ya existe.")
                return
            
            result = supplier_model.create_supplier(supplier_data_payload)
            if result is not None: 
                messagebox.showinfo("Éxito", f"Proveedor '{id_for_operation}' creado exitosamente.")
            else:
                messagebox.showerror("Error de Creación", f"No se pudo crear el proveedor '{id_for_operation}'.")
        
        self.load_suppliers_to_treeview() 
        self.clear_form_fields()

    def delete_selected_supplier(self):
        """ Elimina el proveedor seleccionado en el Treeview. """
        if not supplier_model:
            messagebox.showerror("Error Crítico", "El modelo de proveedores no está cargado.")
            return

        selected_items = self.suppliers_treeview.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor para eliminar.")
            return
        
        supplier_id_to_delete = self.suppliers_treeview.selection()[0] # iid es id_proveedor

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
            self.clear_form_fields()

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
        root.geometry("900x650")

        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes: 
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        supplier_view_frame = SupplierView(root)
        supplier_view_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        root.mainloop()

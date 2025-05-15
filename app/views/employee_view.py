# app/views/employee_view.py
import tkinter as tk
from tkinter import ttk, messagebox

# Ajusta las rutas de importación según tu estructura de proyecto.
# Si este archivo está en app/views/ y employee_model.py está en app/models/
try:
    from ..models import employee_model
except ImportError:
    # Fallback si la estructura es diferente o se ejecuta directamente
    try:
        # Necesitarías que 'app' esté en PYTHONPATH o que los módulos estén estructurados de otra forma
        from models import employee_model # Si 'models' es un paquete accesible
    except ImportError:
        print("Error: No se pudo importar el módulo employee_model.py. Verifica tu estructura y PYTHONPATH.")
        employee_model = None

class EmployeeView(ttk.Frame):
    def __init__(self, parent_container, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container
        self.configure(padding=(20, 10))

        if not employee_model:
            # Muestra un error si el modelo no se pudo cargar
            error_label = ttk.Label(self, text="Error crítico: El modelo de empleados no está disponible.", foreground="red")
            error_label.pack(padx=10, pady=10)
            return

        # Variables para los campos del formulario
        self.employee_id_var = tk.StringVar()
        self.first_name_var = tk.StringVar()
        self.last_name_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.password_var = tk.StringVar() # Solo para creación
        self.status_var = tk.StringVar()

        # --- Creación de Widgets ---
        self._create_form_widgets()
        self._create_treeview_widget()
        self._create_action_buttons()

        self.load_employees_to_treeview()
        self.clear_form_fields() # Prepara para un nuevo empleado o selección

    def _create_form_widgets(self):
        # Frame para el formulario
        form_frame = ttk.LabelFrame(self, text="Datos del Empleado", padding=(15, 10))
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=2)
        form_frame.columnconfigure(1, weight=1) # Hace que los Entry se expandan

        # ID Empleado
        ttk.Label(form_frame, text="ID Empleado:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.id_entry = ttk.Entry(form_frame, textvariable=self.employee_id_var, width=40)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Nombre
        ttk.Label(form_frame, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.first_name_entry = ttk.Entry(form_frame, textvariable=self.first_name_var, width=40)
        self.first_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Apellido
        ttk.Label(form_frame, text="Apellido:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.last_name_entry = ttk.Entry(form_frame, textvariable=self.last_name_var, width=40)
        self.last_name_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Rol
        ttk.Label(form_frame, text="Rol:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        # Los roles deben coincidir con los permitidos en la BD y la lógica de negocio
        self.role_combobox = ttk.Combobox(form_frame, textvariable=self.role_var, 
                                          values=["administrador", "empleado", "mesero", "cocinero"], state="readonly")
        self.role_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Contraseña (solo para creación, se habilita/deshabilita)
        ttk.Label(form_frame, text="Contraseña:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.password_entry = ttk.Entry(form_frame, textvariable=self.password_var, show="*", width=40)
        self.password_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.password_entry.configure(state='disabled') # Deshabilitado por defecto

        # Estado
        ttk.Label(form_frame, text="Estado:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.status_combobox = ttk.Combobox(form_frame, textvariable=self.status_var, 
                                            values=["activo", "inactivo"], state="readonly")
        self.status_combobox.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

    def _create_treeview_widget(self):
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", columnspan=2)
        self.grid_rowconfigure(1, weight=1) # Permite que el treeview se expanda verticalmente
        self.grid_columnconfigure(0, weight=1) # Permite que el treeview se expanda horizontalmente

        columns = ("id_empleado", "nombre", "apellido", "rol", "estado")
        self.employees_treeview = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.employees_treeview.heading("id_empleado", text="ID Empleado")
        self.employees_treeview.heading("nombre", text="Nombre")
        self.employees_treeview.heading("apellido", text="Apellido")
        self.employees_treeview.heading("rol", text="Rol")
        self.employees_treeview.heading("estado", text="Estado")

        self.employees_treeview.column("id_empleado", width=100, anchor="w")
        self.employees_treeview.column("nombre", width=150, anchor="w")
        self.employees_treeview.column("apellido", width=150, anchor="w")
        self.employees_treeview.column("rol", width=100, anchor="w")
        self.employees_treeview.column("estado", width=80, anchor="center")

        # Scrollbar para el Treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.employees_treeview.yview)
        self.employees_treeview.configure(yscroll=scrollbar.set)
        
        self.employees_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Vincular evento de selección
        self.employees_treeview.bind("<<TreeviewSelect>>", self.on_employee_select)

    def _create_action_buttons(self):
        buttons_frame = ttk.Frame(self, padding=(0, 10))
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        buttons_frame.columnconfigure(0, weight=1) # Para centrar los botones si se usa grid
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)


        ttk.Button(buttons_frame, text="Nuevo", command=self.clear_form_fields, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="Guardar", command=self.save_employee, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="Eliminar", command=self.delete_selected_employee, width=15).pack(side=tk.LEFT, padx=10)


    def load_employees_to_treeview(self):
        """ Carga o recarga los empleados desde el modelo al Treeview. """
        if not employee_model: return

        # Limpiar Treeview existente
        for item in self.employees_treeview.get_children():
            self.employees_treeview.delete(item)
        
        employees_list = employee_model.get_all_employees_list()
        if employees_list:
            for emp in employees_list:
                # Asegúrate de que los nombres de las claves coincidan con lo que devuelve tu modelo
                self.employees_treeview.insert("", tk.END, values=(
                    emp.get("id_empleado", ""),
                    emp.get("nombre", ""),
                    emp.get("apellido", ""),
                    emp.get("rol", ""),
                    emp.get("estado", "")
                ))
        elif employees_list is None: # Indica un error del modelo
             messagebox.showerror("Error de Carga", "No se pudieron cargar los empleados desde la base de datos.")


    def on_employee_select(self, event=None):
        """ Maneja la selección de un empleado en el Treeview y carga sus datos en el formulario. """
        selected_items = self.employees_treeview.selection()
        if not selected_items:
            return # No hay nada seleccionado

        selected_item = selected_items[0] # Obtener el primer (y único) ítem seleccionado
        employee_values = self.employees_treeview.item(selected_item, "values")

        if employee_values:
            self.employee_id_var.set(employee_values[0])
            self.first_name_var.set(employee_values[1])
            self.last_name_var.set(employee_values[2])
            self.role_var.set(employee_values[3])
            self.status_var.set(employee_values[4])
            
            self.password_var.set("") # Limpiar contraseña al seleccionar
            self.password_entry.configure(state='disabled') # Deshabilitar campo de contraseña
            self.id_entry.configure(state='readonly') # ID no editable al seleccionar
            self.status_combobox.configure(state='readonly') # Estado se cambia con función específica si se desea
            self.role_combobox.configure(state='readonly') # Rol se cambia con función específica


    def clear_form_fields(self):
        """ Limpia los campos del formulario y los prepara para un nuevo empleado. """
        self.employee_id_var.set("")
        self.first_name_var.set("")
        self.last_name_var.set("")
        self.role_var.set("") 
        self.password_var.set("")
        self.status_var.set("activo") # Valor por defecto para nuevo empleado

        self.id_entry.configure(state='normal') # Habilitar ID para nuevo empleado
        self.password_entry.configure(state='normal') # Habilitar contraseña para nuevo empleado
        self.status_combobox.configure(state='readonly') # Estado por defecto 'activo'
        self.role_combobox.configure(state='readonly')

        # Deseleccionar cualquier fila en el treeview
        if self.employees_treeview.selection():
            self.employees_treeview.selection_remove(self.employees_treeview.selection()[0])
        
        self.id_entry.focus() # Poner foco en el ID

    def validate_inputs(self, is_new_employee=True):
        """ Valida los campos de entrada antes de guardar. """
        employee_id = self.employee_id_var.get().strip()
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()
        role = self.role_var.get()
        password = self.password_var.get() # No se valida su contenido, solo si es requerido

        if not employee_id:
            messagebox.showerror("Error de Validación", "El ID de Empleado es obligatorio.")
            return False
        if not first_name:
            messagebox.showerror("Error de Validación", "El Nombre es obligatorio.")
            return False
        if not last_name:
            messagebox.showerror("Error de Validación", "El Apellido es obligatorio.")
            return False
        if not role:
            messagebox.showerror("Error de Validación", "El Rol es obligatorio.")
            return False
        
        if is_new_employee and not password:
            messagebox.showerror("Error de Validación", "La Contraseña es obligatoria para nuevos empleados.")
            return False
        
        # Aquí podrías añadir más validaciones (longitud, formato, etc.)
        return True

    def save_employee(self):
        """ Guarda el empleado actual (nuevo o existente). """
        if not employee_model:
            messagebox.showerror("Error Crítico", "El modelo de empleados no está cargado.")
            return

        is_new = not self.employees_treeview.selection() # Es nuevo si no hay nada seleccionado
        
        if not self.validate_inputs(is_new_employee=is_new):
            return

        employee_data = {
            'id_empleado': self.employee_id_var.get().strip(),
            'nombre': self.first_name_var.get().strip(),
            'apellido': self.last_name_var.get().strip(),
            'rol': self.role_var.get(),
            'estado': self.status_var.get()
        }

        if is_new:
            # Para un nuevo empleado, necesitamos la contraseña plana
            employee_data['contrasena_plana'] = self.password_var.get()
            
            # Verificar si el ID ya existe antes de intentar crear
            existing_employee = employee_model.get_employee_by_id(employee_data['id_empleado'])
            if existing_employee:
                messagebox.showerror("Error de Creación", f"El ID de empleado '{employee_data['id_empleado']}' ya existe.")
                return

            result = employee_model.create_employee(employee_data)
            if result is not None: # El modelo devuelve el resultado de execute_query
                messagebox.showinfo("Éxito", f"Empleado '{employee_data['id_empleado']}' creado exitosamente.")
            else:
                messagebox.showerror("Error de Creación", f"No se pudo crear el empleado '{employee_data['id_empleado']}'.")
        else:
            # Actualizar empleado existente
            # El ID no se puede cambiar, se obtiene del campo que está readonly
            original_id = self.id_entry.get() # ID original no editable
            
            # Los datos a actualizar no incluyen el ID en el diccionario, solo los campos modificables
            update_payload = {
                'nombre': employee_data['nombre'],
                'apellido': employee_data['apellido'],
                'rol': employee_data['rol'],
                'estado': employee_data['estado']
            }
            result = employee_model.update_employee_details(original_id, update_payload)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Empleado '{original_id}' actualizado exitosamente.")
            elif result == 0:
                 messagebox.showinfo("Información", f"No se realizaron cambios en el empleado '{original_id}'.")
            else:
                messagebox.showerror("Error de Actualización", f"No se pudo actualizar el empleado '{original_id}'.")

        self.load_employees_to_treeview()
        self.clear_form_fields()


    def delete_selected_employee(self):
        """ Elimina el empleado seleccionado en el Treeview. """
        if not employee_model:
            messagebox.showerror("Error Crítico", "El modelo de empleados no está cargado.")
            return

        selected_items = self.employees_treeview.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un empleado para eliminar.")
            return
        
        employee_id_to_delete = self.employees_treeview.item(selected_items[0], "values")[0]

        confirm = messagebox.askyesno("Confirmar Eliminación", 
                                      f"¿Está seguro de que desea eliminar al empleado ID: {employee_id_to_delete}?\n¡Esta acción es permanente!")
        if confirm:
            result = employee_model.delete_employee_by_id_permanently(employee_id_to_delete)
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", f"Empleado '{employee_id_to_delete}' eliminado exitosamente.")
            else:
                messagebox.showerror("Error de Eliminación", f"No se pudo eliminar el empleado '{employee_id_to_delete}'.\nPuede que tenga registros asociados o no exista.")
            
            self.load_employees_to_treeview()
            self.clear_form_fields()

# --- Para probar esta vista de forma aislada ---
if __name__ == '__main__':
    # Necesitas una forma de configurar PYTHONPATH para que las importaciones relativas funcionen
    # o ejecutar este script desde un contexto donde 'app' sea reconocible.
    # Ejemplo: python -m app.views.employee_view (desde la raíz del proyecto)

    # Si employee_model es None, muestra un mensaje y sale.
    if not employee_model:
        root_error = tk.Tk()
        root_error.withdraw() # Ocultar la ventana principal vacía
        messagebox.showerror("Error Crítico de Módulo", 
                             "No se pudo cargar 'employee_model'.\n" +
                             "Asegúrate de que el archivo exista y las importaciones sean correctas.\n" +
                             "Ejecuta como: python -m app.views.employee_view")
        root_error.destroy()
        
    else:
        # Crear la ventana principal de la aplicación de prueba
        root = tk.Tk()
        root.title("Gestión de Empleados (Prueba Aislada)")
        root.geometry("800x600")

        # Estilo ttk
        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes: 
            style.theme_use('vista')
        
        # Crear e instanciar la vista de empleados
        # La vista EmployeeView es un ttk.Frame, así que se puede empaquetar en root.
        employee_view_frame = EmployeeView(root)
        employee_view_frame.pack(fill=tk.BOTH, expand=True)

        root.mainloop()

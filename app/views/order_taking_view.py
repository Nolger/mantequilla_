# app/views/order_taking_view.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Ajusta las rutas de importación según tu estructura de proyecto.
from ..models import table_model, menu_model, order_model
from ..auth import auth_logic # Para saber qué empleado está logueado (necesario)

class OrderTakingView(ttk.Frame):
    def __init__(self, parent_container, logged_in_employee_info, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container
        self.logged_in_employee_info = logged_in_employee_info # Ej: {'id_empleado': 'MESERO01', 'nombre': 'Juan'}
        
        self.current_selected_table_id = None
        self.current_active_order_id = None # ID de la comanda activa para la mesa seleccionada

        if not all([table_model, menu_model, order_model, auth_logic]):
            error_label = ttk.Label(self, text="Error crítico: Módulos esenciales no disponibles.", foreground="red")
            error_label.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
            return

        self._initialize_variables()
        self._create_layout()
        self._load_initial_data()

    def _initialize_variables(self):
        # Variables para la información de la comanda
        self.order_details_vars = [] # Para los items de la comanda
        self.order_subtotal_var = tk.DoubleVar(value=0.0)
        self.order_total_var = tk.DoubleVar(value=0.0) # Podría incluir impuestos/servicio en el futuro

        # Variables para añadir plato
        self.selected_dish_id_var = tk.StringVar()
        self.quantity_var = tk.IntVar(value=1)
        self.dish_observations_var = tk.StringVar()


    def _create_layout(self):
        # PanedWindow principal para dividir horizontalmente: Mesas | Menú y Comanda
        main_pw = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pw.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # --- Panel Izquierdo: Selección de Mesas y Acciones de Comanda ---
        left_frame_outer = ttk.Frame(main_pw, padding=5)
        main_pw.add(left_frame_outer, weight=1)

        tables_frame = ttk.LabelFrame(left_frame_outer, text="Mesas Disponibles", padding=10)
        tables_frame.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        self._create_tables_list_widget(tables_frame) # Lista de mesas

        order_actions_frame = ttk.LabelFrame(left_frame_outer, text="Acciones de Comanda", padding=10)
        order_actions_frame.pack(pady=5, padx=5, fill=tk.X)
        self._create_order_actions_buttons(order_actions_frame)


        # --- Panel Derecho: Menú de Platos y Detalles de la Comanda Actual ---
        right_frame_outer = ttk.Frame(main_pw, padding=5)
        main_pw.add(right_frame_outer, weight=3) # Dar más espacio al panel derecho

        # PanedWindow vertical para dividir: Menú Arriba | Comanda Abajo
        right_pw_vertical = ttk.PanedWindow(right_frame_outer, orient=tk.VERTICAL)
        right_pw_vertical.pack(expand=True, fill=tk.BOTH)

        menu_dishes_frame = ttk.LabelFrame(right_pw_vertical, text="Menú - Platos Disponibles", padding=10)
        right_pw_vertical.add(menu_dishes_frame, weight=1)
        self._create_menu_dishes_widget(menu_dishes_frame) # Lista de platos del menú

        current_order_frame = ttk.LabelFrame(right_pw_vertical, text="Comanda Actual", padding=10)
        right_pw_vertical.add(current_order_frame, weight=2) # Más espacio para los detalles de la comanda
        self._create_current_order_display_widget(current_order_frame) # Display de la comanda


    def _create_tables_list_widget(self, parent_frame):
        # Usaremos un Listbox simple por ahora para seleccionar mesas
        # Podríamos integrar el TableView con canvas aquí si fuera necesario más adelante
        ttk.Label(parent_frame, text="Seleccionar Mesa:").pack(anchor=tk.W)
        self.tables_listbox = tk.Listbox(parent_frame, exportselection=False, height=10)
        self.tables_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.tables_listbox.bind("<<ListboxSelect>>", self._on_table_selected_from_list)

        refresh_tables_btn = ttk.Button(parent_frame, text="Refrescar Mesas", command=self._load_tables_to_listbox)
        refresh_tables_btn.pack(pady=5)

    def _create_order_actions_buttons(self, parent_frame):
        self.open_order_btn = ttk.Button(parent_frame, text="Abrir/Ver Comanda", command=self._handle_open_or_view_order, state=tk.DISABLED)
        self.open_order_btn.pack(pady=3, fill=tk.X)
        
        self.send_to_kitchen_btn = ttk.Button(parent_frame, text="Enviar a Cocina", command=self._send_order_to_kitchen, state=tk.DISABLED)
        self.send_to_kitchen_btn.pack(pady=3, fill=tk.X)
        
        # Más botones (facturar, cancelar comanda) se añadirían aquí
        # self.bill_order_btn = ttk.Button(parent_frame, text="Facturar Comanda", command=self._bill_order, state=tk.DISABLED)
        # self.bill_order_btn.pack(pady=3, fill=tk.X)

    def _create_menu_dishes_widget(self, parent_frame):
        # Treeview para mostrar los platos del menú
        cols = ("nombre_plato", "categoria", "precio_venta")
        self.menu_treeview = ttk.Treeview(parent_frame, columns=cols, show="headings", selectmode="browse", height=8)
        self.menu_treeview.heading("nombre_plato", text="Plato")
        self.menu_treeview.heading("categoria", text="Categoría")
        self.menu_treeview.heading("precio_venta", text="Precio")

        self.menu_treeview.column("nombre_plato", width=200, anchor="w")
        self.menu_treeview.column("categoria", width=100, anchor="w")
        self.menu_treeview.column("precio_venta", width=70, anchor="e")
        self.menu_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        menu_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.menu_treeview.yview)
        self.menu_treeview.configure(yscrollcommand=menu_scrollbar.set)
        menu_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.menu_treeview.bind("<<TreeviewSelect>>", self._on_dish_selected_from_menu)

        # Controles para añadir el plato seleccionado a la comanda
        add_dish_frame = ttk.Frame(parent_frame)
        add_dish_frame.pack(fill=tk.X, pady=10)

        ttk.Label(add_dish_frame, text="Cant:").grid(row=0, column=0, padx=2)
        self.quantity_spinbox = ttk.Spinbox(add_dish_frame, from_=1, to=20, textvariable=self.quantity_var, width=5)
        self.quantity_spinbox.grid(row=0, column=1, padx=2)

        ttk.Label(add_dish_frame, text="Obs:").grid(row=0, column=2, padx=2)
        self.dish_obs_entry = ttk.Entry(add_dish_frame, textvariable=self.dish_observations_var, width=20)
        self.dish_obs_entry.grid(row=0, column=3, padx=2, sticky=tk.EW)
        add_dish_frame.columnconfigure(3, weight=1)


        self.add_dish_btn = ttk.Button(add_dish_frame, text="Añadir Plato", command=self._add_selected_dish_to_order, state=tk.DISABLED)
        self.add_dish_btn.grid(row=0, column=4, padx=5)


    def _create_current_order_display_widget(self, parent_frame):
        # Treeview para mostrar los ítems de la comanda actual
        order_cols = ("cantidad", "nombre_plato", "precio_unitario", "subtotal_item", "estado_plato", "observaciones")
        self.current_order_treeview = ttk.Treeview(parent_frame, columns=order_cols, show="headings", selectmode="browse", height=10)
        
        self.current_order_treeview.heading("cantidad", text="Cant.")
        self.current_order_treeview.heading("nombre_plato", text="Plato")
        self.current_order_treeview.heading("precio_unitario", text="P. Unit.")
        self.current_order_treeview.heading("subtotal_item", text="Subtotal")
        self.current_order_treeview.heading("estado_plato", text="Estado Plato")
        self.current_order_treeview.heading("observaciones", text="Obs.")

        self.current_order_treeview.column("cantidad", width=40, anchor="center")
        self.current_order_treeview.column("nombre_plato", width=180, anchor="w")
        self.current_order_treeview.column("precio_unitario", width=70, anchor="e")
        self.current_order_treeview.column("subtotal_item", width=80, anchor="e")
        self.current_order_treeview.column("estado_plato", width=100, anchor="w")
        self.current_order_treeview.column("observaciones", width=150, anchor="w")
        self.current_order_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        order_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.current_order_treeview.yview)
        self.current_order_treeview.configure(yscrollcommand=order_scrollbar.set)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Aquí podrías añadir botones para modificar/eliminar ítems de la comanda
        # y un display para el total de la comanda.
        total_frame = ttk.Frame(parent_frame)
        total_frame.pack(fill=tk.X, pady=5)
        ttk.Label(total_frame, text="Total Comanda: $").pack(side=tk.LEFT)
        ttk.Label(total_frame, textvariable=self.order_total_var, font=("Arial", 12, "bold")).pack(side=tk.LEFT)


    def _load_initial_data(self):
        self._load_tables_to_listbox()
        self._load_menu_to_treeview()

    def _load_tables_to_listbox(self):
        if not table_model: return
        self.tables_listbox.delete(0, tk.END)
        tables = table_model.get_all_tables_list()
        if tables:
            for table in tables:
                # Mostrar ID y estado para rápida visualización
                display_text = f"{table['id_mesa']} - Cap: {table['capacidad']} ({table['estado']})"
                self.tables_listbox.insert(tk.END, display_text)
                # Guardar el ID real como metadato si fuera necesario, o parsear desde el texto
        elif tables is None:
            messagebox.showerror("Error", "No se pudieron cargar las mesas.")
        self.current_selected_table_id = None
        self.current_active_order_id = None
        self.open_order_btn.config(state=tk.DISABLED)
        self._clear_current_order_display()


    def _load_menu_to_treeview(self):
        if not menu_model: return
        for item in self.menu_treeview.get_children():
            self.menu_treeview.delete(item)
        
        dishes = menu_model.get_active_dishes()
        if dishes:
            for dish in dishes:
                # Guardar el ID del plato como el 'iid' del item para fácil recuperación
                self.menu_treeview.insert("", tk.END, iid=dish['id_plato'], values=(
                    dish['nombre_plato'], 
                    dish['categoria'], 
                    f"{dish['precio_venta']:.2f}"
                ))
        elif dishes is None:
            messagebox.showerror("Error", "No se pudieron cargar los platos del menú.")
        self.selected_dish_id_var.set("")


    def _on_table_selected_from_list(self, event=None):
        selection_indices = self.tables_listbox.curselection()
        if not selection_indices:
            self.current_selected_table_id = None
            self.open_order_btn.config(state=tk.DISABLED)
            self._clear_current_order_display()
            return

        selected_text = self.tables_listbox.get(selection_indices[0])
        # Extraer el ID de la mesa del texto (ej. "M01 - ...")
        self.current_selected_table_id = selected_text.split(" - ")[0]
        
        print(f"Mesa seleccionada: {self.current_selected_table_id}") # Debug
        self.open_order_btn.config(state=tk.NORMAL)
        self._load_active_order_for_selected_table()


    def _load_active_order_for_selected_table(self):
        self._clear_current_order_display()
        self.current_active_order_id = None
        self.send_to_kitchen_btn.config(state=tk.DISABLED)
        self.add_dish_btn.config(state=tk.DISABLED)


        if not self.current_selected_table_id or not order_model:
            return

        active_orders = order_model.get_active_orders_for_table(self.current_selected_table_id)
        if active_orders: # Asumimos que solo hay una comanda activa por mesa como máximo
            self.current_active_order_id = active_orders[0]['id_comanda']
            print(f"Comanda activa encontrada: {self.current_active_order_id} para mesa {self.current_selected_table_id}")
            self._display_order_details(self.current_active_order_id)
            self.open_order_btn.config(text="Ver Comanda Actual")
            if active_orders[0]['estado_comanda'] == 'abierta':
                 self.send_to_kitchen_btn.config(state=tk.NORMAL)
                 self.add_dish_btn.config(state=tk.NORMAL) # Permitir añadir platos si está abierta

        else:
            print(f"No hay comanda activa para la mesa {self.current_selected_table_id}.")
            self.open_order_btn.config(text="Abrir Nueva Comanda")
            # No se habilita el botón de añadir plato hasta que se abra una comanda


    def _handle_open_or_view_order(self):
        if not self.current_selected_table_id or not order_model or not self.logged_in_employee_info:
            messagebox.showwarning("Acción Requerida", "Por favor, seleccione una mesa primero.")
            return

        if self.current_active_order_id: # Ya hay una comanda activa, solo mostrarla (ya debería estar cargada)
            messagebox.showinfo("Comanda Activa", f"Mostrando comanda activa {self.current_active_order_id} para la mesa {self.current_selected_table_id}.")
            self._display_order_details(self.current_active_order_id) # Asegurar que esté actualizada
            self.add_dish_btn.config(state=tk.NORMAL) # Habilitar añadir platos
        else: # Abrir nueva comanda
            num_people = simpledialog.askinteger("Número de Personas", "Ingrese el número de personas para la mesa:",
                                                 parent=self, minvalue=1, initialvalue=1)
            if num_people is None: # Usuario canceló
                return

            employee_id = self.logged_in_employee_info.get('id_empleado')
            if not employee_id:
                messagebox.showerror("Error de Autenticación", "No se pudo identificar al empleado logueado.")
                return

            new_order_id = order_model.create_new_order(self.current_selected_table_id, employee_id, num_people=num_people)
            if new_order_id:
                self.current_active_order_id = new_order_id
                messagebox.showinfo("Éxito", f"Nueva comanda '{new_order_id}' abierta para la mesa '{self.current_selected_table_id}'.")
                self._load_tables_to_listbox() # Refrescar estado de la mesa en la lista
                self._display_order_details(new_order_id)
                self.open_order_btn.config(text="Ver Comanda Actual")
                self.send_to_kitchen_btn.config(state=tk.NORMAL)
                self.add_dish_btn.config(state=tk.NORMAL)
            else:
                messagebox.showerror("Error", f"No se pudo abrir una nueva comanda para la mesa '{self.current_selected_table_id}'.")


    def _on_dish_selected_from_menu(self, event=None):
        selected_items = self.menu_treeview.selection()
        if not selected_items:
            self.selected_dish_id_var.set("")
            return
        self.selected_dish_id_var.set(selected_items[0]) # El iid es el dish_id
        print(f"Plato seleccionado del menú: {self.selected_dish_id_var.get()}") # Debug


    def _add_selected_dish_to_order(self):
        if not self.current_active_order_id:
            messagebox.showwarning("Acción Requerida", "No hay una comanda activa seleccionada o abierta.")
            return
        
        dish_id = self.selected_dish_id_var.get()
        if not dish_id:
            messagebox.showwarning("Acción Requerida", "Por favor, seleccione un plato del menú.")
            return
        
        try:
            quantity = self.quantity_var.get()
            if quantity <= 0:
                messagebox.showerror("Error de Cantidad", "La cantidad debe ser mayor que cero.")
                return
        except tk.TclError:
            messagebox.showerror("Error de Cantidad", "La cantidad ingresada no es válida.")
            return
            
        observations = self.dish_observations_var.get().strip()

        if order_model:
            detail_id = order_model.add_dish_to_order(self.current_active_order_id, dish_id, quantity, observations)
            if detail_id:
                messagebox.showinfo("Éxito", "Plato añadido a la comanda.")
                self._display_order_details(self.current_active_order_id) # Recargar detalles de la comanda
                # Limpiar campos de añadir plato
                self.quantity_var.set(1)
                self.dish_observations_var.set("")
                if self.menu_treeview.selection(): # Deseleccionar del menú
                    self.menu_treeview.selection_remove(self.menu_treeview.selection()[0])
                self.selected_dish_id_var.set("")
            else:
                messagebox.showerror("Error", "No se pudo añadir el plato a la comanda.")

    def _clear_current_order_display(self):
        for item in self.current_order_treeview.get_children():
            self.current_order_treeview.delete(item)
        self.order_total_var.set(0.0)
        # Podrías limpiar también etiquetas de ID de comanda, etc.

    def _display_order_details(self, order_id_to_display):
        self._clear_current_order_display()
        if not order_model or not order_id_to_display:
            return

        order_data = order_model.get_order_by_id(order_id_to_display)
        if order_data and order_data.get('detalles') is not None:
            current_total = 0.0
            for detail in order_data['detalles']:
                self.current_order_treeview.insert("", tk.END, iid=detail['id_detalle_comanda'], values=(
                    detail['cantidad'],
                    detail['nombre_plato'],
                    f"{detail['precio_unitario_momento']:.2f}",
                    f"{detail['subtotal_detalle']:.2f}",
                    detail['estado_plato'],
                    detail['observaciones_plato']
                ))
                current_total += detail['subtotal_detalle']
            self.order_total_var.set(round(current_total, 2))
            
            # Actualizar estado de botones según estado de la comanda
            order_status = order_data.get('estado_comanda', 'abierta')
            if order_status == 'abierta':
                self.send_to_kitchen_btn.config(state=tk.NORMAL)
                self.add_dish_btn.config(state=tk.NORMAL)
            else: # 'en preparacion', 'servida', etc.
                self.send_to_kitchen_btn.config(state=tk.DISABLED)
                self.add_dish_btn.config(state=tk.DISABLED) # No se pueden añadir más platos
        elif order_data is None:
            messagebox.showerror("Error", f"No se pudo cargar la comanda con ID {order_id_to_display}.")


    def _send_order_to_kitchen(self):
        if not self.current_active_order_id or not order_model:
            messagebox.showwarning("Acción Requerida", "No hay una comanda activa para enviar.")
            return

        # Verificar si la comanda tiene ítems
        order_data = order_model.get_order_by_id(self.current_active_order_id)
        if not order_data or not order_data.get('detalles'):
            messagebox.showwarning("Comanda Vacía", "No se puede enviar una comanda vacía a cocina.")
            return

        confirm = messagebox.askyesno("Confirmar Envío", 
                                      f"¿Está seguro de que desea enviar la comanda {self.current_active_order_id} a cocina?\n"
                                      "Una vez enviada, no podrá añadir más platos directamente aquí.")
        if confirm:
            result = order_model.update_order_status(self.current_active_order_id, 'en preparacion')
            if result:
                messagebox.showinfo("Éxito", f"Comanda {self.current_active_order_id} enviada a cocina.")
                self._display_order_details(self.current_active_order_id) # Recargar para ver estado y deshabilitar botones
            else:
                messagebox.showerror("Error", f"No se pudo enviar la comanda {self.current_active_order_id} a cocina.")


# --- Para probar esta vista de forma aislada ---
def main_test(employee_info_for_test=None):
    if not all([table_model, menu_model, order_model, auth_logic]):
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico de Módulo", 
                             "No se pudieron cargar módulos esenciales para probar la vista de toma de comandas.")
        root_error.destroy()
        return

    if employee_info_for_test is None:
        # Simular un empleado logueado para las pruebas
        # En la app real, esto vendría del flujo de login
        employee_info_for_test = {
            "id_empleado": "MESERO01", # Asegúrate que este empleado exista o créalo
            "nombre": "Mesero",
            "apellido": "Prueba",
            "rol": "mesero"
        }
        # Podrías verificar si MESERO01 existe y si no, intentar crearlo con auth_logic
        # para que las pruebas sean más autocontenidas.

    root = tk.Tk()
    root.title("Toma de Comandas (Prueba Aislada)")
    root.geometry("1100x750")

    style = ttk.Style(root)
    available_themes = style.theme_names()
    if 'clam' in available_themes: style.theme_use('clam')
    
    order_taking_view_frame = OrderTakingView(root, employee_info_for_test)
    order_taking_view_frame.pack(fill=tk.BOTH, expand=True)

    root.mainloop()

if __name__ == '__main__':
    # Para ejecutar esta prueba: python -m app.views.order_taking_view
    # (desde la raíz de tu proyecto)
    print("Ejecutando prueba aislada de OrderTakingView...")
    main_test()

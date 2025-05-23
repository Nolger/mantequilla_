import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import traceback

try:
    from app.models import table_model, menu_model, order_model, stock_model
    from app.auth import auth_logic
except ImportError:
    print(
        "Advertencia: Falló la importación principal (app...) en OrderTakingView. Intentando fallback relativo..."
    )
    try:
        from ..models import table_model, menu_model, order_model, stock_model
        from ..auth import auth_logic
    except ImportError:
        print(
            "Advertencia: Falló la importación relativa (..) en OrderTakingView. Intentando importación directa..."
        )
        try:
            from models import table_model, menu_model, order_model, stock_model
            from auth import auth_logic
        except ImportError as e:
            print(
                f"Error CRÍTICO: No se pudieron importar módulos esenciales en OrderTakingView: {e}"
            )
            table_model = menu_model = order_model = stock_model = auth_logic = None


class OrderTakingView(ttk.Frame):
    def __init__(self, parent_container, logged_in_employee_info, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        self.parent_container = parent_container
        self.logged_in_employee_info = logged_in_employee_info

        self.current_selected_table_id = None
        self.current_active_order_id = None
        self.current_order_status = None
        self.selected_order_detail_id_for_status = None

        if not all(
            [table_model, menu_model, order_model, auth_logic, stock_model]
        ):
            error_label = ttk.Label(
                self,
                text="Error crítico: Módulos esenciales no disponibles.",
                foreground="red",
            )
            error_label.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
            return

        self._initialize_variables()
        self._create_layout()
        self._load_initial_data()
        self._update_ui_states()

    def _initialize_variables(self):
        self.order_total_var = tk.DoubleVar(value=0.0)
        self.selected_dish_id_var = tk.StringVar()
        self.quantity_var = tk.IntVar(value=1)
        self.dish_observations_var = tk.StringVar()

    def _create_layout(self):
        main_pw = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pw.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        left_frame_outer = ttk.Frame(main_pw, padding=5)
        main_pw.add(left_frame_outer, weight=1)
        tables_frame = ttk.LabelFrame(
            left_frame_outer, text="Mesas", padding=10
        )
        tables_frame.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        self._create_tables_list_widget(tables_frame)
        order_actions_frame = ttk.LabelFrame(
            left_frame_outer, text="Acciones de Comanda Principal", padding=10
        )
        order_actions_frame.pack(pady=10, padx=5, fill=tk.X)
        self._create_order_main_actions_buttons(order_actions_frame)

        right_frame_outer = ttk.Frame(main_pw, padding=5)
        main_pw.add(right_frame_outer, weight=3)
        right_pw_vertical = ttk.PanedWindow(
            right_frame_outer, orient=tk.VERTICAL
        )
        right_pw_vertical.pack(expand=True, fill=tk.BOTH)
        menu_dishes_frame = ttk.LabelFrame(
            right_pw_vertical, text="Menú - Añadir Plato", padding=10
        )
        right_pw_vertical.add(menu_dishes_frame, weight=1)
        self._create_menu_dishes_widget(menu_dishes_frame)
        current_order_frame = ttk.LabelFrame(
            right_pw_vertical, text="Detalle de Comanda Activa", padding=10
        )
        right_pw_vertical.add(current_order_frame, weight=2)
        self._create_current_order_display_widget(current_order_frame)

    def _create_tables_list_widget(self, parent_frame):
        ttk.Label(parent_frame, text="Seleccionar Mesa:").pack(anchor=tk.W)
        self.tables_listbox = tk.Listbox(
            parent_frame,
            exportselection=False,
            height=15,
            font=("Segoe UI", 10),
            relief=tk.SUNKEN,
            borderwidth=1,
        )
        self.tables_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        self.tables_listbox.bind(
            "<<ListboxSelect>>", self._on_table_selected_from_list
        )
        refresh_tables_btn = ttk.Button(
            parent_frame,
            text="Refrescar Mesas",
            command=self._load_tables_to_listbox,
        )
        refresh_tables_btn.pack(pady=(5, 0), fill=tk.X)

    def _create_order_main_actions_buttons(self, parent_frame):
        self.manage_order_btn = ttk.Button(
            parent_frame,
            text="Seleccione una Mesa",
            command=self._handle_manage_order_button,
            state=tk.DISABLED,
        )
        self.manage_order_btn.pack(pady=3, fill=tk.X, ipady=5)

        self.send_to_kitchen_btn = ttk.Button(
            parent_frame, text="Enviar a Cocina", command=self._send_order_to_kitchen
        )
        self.send_to_kitchen_btn.pack(pady=3, fill=tk.X)

        self.request_bill_btn = ttk.Button(
            parent_frame, text="Solicitar Cuenta", command=self._request_bill
        )
        self.request_bill_btn.pack(pady=3, fill=tk.X)

        self.finalize_order_btn = ttk.Button(
            parent_frame,
            text="Finalizar/Liberar Mesa",
            command=self._finalize_order_and_free_table,
        )
        self.finalize_order_btn.pack(pady=(10, 3), fill=tk.X)

    def _create_menu_dishes_widget(self, parent_frame):
        cols = ("nombre_plato", "categoria", "precio_venta")
        self.menu_treeview = ttk.Treeview(
            parent_frame, columns=cols, show="headings", selectmode="browse", height=7
        )
        self.menu_treeview.heading("nombre_plato", text="Plato")
        self.menu_treeview.heading("categoria", text="Categoría")
        self.menu_treeview.heading("precio_venta", text="Precio")
        self.menu_treeview.column("nombre_plato", width=220, anchor="w")
        self.menu_treeview.column("categoria", width=100, anchor="w")
        self.menu_treeview.column("precio_venta", width=70, anchor="e")

        menu_scrollbar = ttk.Scrollbar(
            parent_frame, orient=tk.VERTICAL, command=self.menu_treeview.yview
        )
        self.menu_treeview.configure(yscrollcommand=menu_scrollbar.set)
        self.menu_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        menu_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.menu_treeview.bind("<<TreeviewSelect>>", self._on_dish_selected_from_menu)

        add_dish_controls_frame = ttk.Frame(parent_frame)
        add_dish_controls_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(add_dish_controls_frame, text="Cant:").grid(
            row=0, column=0, padx=2
        )
        self.quantity_spinbox = ttk.Spinbox(
            add_dish_controls_frame,
            from_=1,
            to=20,
            textvariable=self.quantity_var,
            width=4,
        )
        self.quantity_spinbox.grid(row=0, column=1, padx=2)
        ttk.Label(add_dish_controls_frame, text="Obs:").grid(
            row=0, column=2, padx=2
        )
        self.dish_obs_entry = ttk.Entry(
            add_dish_controls_frame, textvariable=self.dish_observations_var, width=25
        )
        self.dish_obs_entry.grid(row=0, column=3, padx=2, sticky=tk.EW)
        add_dish_controls_frame.columnconfigure(3, weight=1)
        self.add_dish_btn = ttk.Button(
            add_dish_controls_frame,
            text="Añadir Plato",
            command=self._add_selected_dish_to_order,
        )
        self.add_dish_btn.grid(row=0, column=4, padx=(5, 0))

    def _create_current_order_display_widget(self, parent_frame):
        order_cols = (
            "id_detalle",
            "cantidad",
            "nombre_plato",
            "precio_u",
            "subtotal",
            "estado_plato",
            "obs_plato",
        )
        self.current_order_treeview = ttk.Treeview(
            parent_frame, columns=order_cols, show="headings", selectmode="browse", height=10
        )
        self.current_order_treeview.heading("id_detalle", text="ID Det.")
        self.current_order_treeview.heading("cantidad", text="Cant.")
        self.current_order_treeview.heading("nombre_plato", text="Plato")
        self.current_order_treeview.heading("precio_u", text="P.Unit")
        self.current_order_treeview.heading("subtotal", text="Subtotal")
        self.current_order_treeview.heading("estado_plato", text="Estado")
        self.current_order_treeview.heading("obs_plato", text="Obs.")

        self.current_order_treeview.column("id_detalle", width=60, stretch=tk.NO, anchor="center")
        self.current_order_treeview.column("cantidad", width=40, anchor="center")
        self.current_order_treeview.column("nombre_plato", width=180)
        self.current_order_treeview.column("precio_u", width=70, anchor="e")
        self.current_order_treeview.column("subtotal", width=80, anchor="e")
        self.current_order_treeview.column("estado_plato", width=100)
        self.current_order_treeview.column("obs_plato", width=150)

        order_scrollbar = ttk.Scrollbar(
            parent_frame, orient=tk.VERTICAL, command=self.current_order_treeview.yview
        )
        self.current_order_treeview.configure(yscrollcommand=order_scrollbar.set)
        self.current_order_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.current_order_treeview.bind(
            "<<TreeviewSelect>>", self._on_order_item_selected
        )

        item_actions_frame = ttk.Frame(parent_frame)
        item_actions_frame.pack(fill=tk.X, pady=5)
        self.mark_delivered_btn = ttk.Button(
            item_actions_frame,
            text="Marcar Plato Entregado",
            command=self._mark_selected_item_as_delivered,
        )
        self.mark_delivered_btn.pack(side=tk.LEFT, padx=5)

        total_frame = ttk.Frame(parent_frame)
        total_frame.pack(fill=tk.X, pady=(5, 0), anchor=tk.E)
        ttk.Label(
            total_frame,
            textvariable=self.order_total_var,
            font=("Segoe UI", 12, "bold"),
        ).pack(side=tk.RIGHT, padx=5)
        ttk.Label(total_frame, text="Total Comanda: $", font=("Segoe UI", 10, "bold")).pack(
            side=tk.RIGHT
        )

    def _load_initial_data(self):
        self._load_tables_to_listbox()
        self._load_menu_to_treeview()

    def _load_tables_to_listbox(self):
        if not table_model: return
        self.tables_listbox.delete(0, tk.END)
        tables = table_model.get_all_tables_list()
        if tables:
            for table in tables:
                display_text = f"{table['id_mesa']} - Cap: {table['capacidad']} ({table['estado']})"
                self.tables_listbox.insert(tk.END, display_text)
        elif tables is None:
            messagebox.showerror("Error", "No se pudieron cargar las mesas.")
        self._clear_selection_and_order_details()

    def _load_menu_to_treeview(self):
        if not menu_model: return
        for item in self.menu_treeview.get_children():
            self.menu_treeview.delete(item)
        dishes = menu_model.get_active_dishes()
        if dishes:
            for dish in dishes:
                self.menu_treeview.insert("", tk.END, iid=dish['id_plato'], values=(
                    dish['nombre_plato'], dish['categoria'], f"{dish['precio_venta']:.2f}"
                ))
        elif dishes is None:
            messagebox.showerror("Error", "No se pudieron cargar los platos del menú.")
        self.selected_dish_id_var.set("")

    def _clear_selection_and_order_details(self):
        self.current_selected_table_id = None
        self.current_active_order_id = None
        self.current_order_status = None
        self.selected_order_detail_id_for_status = None
        if self.tables_listbox.curselection():
            self.tables_listbox.selection_clear(0, tk.END)
        self._clear_current_order_display()
        self._update_ui_states()

    def _clear_current_order_display(self):
        for item in self.current_order_treeview.get_children():
            self.current_order_treeview.delete(item)
        self.order_total_var.set(0.0)
        self.selected_order_detail_id_for_status = None

    def _update_ui_states(self):
        table_selected = bool(self.current_selected_table_id)
        order_active = bool(self.current_active_order_id)
        order_is_open = order_active and self.current_order_status == 'abierta'
        order_is_preparing_or_ready = order_active and self.current_order_status in ['en preparacion', 'lista para servir']
        order_is_served = order_active and self.current_order_status == 'servida'

        self.manage_order_btn.config(state=tk.NORMAL if table_selected else tk.DISABLED)
        if order_active:
            self.manage_order_btn.config(text=f"Ver/Mod. Comanda: {self.current_active_order_id[:12]}...")
        elif table_selected:
            self.manage_order_btn.config(text="Abrir Nueva Comanda")
        else:
            self.manage_order_btn.config(text="Seleccione una Mesa")

        self.send_to_kitchen_btn.config(state=tk.NORMAL if order_is_open and self.current_order_treeview.get_children() else tk.DISABLED)
        self.request_bill_btn.config(state=tk.NORMAL if order_is_preparing_or_ready or order_is_served else tk.DISABLED)
        self.finalize_order_btn.config(state=tk.NORMAL if order_is_served else tk.DISABLED)

        self.add_dish_btn.config(state=tk.NORMAL if order_is_open else tk.DISABLED)
        self.quantity_spinbox.config(state=tk.NORMAL if order_is_open else tk.DISABLED)
        self.dish_obs_entry.config(state=tk.NORMAL if order_is_open else tk.DISABLED)

        can_mark_delivered = False
        if self.selected_order_detail_id_for_status:
            try:
                item_data = self.current_order_treeview.item(self.selected_order_detail_id_for_status)
                if item_data and item_data.get('values') and len(item_data['values']) > 5:
                    current_item_status = item_data['values'][5]
                    if current_item_status == 'listo':
                        can_mark_delivered = True
            except tk.TclError: pass
            except IndexError: pass
        self.mark_delivered_btn.config(state=tk.NORMAL if can_mark_delivered else tk.DISABLED)

    def _on_table_selected_from_list(self, event=None):
        selection_indices = self.tables_listbox.curselection()
        if not selection_indices:
            self._clear_selection_and_order_details()
            return

        selected_text = self.tables_listbox.get(selection_indices[0])
        self.current_selected_table_id = selected_text.split(" - ")[0]
        print(f"INFO: Mesa seleccionada: {self.current_selected_table_id}")
        self._load_active_order_for_selected_table()

    def _load_active_order_for_selected_table(self):
        self._clear_current_order_display()
        self.current_active_order_id = None
        self.current_order_status = None

        if not self.current_selected_table_id or not order_model:
            self._update_ui_states()
            return

        active_orders = order_model.get_active_orders_for_table(self.current_selected_table_id)
        if active_orders:
            self.current_active_order_id = active_orders[0]['id_comanda']
            self.current_order_status = active_orders[0]['estado_comanda']
            print(f"INFO: Comanda activa: {self.current_active_order_id} (Estado: {self.current_order_status}) para mesa {self.current_selected_table_id}")
            self._display_order_details(self.current_active_order_id)
        else:
            print(f"INFO: No hay comanda activa para la mesa {self.current_selected_table_id}.")
        self._update_ui_states()

    def _handle_manage_order_button(self):
        if not self.current_selected_table_id:
            messagebox.showwarning("Acción Requerida", "Por favor, seleccione una mesa primero.")
            return
        if self.current_active_order_id:
            print(f"INFO: Accediendo a comanda activa {self.current_active_order_id}.")
            self._display_order_details(self.current_active_order_id)
        else:
            self._open_new_order_for_selected_table()
        self._update_ui_states()

    def _open_new_order_for_selected_table(self):
        if not self.current_selected_table_id or not self.logged_in_employee_info: return

        num_people = simpledialog.askinteger("Número de Personas",
                                             f"Ingrese el número de personas para la mesa {self.current_selected_table_id}:",
                                             parent=self, minvalue=1, initialvalue=1)
        if num_people is None: return

        employee_id = self.logged_in_employee_info.get('id_empleado')
        if not employee_id:
            messagebox.showerror("Error de Autenticación", "No se pudo identificar al empleado logueado.")
            return

        new_order_id = order_model.create_new_order(self.current_selected_table_id, employee_id, num_people=num_people)
        if new_order_id:
            self.current_active_order_id = new_order_id
            self.current_order_status = 'abierta'
            messagebox.showinfo("Éxito", f"Nueva comanda '{new_order_id}' abierta para la mesa '{self.current_selected_table_id}'.")
            self._load_tables_to_listbox()
            self._display_order_details(new_order_id)
        else:
            messagebox.showerror("Error", f"No se pudo abrir una nueva comanda para la mesa '{self.current_selected_table_id}'. Verifique el estado de la mesa.")
        self._update_ui_states()

    def _on_dish_selected_from_menu(self, event=None):
        selected_items = self.menu_treeview.selection()
        if not selected_items:
            self.selected_dish_id_var.set("")
            return
        self.selected_dish_id_var.set(selected_items[0])
        self.quantity_var.set(1)
        self.dish_observations_var.set("")
        self.quantity_spinbox.focus()

    def _add_selected_dish_to_order(self):
        if not self.current_active_order_id or self.current_order_status != 'abierta':
            messagebox.showwarning("Acción Requerida", "Debe tener una comanda 'abierta' activa para añadir platos.")
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

        if stock_model:
            print(f"DEBUG: Verificando stock para dish_id: {dish_id}, quantity: {quantity}")
            try:
                stock_check_result = stock_model.check_stock_for_dish(dish_id, quantity)
                print(f"DEBUG: stock_check_result: {stock_check_result}")

                if stock_check_result is None:
                    messagebox.showerror("Error de Sistema", "No se pudo verificar el stock del plato (resultado nulo). Intente de nuevo o contacte al administrador.")
                    return

                if not stock_check_result['can_prepare']:
                    missing_items_str = "No hay suficiente stock para preparar este plato:\n"
                    for item in stock_check_result['missing_items']:
                        missing_items_str += (
                            f"- {item.get('nombre_ingrediente', 'Desconocido')}: Necesita {item.get('needed', 0):.3f}, "
                            f"Disponible: {item.get('available', 0):.3f} {item.get('unit', '')}\n"
                        )
                    messagebox.showwarning("Stock Insuficiente", missing_items_str)
                    return
            except Exception as e_stock_check:
                print(f"ERROR EXCEPCIÓN durante la verificación de stock: {e_stock_check}")
                traceback.print_exc()
                messagebox.showerror("Error de Verificación de Stock", f"Ocurrió un error al verificar el stock: {e_stock_check}")
                return
        else:
            messagebox.showwarning("Advertencia del Sistema", "No se pudo verificar el stock (módulo de stock no disponible). El plato se añadirá sin confirmación de stock.")

        if order_model:
            detail_id = order_model.add_dish_to_order(self.current_active_order_id, dish_id, quantity, observations)
            if detail_id:
                self._display_order_details(self.current_active_order_id)
                self.quantity_var.set(1)
                self.dish_observations_var.set("")
                if self.menu_treeview.selection():
                    self.menu_treeview.selection_remove(self.menu_treeview.selection()[0])
                self.selected_dish_id_var.set("")
            else:
                messagebox.showerror("Error", "No se pudo añadir el plato a la comanda (después de la verificación de stock).")
        self._update_ui_states()

    def _display_order_details(self, order_id_to_display):
        self._clear_current_order_display()
        if not order_model or not order_id_to_display:
            self._update_ui_states()
            return

        order_data = order_model.get_order_by_id(order_id_to_display)
        if order_data:
            self.current_order_status = order_data.get('estado_comanda', 'desconocido')
            current_total = 0.0
            if order_data.get('detalles'):
                for detail in order_data['detalles']:
                    self.current_order_treeview.insert("", tk.END, iid=detail['id_detalle_comanda'], values=(
                        detail['id_detalle_comanda'],
                        detail['cantidad'],
                        detail['nombre_plato'],
                        f"{float(detail['precio_unitario_momento']):.2f}",
                        f"{float(detail['subtotal_detalle']):.2f}",
                        detail['estado_plato'],
                        detail.get('observaciones_plato', '')
                    ))
                    current_total += float(detail['subtotal_detalle'])
            self.order_total_var.set(round(current_total, 2))
        else:
            messagebox.showerror("Error", f"No se pudo cargar la comanda con ID {order_id_to_display}.")
            self.current_active_order_id = None
            self.current_order_status = None
        self._update_ui_states()

    def _on_order_item_selected(self, event=None):
        selected = self.current_order_treeview.selection()
        if selected:
            self.selected_order_detail_id_for_status = selected[0]
        else:
            self.selected_order_detail_id_for_status = None
        self._update_ui_states()

    def _mark_selected_item_as_delivered(self):
        if not self.selected_order_detail_id_for_status or not order_model:
            messagebox.showwarning("Sin Selección", "Seleccione un plato de la comanda que esté 'listo' para marcar como entregado.")
            return

        item_data = self.current_order_treeview.item(self.selected_order_detail_id_for_status)
        if not item_data or not item_data.get('values') or len(item_data['values']) <= 5 or item_data['values'][5] != 'listo':
             messagebox.showwarning("Estado Incorrecto", "Solo los platos en estado 'listo' pueden marcarse como entregados.")
             return

        if messagebox.askyesno("Confirmar Entrega", "Marcar el plato seleccionado como 'ENTREGADO' al cliente?"):
            result = order_model.update_order_item_status(self.selected_order_detail_id_for_status, 'entregado')
            if result is not None and result > 0:
                messagebox.showinfo("Éxito", "Plato marcado como 'entregado'.")
                if self.current_active_order_id:
                    self._display_order_details(self.current_active_order_id)
            else:
                messagebox.showerror("Error", "No se pudo actualizar el estado del plato a 'entregado'.")
        self._update_ui_states()

    def _request_bill(self):
        if not self.current_active_order_id or not order_model:
            messagebox.showwarning("Sin Comanda", "No hay una comanda activa para solicitar la cuenta.")
            return

        if self.current_order_status not in ['en preparacion', 'lista para servir', 'servida']:
            messagebox.showwarning("Estado Inválido", f"No se puede solicitar cuenta para una comanda en estado '{self.current_order_status}'.")
            return

        if messagebox.askyesno("Solicitar Cuenta", f"Marcar la comanda {self.current_active_order_id} como 'servida' (lista para facturar)?"):
            result = order_model.update_order_status(self.current_active_order_id, 'servida')
            if result is not None and result > 0:
                messagebox.showinfo("Cuenta Solicitada", f"Comanda {self.current_active_order_id} marcada como 'servida'.")
                self._display_order_details(self.current_active_order_id)
            else:
                messagebox.showerror("Error", "No se pudo actualizar el estado de la comanda.")
        self._update_ui_states()

    def _send_order_to_kitchen(self):
        if not self.current_active_order_id or self.current_order_status != 'abierta':
            messagebox.showwarning("Acción Requerida", "Debe tener una comanda 'abierta' activa para enviar a cocina.")
            return
        if not self.current_order_treeview.get_children():
            messagebox.showwarning("Comanda Vacía", "No se puede enviar una comanda vacía a cocina.")
            return

        if messagebox.askyesno("Confirmar Envío", f"Enviar la comanda {self.current_active_order_id} a cocina?"):
            all_items_processed_successfully = True
            order_data = order_model.get_order_by_id(self.current_active_order_id)

            if order_data and order_data.get('detalles'):
                id_empleado_resp = self.logged_in_employee_info.get('id_empleado')
                for detail in order_data['detalles']:
                    if detail['estado_plato'] == 'pendiente':
                        res_item = order_model.update_order_item_status(detail['id_detalle_comanda'], 'en preparacion', id_employee_responsible=id_empleado_resp)
                        if not res_item:
                            all_items_processed_successfully = False
                            messagebox.showerror("Error de Stock/Proceso", f"No se pudo procesar el plato '{detail['nombre_plato']}' para cocina (posible falta de stock o error). La comanda no se envió completamente.")
                            break

            if all_items_processed_successfully:
                result_comanda = order_model.update_order_status(self.current_active_order_id, 'en preparacion')
                if result_comanda:
                    messagebox.showinfo("Éxito", f"Comanda {self.current_active_order_id} y sus platos pendientes enviados a cocina.")
                else:
                    messagebox.showerror("Error", f"Se procesaron los platos, pero no se pudo actualizar el estado general de la comanda {self.current_active_order_id}.")

            self._display_order_details(self.current_active_order_id)
        self._update_ui_states()

    def _finalize_order_and_free_table(self):
        if not self.current_active_order_id or self.current_order_status != 'servida':
            messagebox.showwarning("Acción Requerida", "Solo se pueden finalizar comandas que estén en estado 'servida'.")
            return

        action = simpledialog.askstring("Finalizar Comanda",
                                        f"Comanda: {self.current_active_order_id}\nEstado actual: Servida\n\n"
                                        "Acción: 'facturar' o 'cancelar'",
                                        parent=self, initialvalue="facturar")

        if action and action.lower() in ['facturar', 'cancelar']:
            new_final_status = 'facturada' if action.lower() == 'facturar' else 'cancelada'

            result = order_model.update_order_status(self.current_active_order_id, new_final_status)
            if result is not None and result > 0:
                messagebox.showinfo("Comanda Finalizada", f"Comanda {self.current_active_order_id} marcada como '{new_final_status}'.\nMesa {self.current_selected_table_id} liberada.")
                self._load_tables_to_listbox()
                self._clear_selection_and_order_details()
            else:
                messagebox.showerror("Error", f"No se pudo finalizar la comanda {self.current_active_order_id}.")
        elif action is not None:
            messagebox.showwarning("Acción Inválida", "Por favor, ingrese 'facturar' o 'cancelar'.")

        self._update_ui_states()

if __name__ == '__main__':
    if not all([table_model, menu_model, order_model, auth_logic, stock_model]):
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico de Módulo",
                             "No se pudieron cargar módulos esenciales para probar la vista de toma de comandas.")
        root_error.destroy()
    else:
        test_employee_info = {
            "id_empleado": "MESERO_TEST01",
            "nombre": "MeseroPrueba",
            "apellido": "Test",
            "rol": "mesero"
        }
        root = tk.Tk()
        root.title("Toma de Comandas (Prueba Aislada)")
        root.geometry("1200x750")

        style = ttk.Style(root)
        available_themes = style.theme_names()
        if 'clam' in available_themes: style.theme_use('clam')
        elif 'vista' in available_themes: style.theme_use('vista')

        order_taking_view_frame = OrderTakingView(root, test_employee_info)
        order_taking_view_frame.pack(fill=tk.BOTH, expand=True)

        root.mainloop()
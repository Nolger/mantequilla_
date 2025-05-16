# app/views/order_history_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import datetime # Para validación de fechas

try:
    from ..models import order_model, employee_model, table_model # Para poblar filtros
except ImportError:
    try:
        from models import order_model, employee_model, table_model
    except ImportError:
        order_model = employee_model = table_model = None

class OrderHistoryView(ttk.Frame):
    def __init__(self, parent_container, *args, **kwargs):
        super().__init__(parent_container, *args, **kwargs)
        
        if not order_model:
            ttk.Label(self, text="Error: Modelo de comandas no disponible.", foreground="red").pack(pady=20)
            return

        # Variables para filtros
        self.filter_oh_start_date_var = tk.StringVar()
        self.filter_oh_end_date_var = tk.StringVar()
        self.filter_oh_table_id_var = tk.StringVar()
        self.filter_oh_employee_id_var = tk.StringVar()
        self.filter_oh_status_var = tk.StringVar()
        
        self.selected_order_id_for_details = None # Para mostrar detalles de una comanda del historial

        self._create_widgets()
        self._populate_filter_comboboxes()
        self._load_order_history()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Filtros ---
        filter_lf = ttk.LabelFrame(main_frame, text="Filtros del Historial de Comandas", padding="10")
        filter_lf.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(filter_lf, text="Desde (YYYY-MM-DD):").grid(row=0, column=0, padx=3, pady=3, sticky="w")
        self.start_date_entry = ttk.Entry(filter_lf, textvariable=self.filter_oh_start_date_var, width=12)
        self.start_date_entry.grid(row=0, column=1, padx=3, pady=3)

        ttk.Label(filter_lf, text="Hasta (YYYY-MM-DD):").grid(row=1, column=0, padx=3, pady=3, sticky="w")
        self.end_date_entry = ttk.Entry(filter_lf, textvariable=self.filter_oh_end_date_var, width=12)
        self.end_date_entry.grid(row=1, column=1, padx=3, pady=3)

        ttk.Label(filter_lf, text="Mesa ID:").grid(row=0, column=2, padx=3, pady=3, sticky="w")
        self.table_combo = ttk.Combobox(filter_lf, textvariable=self.filter_oh_table_id_var, width=10, state="readonly")
        self.table_combo.grid(row=0, column=3, padx=3, pady=3)

        ttk.Label(filter_lf, text="Mesero ID:").grid(row=1, column=2, padx=3, pady=3, sticky="w")
        self.employee_combo = ttk.Combobox(filter_lf, textvariable=self.filter_oh_employee_id_var, width=15, state="readonly")
        self.employee_combo.grid(row=1, column=3, padx=3, pady=3)
        
        ttk.Label(filter_lf, text="Estado Comanda:").grid(row=0, column=4, padx=3, pady=3, sticky="w")
        self.status_combo = ttk.Combobox(filter_lf, textvariable=self.filter_oh_status_var, width=15, state="readonly",
                                         values=["", "abierta", "en preparacion", "lista para servir", "servida", "facturada", "cancelada"])
        self.status_combo.grid(row=0, column=5, padx=3, pady=3)


        apply_btn = ttk.Button(filter_lf, text="Buscar", command=self._load_order_history)
        apply_btn.grid(row=0, column=6, rowspan=2, padx=10, pady=3, sticky="ns")
        clear_btn = ttk.Button(filter_lf, text="Limpiar", command=self._clear_order_history_filters)
        clear_btn.grid(row=0, column=7, rowspan=2, padx=10, pady=3, sticky="ns")

        # --- Treeview para Historial de Comandas ---
        history_lf = ttk.LabelFrame(main_frame, text="Historial de Comandas", padding="10")
        history_lf.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        cols = ("id_comanda", "fecha_apertura", "mesa", "mesero", "cliente", "personas", "estado", "fecha_cierre")
        self.history_treeview = ttk.Treeview(history_lf, columns=cols, show="headings", selectmode="browse", height=15)
        
        self.history_treeview.heading("id_comanda", text="ID Comanda")
        self.history_treeview.heading("fecha_apertura", text="Apertura")
        self.history_treeview.heading("mesa", text="Mesa")
        self.history_treeview.heading("mesero", text="Mesero")
        self.history_treeview.heading("cliente", text="Cliente")
        self.history_treeview.heading("personas", text="Personas")
        self.history_treeview.heading("estado", text="Estado")
        self.history_treeview.heading("fecha_cierre", text="Cierre")

        self.history_treeview.column("id_comanda", width=120)
        self.history_treeview.column("fecha_apertura", width=140)
        self.history_treeview.column("mesa", width=80)
        self.history_treeview.column("mesero", width=150)
        self.history_treeview.column("cliente", width=150)
        self.history_treeview.column("personas", width=70, anchor="center")
        self.history_treeview.column("estado", width=100)
        self.history_treeview.column("fecha_cierre", width=140)
        
        hist_scroll = ttk.Scrollbar(history_lf, orient=tk.VERTICAL, command=self.history_treeview.yview)
        self.history_treeview.configure(yscrollcommand=hist_scroll.set)
        self.history_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_treeview.bind("<<TreeviewSelect>>", self._on_order_history_selected)
        
        # --- Botón para ver detalles de la comanda seleccionada ---
        # Podrías tener un frame debajo para mostrar los detalles o un botón que abra un Toplevel
        self.view_details_button = ttk.Button(main_frame, text="Ver Detalles de Comanda Seleccionada", 
                                              command=self._show_selected_order_details, state=tk.DISABLED)
        self.view_details_button.pack(pady=10)


    def _populate_filter_comboboxes(self):
        if table_model:
            tables = table_model.get_all_tables_list()
            self.table_combo['values'] = [""] + [t['id_mesa'] for t in tables if tables] if tables else [""]
        if employee_model:
            employees = employee_model.get_all_employees_list() # Podrías filtrar por rol mesero
            self.employee_combo['values'] = [""] + [f"{e['nombre']} {e['apellido']} ({e['id_empleado']})" for e in employees if employees] if employees else [""]
            # Nota: Si usas el nombre + ID, necesitarás parsear el ID al enviar al modelo.

    def _load_order_history(self):
        if not order_model: return
        for item in self.history_treeview.get_children():
            self.history_treeview.delete(item)
        self.selected_order_id_for_details = None
        self.view_details_button.config(state=tk.DISABLED)

        start_d = self.filter_oh_start_date_var.get().strip() or None
        end_d = self.filter_oh_end_date_var.get().strip() or None
        table_id_val = self.filter_oh_table_id_var.get().strip() or None
        
        employee_display_val = self.filter_oh_employee_id_var.get().strip()
        employee_id_val = None
        if employee_display_val: # Parsear ID si el formato es "Nombre Apellido (ID)"
            try: employee_id_val = employee_display_val.split('(')[-1].split(')')[0]
            except: pass # Si no tiene el formato esperado, se ignora
            
        status_val = self.filter_oh_status_var.get().strip() or None

        if start_d:
            try: datetime.datetime.strptime(start_d, "%Y-%m-%d")
            except ValueError: messagebox.showerror("Error Filtro", "Formato 'Desde' inválido."); return
        if end_d:
            try: datetime.datetime.strptime(end_d, "%Y-%m-%d")
            except ValueError: messagebox.showerror("Error Filtro", "Formato 'Hasta' inválido."); return

        history = order_model.get_orders_history(
            start_date=start_d, end_date=end_d, table_id=table_id_val,
            employee_id=employee_id_val, order_status=status_val, limit=200
        )

        if history:
            for order in history:
                mesero_name = f"{order.get('nombre_mesero','')} {order.get('apellido_mesero','')}".strip()
                self.history_treeview.insert("", tk.END, iid=order['id_comanda'], values=(
                    order.get('id_comanda',''),
                    order.get('fecha_hora_apertura','').strftime('%Y-%m-%d %H:%M') if order.get('fecha_hora_apertura') else '',
                    order.get('id_mesa',''),
                    mesero_name or order.get('id_empleado_mesero',''),
                    order.get('nombre_cliente','') or order.get('id_cliente',''),
                    order.get('cantidad_personas',''),
                    order.get('estado_comanda',''),
                    order.get('fecha_hora_cierre','').strftime('%Y-%m-%d %H:%M') if order.get('fecha_hora_cierre') else 'N/A'
                ))
        elif history == []:
            messagebox.showinfo("Historial", "No se encontraron comandas con los filtros aplicados.")
        else:
            messagebox.showerror("Error", "No se pudo cargar el historial de comandas.")
            
    def _clear_order_history_filters(self):
        self.filter_oh_start_date_var.set("")
        self.filter_oh_end_date_var.set("")
        self.filter_oh_table_id_var.set("")
        self.filter_oh_employee_id_var.set("")
        self.filter_oh_status_var.set("")
        self._load_order_history()

    def _on_order_history_selected(self, event=None):
        selected = self.history_treeview.selection()
        if selected:
            self.selected_order_id_for_details = selected[0] # iid es id_comanda
            self.view_details_button.config(state=tk.NORMAL)
        else:
            self.selected_order_id_for_details = None
            self.view_details_button.config(state=tk.DISABLED)

    def _show_selected_order_details(self):
        if not self.selected_order_id_for_details or not order_model:
            return
        
        order_full_data = order_model.get_order_by_id(self.selected_order_id_for_details)
        if not order_full_data:
            messagebox.showerror("Error", "No se pudieron cargar los detalles de la comanda.")
            return

        details_win = tk.Toplevel(self)
        details_win.title(f"Detalles Comanda: {self.selected_order_id_for_details}")
        details_win.geometry("600x400")
        
        text_area = tk.Text(details_win, wrap=tk.WORD, font=("Consolas", 10), height=20, width=70)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        details_str = f"Comanda ID: {order_full_data.get('id_comanda')}\n"
        details_str += f"Mesa: {order_full_data.get('id_mesa')}\n"
        details_str += f"Mesero ID: {order_full_data.get('id_empleado_mesero')}\n" # Podrías JOIN para nombre
        details_str += f"Cliente ID: {order_full_data.get('id_cliente', 'N/A')}\n"
        details_str += f"Apertura: {order_full_data.get('fecha_hora_apertura').strftime('%Y-%m-%d %H:%M') if order_full_data.get('fecha_hora_apertura') else 'N/A'}\n"
        details_str += f"Cierre: {order_full_data.get('fecha_hora_cierre').strftime('%Y-%m-%d %H:%M') if order_full_data.get('fecha_hora_cierre') else 'N/A'}\n"
        details_str += f"Personas: {order_full_data.get('cantidad_personas')}\n"
        details_str += f"Estado: {order_full_data.get('estado_comanda')}\n"
        details_str += f"Observaciones Generales: {order_full_data.get('observaciones', 'Ninguna')}\n\n"
        details_str += "--- Platos ---\n"
        
        total_comanda = 0.0
        if order_full_data.get('detalles'):
            for item in order_full_data['detalles']:
                details_str += (
                    f"  - {item['cantidad']}x {item['nombre_plato']} "
                    f"(@ ${item['precio_unitario_momento']:.2f} c/u) "
                    f"= ${item['subtotal_detalle']:.2f}\n"
                    f"    Estado Plato: {item['estado_plato']}\n"
                    f"    Obs. Plato: {item.get('observaciones_plato', 'Ninguna')}\n"
                )
                total_comanda += item['subtotal_detalle']
        else:
            details_str += "  (No hay platos en esta comanda)\n"
            
        details_str += f"\n--- TOTAL COMANDA: ${total_comanda:.2f} ---"

        text_area.insert("1.0", details_str)
        text_area.config(state=tk.DISABLED)
        
        ttk.Button(details_win, text="Cerrar", command=details_win.destroy).pack(pady=5)
        details_win.transient(self)
        details_win.grab_set()
        self.wait_window(details_win)

# Para probar esta vista aislada
if __name__ == '__main__':
    if not order_model:
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error", "Modelo de comandas no disponible para prueba.")
        root_error.destroy()
    else:
        root = tk.Tk()
        root.title("Historial de Comandas (Prueba)")
        root.geometry("950x600")
        style = ttk.Style(root)
        if 'clam' in style.theme_names(): style.theme_use('clam')
        
        view = OrderHistoryView(root)
        view.pack(expand=True, fill=tk.BOTH)
        root.mainloop()
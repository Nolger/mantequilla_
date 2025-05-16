# app/views/waiter_dashboard_view.py
import tkinter as tk
from tkinter import ttk, messagebox

# Importar OrderTakingView y modelos si es necesario para otras funcionalidades
try:
    from .order_taking_view import OrderTakingView
    from ..models import order_model # Para la lista de "Mis Comandas"
except ImportError:
    try:
        from order_taking_view import OrderTakingView
        from models import order_model
    except ImportError:
        OrderTakingView = None
        order_model = None
        print("Error crítico: No se pudo importar OrderTakingView o order_model.")

class WaiterDashboardView(tk.Tk):
    def __init__(self, waiter_user_info):
        super().__init__()

        if not OrderTakingView:
            self.withdraw()
            messagebox.showerror("Error Crítico", "No se pudo cargar el módulo de toma de comandas.")
            self.destroy()
            return

        self.waiter_user_info = waiter_user_info
        self.title(f"Panel de Mesero - (Usuario: {self.waiter_user_info.get('nombre', 'Mesero')})")
        self.geometry("1150x750") # Similar a OrderTakingView

        style = ttk.Style(self)
        if 'clam' in style.theme_names(): style.theme_use('clam')

        self._create_main_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_main_widgets(self):
        main_notebook = ttk.Notebook(self)
        main_notebook.pack(expand=True, fill='both', padx=5, pady=5)

        # Pestaña principal: Toma de Comandas
        order_taking_tab = ttk.Frame(main_notebook) # No necesita padding si OrderTakingView ya lo tiene
        main_notebook.add(order_taking_tab, text='Gestión de Mesas y Comandas')
        
        # Instanciar OrderTakingView dentro de esta pestaña
        # OrderTakingView ya es un ttk.Frame, así que se puede empaquetar directamente.
        self.order_taking_view_instance = OrderTakingView(order_taking_tab, self.waiter_user_info)
        self.order_taking_view_instance.pack(expand=True, fill=tk.BOTH)

        # (Opcional) Pestaña: Mis Comandas Activas
        if order_model: # Solo si el modelo está disponible
            my_orders_tab = ttk.Frame(main_notebook, padding="10")
            main_notebook.add(my_orders_tab, text='Mis Comandas Activas')
            self._create_my_active_orders_list(my_orders_tab)


        # Botón de Cerrar Sesión (general para el dashboard del mesero)
        logout_button_frame = ttk.Frame(self)
        logout_button_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        logout_btn = ttk.Button(logout_button_frame, text="Cerrar Sesión", command=self._logout)
        logout_btn.pack(side=tk.RIGHT)

    def _create_my_active_orders_list(self, parent_tab):
        ttk.Label(parent_tab, text="Comandas que estás atendiendo:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        
        cols = ("id_comanda", "mesa", "apertura", "estado_comanda", "personas")
        self.my_orders_treeview = ttk.Treeview(parent_tab, columns=cols, show="headings", selectmode="browse", height=10)
        self.my_orders_treeview.heading("id_comanda", text="ID Comanda")
        self.my_orders_treeview.heading("mesa", text="Mesa")
        self.my_orders_treeview.heading("apertura", text="Apertura")
        self.my_orders_treeview.heading("estado_comanda", text="Estado")
        self.my_orders_treeview.heading("personas", text="Personas")
        
        # Ajustar anchos según necesidad
        self.my_orders_treeview.column("id_comanda", width=120)
        # ... otros anchos ...

        scroll = ttk.Scrollbar(parent_tab, orient=tk.VERTICAL, command=self.my_orders_treeview.yview)
        self.my_orders_treeview.configure(yscrollcommand=scroll.set)
        self.my_orders_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        refresh_my_orders_btn = ttk.Button(parent_tab, text="Refrescar Mis Comandas", command=self._load_my_active_orders)
        refresh_my_orders_btn.pack(pady=5)
        
        self._load_my_active_orders() # Carga inicial

    def _load_my_active_orders(self):
        if not order_model or not hasattr(self, 'my_orders_treeview'): return
        for item in self.my_orders_treeview.get_children():
            self.my_orders_treeview.delete(item)
            
        mesero_id = self.waiter_user_info.get('id_empleado')
        if not mesero_id: return

        my_active_orders = order_model.get_active_orders_for_waiter(mesero_id)
        if my_active_orders:
            for order in my_active_orders:
                apertura_f = order.get('fecha_hora_apertura','').strftime('%Y-%m-%d %H:%M') if order.get('fecha_hora_apertura') else ''
                self.my_orders_treeview.insert("", tk.END, values=(
                    order.get('id_comanda'),
                    order.get('nombre_mesa'), # Usando el alias de la consulta
                    apertura_f,
                    order.get('estado_comanda'),
                    order.get('cantidad_personas')
                ))
        elif my_active_orders == []:
            print("Mesero no tiene comandas activas.")
        else:
            messagebox.showerror("Error", "No se pudieron cargar 'Mis Comandas Activas'.")


    def _logout(self):
        if messagebox.askokcancel("Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión?"):
            self.destroy()

    def _on_closing(self):
        if messagebox.askokcancel("Salir", "¿Está seguro de que desea salir de la aplicación?"):
            self.destroy()

# Para probar esta vista de forma aislada
if __name__ == '__main__':
    if not OrderTakingView:
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error", "OrderTakingView no disponible para prueba del WaiterDashboard.")
        root_error.destroy()
    else:
        test_waiter_info = {
            "id_empleado": "MESERO01", # Asegúrate que exista con rol 'mesero'
            "nombre": "Mesero",
            "apellido": "DePrueba",
            "rol": "mesero"
        }
        root = tk.Tk()
        root.title("Prueba Dashboard Mesero")
        
        # Es importante tener datos de prueba (mesas, platos en menú, comandas)
        # para que la OrderTakingView interna funcione y muestre algo.
        print("Asegúrate de tener mesas y platos en el menú para probar.")

        waiter_dash = WaiterDashboardView(root, test_waiter_info)
        waiter_dash.pack(expand=True, fill=tk.BOTH)
        root.mainloop()
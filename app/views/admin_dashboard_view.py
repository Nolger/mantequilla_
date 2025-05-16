# app/views/admin_dashboard_view.py
import tkinter as tk
from tkinter import ttk, messagebox

# Ajusta la ruta de importación según tu estructura de proyecto.
from .employee_view import EmployeeView
from .dish_recipe_management_view import DishRecipeManagementView
from .table_view import TableView
from .order_taking_view import OrderTakingView
from .stock_management_view import StockManagementView
from .supplier_view import SupplierView
from .admin_home_tab_view import AdminHomeTabView
from .order_history_view import OrderHistoryView

class AdminDashboardView(tk.Tk):
    def __init__(self, admin_user_info):
        super().__init__()

        # Comprobación crítica de módulos (incluyendo la nueva)
        if not all([EmployeeView, TableView, OrderTakingView, StockManagementView, SupplierView, DishRecipeManagementView, AdminHomeTabView, OrderHistoryView]):
            self.withdraw() 
            messagebox.showerror("Error Crítico de Módulo", 
                                 "Uno o más módulos de vista esenciales no están disponibles.\n" +
                                 "El dashboard no puede cargarse.")
            self.destroy()
            return
        # ... (resto del __init__ sin cambios) ...
        self.admin_user_info = admin_user_info
        self.title(f"Panel de Administrador - Restaurante (Usuario: {self.admin_user_info.get('nombre', 'Admin')})")
        self.geometry("1000x750")

        style = ttk.Style(self)
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes: 
            style.theme_use('vista')
        
        self._create_main_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)


    def _create_main_widgets(self):
        main_content_frame = ttk.Frame(self, padding="10")
        main_content_frame.pack(expand=True, fill=tk.BOTH)

        welcome_message = f"Bienvenido, {self.admin_user_info.get('nombre', '')} {self.admin_user_info.get('apellido', '')} (Rol: {self.admin_user_info.get('rol', '')})"
        welcome_label = ttk.Label(main_content_frame, text=welcome_message, font=("Arial", 12, "italic"))
        welcome_label.pack(pady=(0, 10), anchor="w")

        self.notebook = ttk.Notebook(main_content_frame)
        self.notebook.pack(expand=True, fill='both')

        # --- Pestaña de Inicio/Resumen (NUEVA) ---
        self.home_tab = AdminHomeTabView(self.notebook) # Usar la clase directamente
        self.notebook.add(self.home_tab, text='Inicio')
        # No necesitas .pack() aquí porque AdminHomeTabView es un Frame y se llenará

        # --- Pestaña de Gestión de Empleados ---
        self.employee_management_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.employee_management_tab, text='Gestión de Empleados')
        
        if EmployeeView:
            employee_view_instance = EmployeeView(self.employee_management_tab)
            employee_view_instance.pack(expand=True, fill=tk.BOTH)
        else:
            ttk.Label(self.employee_management_tab, text="Error al cargar la vista de empleados.").pack()

        # --- Pestaña NUEVA: Historial de Comandas ---
        self.order_history_management_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.order_history_management_tab, text='Historial de Comandas')
        
        if OrderHistoryView:
            order_history_view_instance = OrderHistoryView(self.order_history_management_tab)
            order_history_view_instance.pack(expand=True, fill=tk.BOTH)
        else:
            ttk.Label(self.order_history_management_tab, text="Error al cargar la vista de historial de comandas.").pack()

        # --- Pestaña de Gestión de Mesas ---
        self.table_management_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.table_management_tab, text='Gestión de Mesas')
        
        if TableView:
            table_view_instance = TableView(self.table_management_tab)
            table_view_instance.pack(expand=True, fill=tk.BOTH)
        else:
            ttk.Label(self.table_management_tab, text="Error al cargar la vista de gestión de mesas.").pack()

        # --- Pestaña de Toma de Comandas (para que el admin también pueda) ---
        self.order_taking_tab_admin = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.order_taking_tab_admin, text='Toma de Comandas (Admin)')
        
        if OrderTakingView:
            order_view_instance_admin = OrderTakingView(self.order_taking_tab_admin, self.admin_user_info)
            order_view_instance_admin.pack(expand=True, fill=tk.BOTH)
        else:
            ttk.Label(self.order_taking_tab_admin, text="Error al cargar la vista de toma de comandas.").pack()
        
        # --- Pestaña de Gestión de Menú ---
        self.menu_management_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.menu_management_tab, text='Gestión de Menú')
        
        if DishRecipeManagementView:
            dish_recipe_view_instance = DishRecipeManagementView(self.menu_management_tab)
            dish_recipe_view_instance.pack(expand=True, fill=tk.BOTH)
        else:
            ttk.Label(self.menu_management_tab, text="Error al cargar la vista de gestión de menú.").pack()

        # --- Pestaña de Gestión de Stock ---
        self.stock_management_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.stock_management_tab, text='Gestión de Stock')
        
        if StockManagementView:
            stock_view_instance = StockManagementView(self.stock_management_tab)
            stock_view_instance.pack(expand=True, fill=tk.BOTH)
        else:
            ttk.Label(self.stock_management_tab, text="Error al cargar la vista de gestión de stock.").pack()

        # --- Pestaña de Gestión de Proveedores ---
        self.supplier_management_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.supplier_management_tab, text='Gestión de Proveedores')
        
        if SupplierView:
            supplier_view_instance = SupplierView(self.supplier_management_tab)
            supplier_view_instance.pack(expand=True, fill=tk.BOTH)
        else:
            ttk.Label(self.supplier_management_tab, text="Error al cargar la vista de gestión de proveedores.").pack()


        logout_button = ttk.Button(main_content_frame, text="Cerrar Sesión", command=self._logout)
        logout_button.pack(pady=10, side=tk.BOTTOM, anchor="se")

    # ... (resto de _logout y _on_closing sin cambios) ...
    def _logout(self):
        if messagebox.askokcancel("Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión?"):
            self.destroy()
            print("Cierre de sesión solicitado. main_app.py debería manejar el reinicio del login.")

    def _on_closing(self):
        if messagebox.askokcancel("Salir", "¿Está seguro de que desea salir de la aplicación?"):
            self.destroy()
            print("Cierre de aplicación solicitado.")


# Para probar este dashboard de forma aislada (main_test de AdminDashboardView)
def main_test(admin_info_for_test=None):
    if admin_info_for_test is None:
        admin_info_for_test = {
            "id_empleado": "ADMIN_TEST_DASH",
            "nombre": "AdminDash",
            "apellido": "Tester",
            "rol": "administrador"
        }
    # Actualiza la comprobación para incluir AdminHomeTabView y OrderHistoryView
    if not all([EmployeeView, TableView, OrderTakingView, StockManagementView, DishRecipeManagementView, SupplierView, AdminHomeTabView, OrderHistoryView]):
        root_error = tk.Tk()
        root_error.withdraw()
        messagebox.showerror("Error Crítico de Módulo", 
                             "No se pudieron cargar módulos de vista esenciales para probar el dashboard.")
        root_error.destroy()
        return

    dashboard_app = AdminDashboardView(admin_info_for_test)
    dashboard_app.mainloop()

if __name__ == '__main__':
    print("Ejecutando prueba aislada del AdminDashboardView...")
    main_test()
# main_app.py
import tkinter as tk
from tkinter import messagebox
import sys
import os

# Importar las vistas necesarias usando rutas absolutas
try:
    from app.views import login_view
    from app.views import admin_dashboard_view
    from app.views import employee_dashboard_view
except ImportError as e:
    # Manejo de error si las importaciones fallan al inicio
    root_error = tk.Tk()
    root_error.withdraw() # Ocultar la ventana principal vacía
    messagebox.showerror("Error Crítico de Importación", 
                         f"No se pudieron importar módulos esenciales de la aplicación: {e}\n" +
                         "Asegúrate de que la estructura de carpetas (app/views/, etc.) sea correcta y que los archivos existan.")
    root_error.destroy()
    sys.exit(f"Error de importación: {e}")

class MainApplication:
    def __init__(self):
        self.current_user_info = None
        self.show_login_screen()

    def show_login_screen(self):
        # Limpiar cualquier información de usuario anterior
        self.current_user_info = None 
        
        # La vista de login ahora maneja la apertura del dashboard correcto internamente
        # a través de su propio mainloop.
        # Pasamos un callback para que el login nos notifique del éxito.
        login_view.start_login_view(on_success_callback=self.handle_login_success)
        
        # Después de que login_view.start_login_view() termina (es decir, su mainloop se cierra),
        # verificamos si hubo un login exitoso. Si no, la aplicación podría terminar.
        if not self.current_user_info:
            print("La ventana de login se cerró sin un inicio de sesión exitoso. Saliendo de la aplicación.")
            # Aquí podrías decidir si quieres que la aplicación se cierre completamente
            # o si quieres reintentar el login (lo cual sería un bucle más complejo).
            # Por simplicidad, la aplicación terminará si el login se cierra sin éxito.

    def handle_login_success(self, user_info):
        """
        Este callback es llamado por LoginView cuando el login es exitoso.
        Se encarga de cerrar la ventana de login y abrir el dashboard apropiado.
        """
        self.current_user_info = user_info
        print(f"Login exitoso para: {self.current_user_info.get('nombre')}, Rol: {self.current_user_info.get('rol')}")

        # LoginView ya se destruyó a sí mismo. Ahora abrimos el dashboard.
        rol = self.current_user_info.get("rol")
        
        dashboard_to_open = None
        if rol == "administrador":
            if admin_dashboard_view.AdminDashboardView:
                dashboard_to_open = admin_dashboard_view.AdminDashboardView(self.current_user_info)
            else:
                messagebox.showerror("Error de Carga", "No se pudo cargar el Dashboard de Administrador.")
        elif rol in ["empleado", "mesero", "cocinero"]: # Otros roles de empleado
            if employee_dashboard_view.EmployeeDashboardView:
                dashboard_to_open = employee_dashboard_view.EmployeeDashboardView(self.current_user_info)
            else:
                messagebox.showerror("Error de Carga", "No se pudo cargar el Dashboard de Empleado.")
        else:
            messagebox.showerror("Error de Rol", f"Rol '{rol}' no reconocido. Contacte al administrador.")
            self.show_login_screen() # Vuelve a mostrar el login
            return

        if dashboard_to_open:
            # El mainloop del dashboard tomará el control.
            # Cuando el dashboard se cierre, su mainloop terminará.
            # Podríamos querer volver al login después de que un dashboard se cierre (ej. por logout).
            dashboard_to_open.mainloop() 
            
            # Después de que el dashboard se cierra (ej. por logout o cierre de ventana):
            print(f"Dashboard para {rol} cerrado.")
            # Volver a mostrar la pantalla de login para un nuevo inicio de sesión o para salir.
            self.show_login_screen() 
        else:
            # Si no se pudo abrir un dashboard por alguna razón (ej. error de importación ya manejado)
            # volver al login.
            self.show_login_screen()


if __name__ == "__main__":
    # Verificar que los módulos de vista se hayan importado correctamente
    if not login_view or not admin_dashboard_view or not employee_dashboard_view:
        # El error ya se mostró si las importaciones fallaron al inicio.
        # Simplemente salimos para evitar más errores.
        print("Saliendo debido a errores de importación de módulos de vista.")
    else:
        app = MainApplication()
        # El constructor de MainApplication inicia el ciclo con show_login_screen()
        # No se necesita app.mainloop() aquí porque las ventanas Tk (LoginView, Dashboards)
        # tienen sus propios mainloops.

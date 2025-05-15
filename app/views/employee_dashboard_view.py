# app/views/employee_dashboard_view.py
import tkinter as tk
from tkinter import ttk, messagebox

class EmployeeDashboardView(tk.Tk):
    def __init__(self, employee_user_info):
        super().__init__()

        self.employee_user_info = employee_user_info
        self.title(f"Panel de Empleado - Restaurante (Usuario: {self.employee_user_info.get('nombre', 'Empleado')})")
        self.geometry("700x500") # Tamaño inicial

        # Estilo ttk
        style = ttk.Style(self)
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes: 
            style.theme_use('vista')
        
        self._create_main_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_main_widgets(self):
        main_content_frame = ttk.Frame(self, padding="20")
        main_content_frame.pack(expand=True, fill=tk.BOTH)

        welcome_message = (
            f"Bienvenido, {self.employee_user_info.get('nombre', '')} "
            f"{self.employee_user_info.get('apellido', '')}!\n"
            f"Rol: {self.employee_user_info.get('rol', '')}"
        )
        welcome_label = ttk.Label(main_content_frame, text=welcome_message, font=("Arial", 14))
        welcome_label.pack(pady=20)

        info_label = ttk.Label(main_content_frame, text="Este es tu panel de empleado.", font=("Arial", 11))
        info_label.pack(pady=10)
        
        # Aquí podrías añadir funcionalidades específicas para empleados, como:
        # - Ver sus turnos
        # - Registrar asistencia
        # - Acceder a la toma de comandas (si es mesero)
        # - Ver estado de pedidos (si es cocinero)

        logout_button = ttk.Button(main_content_frame, text="Cerrar Sesión", command=self._logout)
        logout_button.pack(pady=20, side=tk.BOTTOM)

    def _logout(self):
        if messagebox.askokcancel("Cerrar Sesión", "¿Está seguro de que desea cerrar la sesión?"):
            self.destroy()
            # Idealmente, esto debería reiniciar la aplicación o volver a la pantalla de login.
            # Esto se manejaría en main_app.py si el login devolviera un estado.
            # Por ahora, simplemente cerramos.
            print("Cierre de sesión de empleado solicitado.")
            # Para reiniciar el login, necesitaríamos una referencia a la función main de login_view
            # o una función de controlador principal en main_app.py
            # from .login_view import main as show_login_screen # Cuidado con importaciones circulares si no se maneja bien
            # show_login_screen()


    def _on_closing(self):
        if messagebox.askokcancel("Salir", "¿Está seguro de que desea salir de la aplicación?"):
            self.destroy()

# Para probar este dashboard de forma aislada
def main_test(employee_info_for_test=None):
    if employee_info_for_test is None:
        employee_info_for_test = {
            "id_empleado": "EMP_TEST01",
            "nombre": "Empleado",
            "apellido": "DePrueba",
            "rol": "mesero"
        }
    
    dashboard_app = EmployeeDashboardView(employee_info_for_test)
    dashboard_app.mainloop()

if __name__ == '__main__':
    # Para ejecutar esta prueba: python -m app.views.employee_dashboard_view
    # (desde la raíz de tu proyecto)
    print("Ejecutando prueba aislada del EmployeeDashboardView...")
    main_test()

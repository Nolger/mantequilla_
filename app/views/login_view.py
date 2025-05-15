# app/views/login_view.py
import tkinter as tk
from tkinter import ttk, messagebox

# Ajusta la ruta de importación según tu estructura
try:
    from ..auth import auth_logic 
except ImportError:
    try:
        from auth import auth_logic 
    except ImportError:
        try:
            import auth_logic 
        except ImportError:
            print("Error: No se pudo importar auth_logic.py. Verifica la estructura de tu proyecto.")
            auth_logic = None

# Importar los dashboards
try:
    from .admin_dashboard_view import AdminDashboardView
    from .employee_dashboard_view import EmployeeDashboardView
except ImportError:
    try:
        from admin_dashboard_view import AdminDashboardView
        from employee_dashboard_view import EmployeeDashboardView
    except ImportError:
        print("Error: No se pudieron importar los módulos de Dashboard. Verifica las rutas.")
        AdminDashboardView = None
        EmployeeDashboardView = None


class LoginView(tk.Tk):
    def __init__(self, on_login_success_callback=None): # Acepta un callback
        super().__init__()
        self.on_login_success_callback = on_login_success_callback
        self.title("Inicio de Sesión - Sistema Restaurante")
        self.geometry("400x270") # Un poco más de alto para el botón
        self.resizable(False, False)

        style = ttk.Style(self)
        available_themes = style.theme_names()
        # Intentar usar un tema moderno si está disponible
        # 'clam' suele ser bueno para personalización. 'alt', 'default', 'classic' también existen.
        # En Windows, 'vista', 'xpnative' pueden ser opciones.
        current_theme = style.theme_use()
        print(f"Tema ttk actual: {current_theme}") # Para depuración
        
        # Intentar establecer un tema que permita mejor personalización si no es uno ya bueno
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
             style.theme_use('alt')

        
        self.configure(bg='#f0f0f0') 

        main_frame = ttk.Frame(self, padding="20 20 20 20") # No es necesario style='Main.TFrame' si el frame no tiene estilo propio
        main_frame.pack(expand=True, fill=tk.BOTH)
        # Si el frame principal no necesita un estilo específico, no es necesario style.configure para él.

        ttk.Label(main_frame, text="Acceso al Sistema", font=("Arial", 16, "bold")).pack(pady=(0, 20)) # Quitar background si hereda del frame

        ttk.Label(main_frame, text="ID de Empleado:").pack(anchor=tk.W, padx=10)
        self.employee_id_var = tk.StringVar()
        self.employee_id_entry = ttk.Entry(main_frame, textvariable=self.employee_id_var, width=30, font=("Arial", 11))
        self.employee_id_entry.pack(pady=(0,10), padx=10, ipady=3)
        self.employee_id_entry.focus() 

        ttk.Label(main_frame, text="Contraseña:").pack(anchor=tk.W, padx=10)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30, font=("Arial", 11))
        self.password_entry.pack(pady=(0,20), padx=10, ipady=3)

        # --- Modificación del Botón ---
        # Crear un estilo específico para el botón si es necesario, o usar opciones directas.
        # La opción 'foreground' en style.configure para ttk.Button a veces no funciona como se espera
        # en todos los temas/plataformas para el color del texto.
        
        # Opción 1: Simplificar el estilo ttk
        style.configure('Accent.TButton', font=('Arial', 11, 'bold'), padding=(10, 5))
        # El color de fondo de ttk.Button es mejor manejarlo con temas o de forma más limitada.
        # Si el tema 'clam' o 'alt' está activo, el botón debería verse razonablemente bien.
        # Si necesitas un color de fondo específico y el texto no aparece, considera tk.Button.

        self.login_button = ttk.Button(main_frame, text="Ingresar", command=self.attempt_login, style='Accent.TButton', width=15)
        self.login_button.pack(pady=10) # ipadx e ipady pueden no ser necesarios si el padding está en el estilo

        # Opción 2: Usar tk.Button estándar para mayor control de color (si ttk sigue dando problemas)
        # Descomenta las siguientes líneas y comenta las de ttk.Button de arriba si es necesario.
        # self.login_button = tk.Button(main_frame, text="Ingresar", command=self.attempt_login,
        #                               font=('Arial', 11, 'bold'), bg='#0078D7', fg='white',
        #                               relief=tk.RAISED, borderwidth=2, padx=10, pady=5)
        # self.login_button.pack(pady=10)
        
        self.bind('<Return>', self.attempt_login_event)
        
        self.update_idletasks() 
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')


    def attempt_login_event(self, event=None): 
        self.attempt_login()

    def attempt_login(self):
        employee_id = self.employee_id_var.get().strip()
        password = self.password_var.get()

        if not employee_id or not password:
            messagebox.showerror("Error de Entrada", "Por favor, ingrese ID de empleado y contraseña.")
            return

        if not auth_logic:
            messagebox.showerror("Error de Configuración", "El módulo de autenticación no está disponible.")
            return
        
        if not AdminDashboardView or not EmployeeDashboardView:
            messagebox.showerror("Error de Configuración", "Los módulos de dashboard no están disponibles.")
            return

        authenticated_employee_info = auth_logic.verify_employee_credentials(employee_id, password)

        if authenticated_employee_info:
            if self.on_login_success_callback:
                self.destroy() 
                self.on_login_success_callback(authenticated_employee_info)
            else:
                self.destroy() 
                rol = authenticated_employee_info.get("rol")
                if rol == "administrador":
                    dashboard = AdminDashboardView(authenticated_employee_info)
                    dashboard.mainloop()
                elif rol in ["empleado", "mesero", "cocinero"]: 
                    dashboard = EmployeeDashboardView(authenticated_employee_info)
                    dashboard.mainloop()
                else:
                    messagebox.showerror("Error de Rol", f"Rol '{rol}' no reconocido. Contacte al administrador.")
        else:
            messagebox.showerror("Login Fallido", "ID de empleado o contraseña incorrectos, o empleado inactivo.")
            self.password_var.set("") 
            self.password_entry.focus()

def start_login_view(on_success_callback=None):
    if auth_logic is None: 
        try:
            root_error = tk.Tk()
            root_error.withdraw() 
            messagebox.showerror("Error Crítico", "No se pudo cargar el módulo de autenticación. La aplicación no puede continuar.")
            root_error.destroy()
        except tk.TclError: 
            print("Error Crítico: No se pudo cargar el módulo de autenticación. La aplicación no puede continuar.")
        return None 

    app = LoginView(on_login_success_callback=on_success_callback)
    app.mainloop()
    return "login_closed" 

if __name__ == "__main__":
    print("Ejecutando prueba aislada de LoginView...")
    
    def mock_on_login_success_for_test(user_info):
        print(f"Login exitoso (mock callback): Usuario {user_info.get('nombre')}, Rol {user_info.get('rol')}")
        # ... (simulación de apertura de dashboards) ...

    start_login_view(on_success_callback=mock_on_login_success_for_test)
    print("Prueba aislada de LoginView finalizada.")

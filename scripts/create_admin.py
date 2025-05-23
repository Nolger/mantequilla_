# create_admin_user.py
import sys
import os
import getpass # Para ocultar la entrada de la contraseña

# Para asegurar que los módulos de la app se puedan importar correctamente
# Añadimos la ruta de la carpeta 'app' al sys.path si este script está en la raíz del proyecto.
# Ajusta esto si tu estructura es diferente.
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, 'app') # Asume que 'app' está en el mismo nivel que este script

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

try:
    from auth import auth_logic
    import db # db.py se importa directamente desde la carpeta 'app'
except ImportError as e:
    print(f"Error crítico: No se pudieron importar los módulos necesarios de la aplicación: {e}")
    print("Asegúrate de que la carpeta 'app' con 'db.py' y 'auth/auth_logic.py' exista y sea accesible.")
    print("Si ejecutas desde una subcarpeta, asegúrate de que PYTHONPATH esté configurado o ejecuta desde la raíz del proyecto.")
    sys.exit(1)

def prompt_for_admin_details():
    """
    Solicita al usuario los detalles para el nuevo administrador.
    Returns:
        dict: Un diccionario con los datos del administrador, o None si el usuario cancela.
    """
    print("--- Creación del Usuario Administrador Inicial ---")
    
    employee_id = input("Ingrese el ID para el administrador (ej. ADMIN001): ").strip()
    if not employee_id:
        print("El ID de empleado no puede estar vacío. Operación cancelada.")
        return None

    first_name = input("Ingrese el nombre del administrador: ").strip()
    if not first_name:
        print("El nombre no puede estar vacío. Operación cancelada.")
        return None

    last_name = input("Ingrese el apellido del administrador: ").strip()
    if not last_name:
        print("El apellido no puede estar vacío. Operación cancelada.")
        return None

    while True:
        password = getpass.getpass("Ingrese la contraseña para el administrador: ")
        if not password:
            print("La contraseña no puede estar vacía.")
            continue
        password_confirm = getpass.getpass("Confirme la contraseña: ")
        if password == password_confirm:
            break
        else:
            print("Las contraseñas no coinciden. Inténtelo de nuevo.")

    admin_data = {
        'id_empleado': employee_id,
        'nombre': first_name,
        'apellido': last_name,
        'rol': 'administrador', # Rol predeterminado
        'contrasena_plana': password,
        'estado': 'activo' # Estado predeterminado
    }
    return admin_data

def main():
    """
    Función principal para crear el usuario administrador.
    """
    if not db or not auth_logic:
        # Este cheque ya se hace al importar, pero es una doble seguridad.
        print("Los módulos de base de datos o autenticación no están disponibles. No se puede continuar.")
        return

    admin_details = prompt_for_admin_details()

    if not admin_details:
        return # El usuario canceló o hubo un error en la entrada

    # Verificar si el ID de empleado ya existe
    print(f"\nVerificando si el ID de empleado '{admin_details['id_empleado']}' ya existe...")
    existing_admin = db.fetch_one("SELECT id_empleado FROM Empleados WHERE id_empleado = %s", (admin_details['id_empleado'],))

    if existing_admin:
        print(f"Error: El ID de empleado '{admin_details['id_empleado']}' ya existe en la base de datos.")
        print("No se creará un nuevo administrador con este ID.")
        return

    print(f"Intentando crear el administrador '{admin_details['id_empleado']}'...")
    
    # Usar la función de auth_logic para crear el empleado de forma segura
    # create_employee_secure espera un diccionario con 'contrasena_plana' y otros campos.
    creation_result = auth_logic.create_employee_secure(admin_details)

    if creation_result is not None: # create_employee_secure devuelve el resultado de db.execute_query
        # db.execute_query devuelve lastrowid o rowcount. Para INSERTs sin AUTO_INCREMENT en el ID principal,
        # podría devolver 0 si la inserción fue exitosa pero no hay lastrowid aplicable.
        # Una mejor verificación sería si no devolvió None y no lanzó una excepción.
        print("\n-----------------------------------------------------")
        print(f"¡Usuario administrador '{admin_details['id_empleado']}' procesado exitosamente!")
        print("Detalles:")
        print(f"  ID: {admin_details['id_empleado']}")
        print(f"  Nombre: {admin_details['nombre']} {admin_details['apellido']}")
        print(f"  Rol: {admin_details['rol']}")
        print(f"  Estado: {admin_details['estado']}")
        print("-----------------------------------------------------")
        print("Por favor, guarde esta información de forma segura.")
        print("Ahora puede iniciar sesión en la aplicación con estas credenciales.")
    else:
        print("\nError: No se pudo crear el usuario administrador.")
        print("Revise los mensajes de error anteriores o los logs del servidor de base de datos si es necesario.")

if __name__ == "__main__":
    # Asegurarse de que la base de datos y las tablas existan antes de ejecutar.
    # Este script asume que setup_db.py ya se ha ejecutado.
    print("Este script creará el primer usuario administrador en la base de datos.")
    print("Asegúrese de que la base de datos esté configurada y las tablas creadas.\n")
    
    confirm = input("¿Desea continuar? (s/N): ").strip().lower()
    if confirm == 's':
        main()
    else:
        print("Operación cancelada por el usuario.")

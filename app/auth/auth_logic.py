# app/auth/auth_logic.py
import hashlib
import os
# Suponiendo que db.py está en la carpeta 'app' y este archivo está en 'app/auth/'
# Ajusta la ruta de importación según tu estructura de proyecto.
try:
    from .. import db  # Para estructuras como app/db.py y app/auth/auth_logic.py
except ImportError:
    try:
        import db # Si db.py y la carpeta auth están dentro de app y app está en PYTHONPATH, o si están en el mismo nivel.
    except ImportError:
        print("Error: No se pudo importar el módulo db.py. Asegúrate de que esté en la ruta correcta.")
        db = None


def generate_salt():
    """Genera un salt aleatorio de 16 bytes."""
    return os.urandom(16)

def hash_password(password, salt):
    """
    Genera el hash de una contraseña usando un salt (SHA-256).
    Args:
        password (str): La contraseña en texto plano.
        salt (bytes): El salt. Si es un string hexadecimal, se convertirá.
    Returns:
        str: El hash de la contraseña en formato hexadecimal.
    """
    if isinstance(salt, str): # Si el salt viene de la DB como hex
        try:
            salt_bytes = bytes.fromhex(salt)
        except ValueError:
            print("Error: Formato de salt (hex string) inválido.")
            # Podrías levantar una excepción específica o devolver None
            # dependiendo de cómo quieras manejar este error.
            raise ValueError("Formato de salt hexadecimal inválido")
    elif isinstance(salt, bytes):
        salt_bytes = salt
    else:
        raise TypeError("El salt debe ser bytes o un string hexadecimal.")

    # Asegurarse de que la contraseña sea bytes
    password_bytes = password.encode('utf-8')
    
    salted_password = salt_bytes + password_bytes
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return hashed_password

def verify_employee_credentials(employee_id, password_attempt):
    """
    Verifica las credenciales de un empleado contra la base de datos.
    Args:
        employee_id (str): El ID del empleado que intenta iniciar sesión.
        password_attempt (str): La contraseña ingresada por el usuario.
    Returns:
        dict: Un diccionario con los datos del empleado (id_empleado, nombre, apellido, rol)
              si las credenciales son válidas y el empleado está activo.
              None en caso contrario o si hay un error.
    """
    if not db:
        print("Error: El módulo de base de datos no está disponible en auth_logic.")
        return None

    query = "SELECT id_empleado, nombre, apellido, rol, hash_contrasena, salt FROM Empleados WHERE id_empleado = %s AND estado = 'activo'"
    
    employee_data = db.fetch_one(query, (employee_id,))

    if employee_data:
        stored_hash = employee_data.get("hash_contrasena")
        salt_hex_from_db = employee_data.get("salt") # El salt se almacena como VARCHAR (hexadecimal)

        if not stored_hash or not salt_hex_from_db:
            print(f"Error: No se encontró hash o salt para el empleado {employee_id}.")
            return None
        
        try:
            # Hashear la contraseña ingresada con el salt recuperado de la BD
            attempted_hash = hash_password(password_attempt, salt_hex_from_db)
        except ValueError as e: # Captura el error de formato de salt desde hash_password
            print(f"Error al procesar el salt para {employee_id}: {e}")
            return None
        except TypeError as e:
            print(f"Error de tipo con el salt para {employee_id}: {e}")
            return None


        if attempted_hash == stored_hash:
            print(f"Autenticación exitosa para {employee_id}. Rol: {employee_data.get('rol')}")
            return {
                "id_empleado": employee_data.get("id_empleado"),
                "nombre": employee_data.get("nombre"),
                "apellido": employee_data.get("apellido"),
                "rol": employee_data.get("rol")
            }
        else:
            print(f"Contraseña incorrecta para {employee_id}.")
            return None
    else:
        print(f"Empleado {employee_id} no encontrado o inactivo.")
        return None

def create_employee_secure(employee_data_with_plain_password):
    """
    Crea un nuevo empleado con contraseña hasheada y salt.
    Esta función es para ser usada por un administrador.
    Args:
        employee_data_with_plain_password (dict): Un diccionario con los datos del empleado,
                                                  incluyendo una clave 'contrasena_plana'.
                                                  Ej: {'id_empleado': 'E001', ..., 'contrasena_plana': 'pass123'}
    Returns:
        int or None: El ID de la última fila insertada (si aplica y es devuelto por db.execute_query)
                     o el número de filas afectadas. None si hay un error.
    """
    if not db:
        print("Error: El módulo de base de datos no está disponible en auth_logic para crear empleado.")
        return None

    # Copiar el diccionario para no modificar el original si se pasa por referencia
    data_copy = employee_data_with_plain_password.copy()
    plain_password = data_copy.pop('contrasena_plana', None)

    if not plain_password:
        print("Error: La 'contrasena_plana' es requerida para crear un empleado.")
        return None

    new_salt_bytes = generate_salt()
    new_hash = hash_password(plain_password, new_salt_bytes) # Pasa los bytes del salt
    
    # Guardar el salt como string hexadecimal en la base de datos
    new_salt_hex = new_salt_bytes.hex()

    query = """
    INSERT INTO Empleados (id_empleado, nombre, apellido, rol, hash_contrasena, salt, estado)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    # Asegúrate de que todos los campos necesarios estén en data_copy
    params = (
        data_copy.get('id_empleado'),
        data_copy.get('nombre'),
        data_copy.get('apellido'),
        data_copy.get('rol'),
        new_hash,
        new_salt_hex,
        data_copy.get('estado', 'activo')
    )

    # Validar que los parámetros no sean None si son obligatorios en la BD
    if not all([params[0], params[1], params[2], params[3]]): # id, nombre, apellido, rol
        print("Error: Faltan datos obligatorios del empleado (ID, nombre, apellido, rol).")
        return None

    try:
        result = db.execute_query(query, params)
        if result is not None:
            print(f"Empleado {data_copy.get('id_empleado')} creado/actualizado exitosamente (resultado: {result}).")
            return result 
        else:
            # Esto podría suceder si db.execute_query devuelve None en caso de error no capturado por excepción
            print(f"No se pudo crear el empleado {data_copy.get('id_empleado')} (db.execute_query devolvió None).")
            return None
    except Exception as e:
        print(f"Excepción al intentar crear empleado en la base de datos: {e}")
        return None

if __name__ == '__main__':
    # --- PRUEBAS (SOLO PARA DESARROLLO) ---
    print("Probando lógica de autenticación (auth_logic.py)...")

    if db:
        test_employee_id = "TEST_AUTH01"
        test_password = "securePassword123!"

        # 1. Intentar crear un empleado de prueba (simulando que un admin lo hace)
        existing_test_employee = db.fetch_one("SELECT id_empleado FROM Empleados WHERE id_empleado = %s", (test_employee_id,))
        
        if not existing_test_employee:
            print(f"\nCreando empleado de prueba '{test_employee_id}'...")
            test_employee_data = {
                'id_empleado': test_employee_id,
                'nombre': 'UsuarioAuth',
                'apellido': 'DePrueba',
                'rol': 'administrador',
                'contrasena_plana': test_password,
                'estado': 'activo'
            }
            creation_result = create_employee_secure(test_employee_data)
            if creation_result is not None: # Podría ser 0 para INSERT si lastrowid no es aplicable
                print(f"Empleado de prueba '{test_employee_id}' procesado. Resultado: {creation_result}")
            else:
                print(f"Fallo al procesar empleado de prueba '{test_employee_id}'. Verifica los logs.")
        else:
            print(f"Empleado de prueba '{test_employee_id}' ya existe, no se intentó crear.")

        # 2. Intentar autenticar al empleado de prueba
        print(f"\nIntentando autenticar a '{test_employee_id}' con contraseña correcta...")
        auth_result_ok = verify_employee_credentials(test_employee_id, test_password)
        if auth_result_ok:
            print(f"Resultado de autenticación OK: {auth_result_ok}")
        else:
            print(f"Fallo en autenticación OK para '{test_employee_id}' (inesperado si el empleado fue creado y la contraseña es correcta).")

        print(f"\nIntentando autenticar a '{test_employee_id}' con contraseña incorrecta...")
        auth_result_fail = verify_employee_credentials(test_employee_id, "wrongpassword")
        if not auth_result_fail:
            print("Resultado de autenticación FALLIDA: Correcto, la contraseña era incorrecta.")
        else:
            print("Fallo en autenticación FALLIDA (inesperado).")

        print(f"\nIntentando autenticar a un empleado inexistente...")
        auth_result_nonexistent = verify_employee_credentials("NOEXISTE_XYZ", "anypassword")
        if not auth_result_nonexistent:
            print("Resultado de autenticación INEXISTENTE: Correcto, el empleado no existe.")
        else:
            print("Fallo en autenticación INEXISTENTE (inesperado).")
    else:
        print("No se pueden ejecutar las pruebas de auth_logic.py porque el módulo db no está cargado.")

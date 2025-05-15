# app/models/employee_model.py

# Ajusta las rutas de importación según tu estructura de proyecto.
# Si este archivo está en app/models/ y db.py está en app/
# y auth_logic.py está en app/auth/
try:
    from .. import db # Para db.py en app/
    from ..auth import auth_logic # Para auth_logic.py en app/auth/
except ImportError:
    # Fallback si la estructura es diferente o se ejecuta directamente y 'app' está en PYTHONPATH
    try:
        import db
        from auth import auth_logic # Asumiendo que la carpeta 'auth' está en el mismo nivel que este archivo o en PYTHONPATH
    except ImportError:
        print("Error: No se pudieron importar los módulos db.py o auth_logic.py. Verifica tu estructura y PYTHONPATH.")
        db = None
        auth_logic = None

def create_employee(employee_data_dict):
    """
    Crea un nuevo empleado en la base de datos.
    Utiliza auth_logic.create_employee_secure para el manejo de contraseña.

    Args:
        employee_data_dict (dict): Un diccionario con los datos del empleado.
            Debe incluir: 'id_empleado', 'nombre', 'apellido', 'rol',
                          'contrasena_plana', y opcionalmente 'estado'.
                          La clave 'contrasena_plana' es la que espera auth_logic.create_employee_secure.
    Returns:
        El resultado de db.execute_query (ej. ID de fila insertada o contador) o None si falla.
    """
    if not auth_logic or not db:
        print("Error: Los módulos db o auth_logic no están disponibles en employee_model.")
        return None
    
    # Validación básica de datos requeridos
    required_fields = ['id_empleado', 'nombre', 'apellido', 'rol', 'contrasena_plana']
    for field in required_fields:
        if field not in employee_data_dict or not employee_data_dict[field]:
            # Los mensajes de error para el usuario final deberían manejarse idealmente en la capa de la vista/controlador,
            # pero una verificación aquí es una buena práctica defensiva.
            print(f"Error de validación en el modelo: El campo '{field}' es obligatorio para crear un empleado.")
            return None # O podrías levantar una excepción personalizada
            
    # El estado por defecto es 'activo' si no se proporciona
    if 'estado' not in employee_data_dict:
        employee_data_dict['estado'] = 'activo' # 'activo' es el término en español usado en la BD

    # Llama a la función de auth_logic que maneja el hash y salt
    return auth_logic.create_employee_secure(employee_data_dict)

def get_employee_by_id(employee_id_value):
    """
    Obtiene un empleado por su ID.

    Args:
        employee_id_value (str): El ID del empleado a buscar.

    Returns:
        dict: Los datos del empleado si se encuentra, None en caso contrario.
              Los datos devueltos son: id_empleado, nombre, apellido, rol, estado.
    """
    if not db: return None
    # Los nombres de las columnas en la consulta SELECT están en español para coincidir con el esquema de la BD
    query_string = "SELECT id_empleado, nombre, apellido, rol, estado FROM Empleados WHERE id_empleado = %s"
    return db.fetch_one(query_string, (employee_id_value,))

def get_all_employees_list():
    """
    Obtiene una lista de todos los empleados.
    Excluye hash_contrasena y salt por seguridad y porque no suelen ser necesarios para listar.

    Returns:
        list: Una lista de diccionarios, cada uno representando un empleado.
              Devuelve una lista vacía si no hay empleados.
              None si hay un error en la consulta.
    """
    if not db: return None
    query_string = "SELECT id_empleado, nombre, apellido, rol, estado FROM Empleados ORDER BY nombre, apellido"
    return db.fetch_all(query_string)

def update_employee_details(employee_id_value, data_to_update_dict):
    """
    Actualiza la información de un empleado existente (excluyendo la contraseña).
    Para actualizar la contraseña, se debería usar una función separada que involucre auth_logic.

    Args:
        employee_id_value (str): El ID del empleado a actualizar.
        data_to_update_dict (dict): Un diccionario con los campos a actualizar y sus nuevos valores.
                                   Campos permitidos (claves del diccionario): 'nombre', 'apellido', 'rol', 'estado'.
                                   Estos son los nombres de las columnas en la BD.
    Returns:
        int: El número de filas afectadas, o None si hay un error. 0 si no hay datos válidos para actualizar.
    """
    if not db: return None
    if not data_to_update_dict:
        print("Modelo: No se proporcionaron datos para actualizar.")
        return 0 # No hay nada que hacer

    # Campos permitidos para actualización directa (nombres de columnas en la BD)
    allowed_fields_for_update = {'nombre', 'apellido', 'rol', 'estado'} 
    
    set_clauses_list = []
    parameters_list = []

    for key, value in data_to_update_dict.items():
        if key in allowed_fields_for_update:
            # Usar acentos graves (backticks) para los nombres de campo es una buena práctica en SQL,
            # especialmente si los nombres de campo pudieran ser palabras clave de SQL.
            set_clauses_list.append(f"`{key}` = %s") 
            parameters_list.append(value)
        else:
            print(f"Advertencia en el modelo: El campo '{key}' no se puede actualizar directamente o no es permitido por esta función.")

    if not set_clauses_list:
        print("Modelo: Ningún campo válido para actualizar fue proporcionado.")
        return 0 # No se construyó ninguna cláusula SET válida

    # Construye la consulta final
    query_string = f"UPDATE Empleados SET {', '.join(set_clauses_list)} WHERE id_empleado = %s"
    parameters_list.append(employee_id_value) # Añade el ID del empleado al final de la lista de parámetros
    
    return db.execute_query(query_string, tuple(parameters_list))

def update_employee_status_only(employee_id_value, new_status_value):
    """
    Actualiza únicamente el estado de un empleado (ej. 'activo', 'inactivo').

    Args:
        employee_id_value (str): El ID del empleado.
        new_status_value (str): El nuevo estado para el empleado ('activo' o 'inactivo').

    Returns:
        int: El número de filas afectadas, o None si hay un error o el estado no es válido.
    """
    if not db: return None
    # Los valores de estado permitidos ('activo', 'inactivo') están en español según la BD
    if new_status_value not in ('activo', 'inactivo'): 
        print(f"Error en el modelo: Estado '{new_status_value}' no es válido.")
        return None # O podrías devolver 0 o levantar una excepción
        
    query_string = "UPDATE Empleados SET estado = %s WHERE id_empleado = %s"
    return db.execute_query(query_string, (new_status_value, employee_id_value))

def delete_employee_by_id_permanently(employee_id_value):
    """
    Elimina un empleado de la base de datos de forma permanente.
    ¡PRECAUCIÓN! Esta es una operación destructiva. En muchos sistemas,
    se prefiere cambiar el estado a 'eliminado' o 'inactivo_permanente'.

    Args:
        employee_id_value (str): El ID del empleado a eliminar.

    Returns:
        int: El número de filas afectadas, o None si hay un error.
    """
    if not db: return None
    # Consideraciones:
    # - Podrías añadir una confirmación o lógica adicional aquí si fuera necesario.
    # - Antes de eliminar, podrías verificar si el empleado tiene dependencias
    #   (ej. si es mesero en comandas abiertas), aunque esto puede
    #   manejarse con restricciones FOREIGN KEY y ON DELETE en la BD.

    query_string = "DELETE FROM Empleados WHERE id_empleado = %s"
    return db.execute_query(query_string, (employee_id_value,))

# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    # Esta sección se ejecuta solo cuando el script se corre directamente (ej. python -m app.models.employee_model)
    # Es útil para probar la lógica del modelo de forma aislada.
    if not db or not auth_logic:
        print("No se pueden ejecutar las pruebas del modelo de empleados: los módulos db o auth_logic no están cargados.")
    else:
        print("Probando el Modelo de Empleados (employee_model.py)...")

        # ID de empleado para pruebas
        test_id = "EMP_MODEL_TEST01" 
        
        # 1. Crear un nuevo empleado
        print(f"\n--- Intentando crear empleado: {test_id} ---")
        # Primero, intentar eliminarlo si existe de una prueba anterior para evitar errores de clave duplicada
        delete_employee_by_id_permanently(test_id) 
        
        new_data = {
            'id_empleado': test_id,
            'nombre': 'Test Employee',    # Nombre en inglés para la prueba
            'apellido': 'Model',         # Apellido en inglés
            'rol': 'mesero',             # Rol en español (debe coincidir con los valores permitidos en la BD)
            'contrasena_plana': 'TestPass123!', # Contraseña en texto plano para la creación
            'estado': 'activo'           # Estado en español
        }
        creation_outcome = create_employee(new_data)
        if creation_outcome is not None: # db.execute_query puede devolver 0 si no hay autoincremento y es un INSERT
            print(f"Procesamiento de creación para {test_id} finalizado (resultado: {creation_outcome}).")
            # Verificar si realmente se creó
            created_emp = get_employee_by_id(test_id)
            if created_emp:
                print(f"Verificación post-creación - Empleado encontrado: {created_emp}")
            else:
                print(f"Verificación post-creación - Empleado {test_id} NO encontrado. La creación pudo haber fallado.")
        else:
            print(f"Fallo al crear empleado {test_id} (el modelo devolvió None).")

        # 2. Listar todos los empleados
        print("\n--- Listando todos los empleados ---")
        all_emps = get_all_employees_list()
        if all_emps is not None: # Puede ser una lista vacía si no hay empleados
            if all_emps:
                for emp in all_emps:
                    print(emp)
            else:
                print("No hay empleados para listar.")
        else: # all_emps es None, lo que indica un error en la consulta
            print("Error al listar empleados (el modelo devolvió None).")

        # 3. Obtener el empleado creado (si la creación fue exitosa)
        print(f"\n--- Obteniendo empleado: {test_id} ---")
        employee_details = get_employee_by_id(test_id)
        if employee_details:
            print(f"Detalles encontrados: {employee_details}")
        else:
            print(f"Empleado {test_id} no encontrado (o hubo un error en la obtención, o no se creó).")

        # 4. Actualizar información del empleado (si se encontró)
        if employee_details: # Solo intentar actualizar si el empleado existe
            print(f"\n--- Actualizando empleado: {test_id} ---")
            update_payload = {
                'nombre': 'Test Employee Updated', # Nuevo nombre en inglés
                'rol': 'cocinero'                 # Nuevo rol en español
            }
            updated_count = update_employee_details(test_id, update_payload)
            if updated_count is not None:
                print(f"Resultado de la actualización (filas afectadas): {updated_count}")
                if updated_count > 0:
                    updated_emp_check = get_employee_by_id(test_id)
                    print(f"Datos después de actualizar: {updated_emp_check}")
                elif updated_count == 0:
                    print(f"Ninguna fila fue actualizada para {test_id}. ¿El ID es correcto y los datos son diferentes?")
            else:
                print(f"Error al actualizar empleado {test_id} (el modelo devolvió None).")

        # 5. Actualizar estado del empleado (si se encontró)
        if employee_details: # Solo intentar actualizar si el empleado existe
            print(f"\n--- Actualizando estado de {test_id} a 'inactivo' ---")
            status_update_count = update_employee_status_only(test_id, 'inactivo') # 'inactivo' en español
            if status_update_count is not None:
                print(f"Resultado del cambio de estado (filas afectadas): {status_update_count}")
                if status_update_count > 0:
                    status_check_emp = get_employee_by_id(test_id)
                    print(f"Datos después de cambiar estado: {status_check_emp}")
            else:
                print(f"Error al actualizar estado de {test_id} (el modelo devolvió None).")

        # 6. Intentar eliminar el empleado (opcional, descomentar para probar la eliminación)
        # if employee_details: # Solo intentar eliminar si el empleado existe
        #     print(f"\n--- Eliminando empleado: {test_id} ---")
        #     deleted_count = delete_employee_by_id_permanently(test_id)
        #     if deleted_count is not None:
        #         print(f"Resultado de la eliminación (filas afectadas): {deleted_count}")
        #         if deleted_count > 0:
        #             deleted_emp_check = get_employee_by_id(test_id)
        #             if not deleted_emp_check:
        #                 print(f"Empleado {test_id} eliminado correctamente.")
        #             else:
        #                 print(f"Error: Empleado {test_id} aún encontrado después del intento de eliminación.")
        #     else:
        #         print(f"Error al eliminar empleado {test_id} (el modelo devolvió None).")
        
        print("\nPruebas del Modelo de Empleados completadas.")
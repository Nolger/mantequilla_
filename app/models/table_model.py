# app/models/table_model.py

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from .. import db # Si db.py está en app/
except ImportError:
    try:
        import db # Si está en el mismo nivel o app está en PYTHONPATH
    except ImportError:
        print("Error: No se pudo importar el módulo db.py en table_model.py.")
        db = None

def create_table(table_data_dict):
    """
    Crea una nueva mesa en la base de datos.

    Args:
        table_data_dict (dict): Un diccionario con los datos de la mesa.
            Debe incluir: 'id_mesa', 'capacidad'.
            Opcional: 'ubicacion', 'estado' (defecto 'libre'), 
                      'pos_x' (defecto 50), 'pos_y' (defecto 50).
    Returns:
        El resultado de db.execute_query o None si falla.
    """
    if not db:
        print("Error: Módulo db no disponible en table_model.")
        return None

    required_fields = ['id_mesa', 'capacidad']
    for field in required_fields:
        if field not in table_data_dict or not table_data_dict[field]:
            print(f"Error de validación en el modelo: El campo '{field}' es obligatorio para crear una mesa.")
            return None
    
    # Valores por defecto si no se proporcionan
    table_data_dict.setdefault('estado', 'libre')
    table_data_dict.setdefault('ubicacion', '') # Ubicación puede ser opcional o tener un valor por defecto
    table_data_dict.setdefault('pos_x', 50)
    table_data_dict.setdefault('pos_y', 50)

    query_string = """
    INSERT INTO Mesa (id_mesa, capacidad, estado, ubicacion, pos_x, pos_y)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        table_data_dict['id_mesa'],
        table_data_dict['capacidad'],
        table_data_dict['estado'],
        table_data_dict['ubicacion'],
        table_data_dict['pos_x'],
        table_data_dict['pos_y']
    )
    return db.execute_query(query_string, params)

def get_tables_status_summary():
    """
    Obtiene un resumen del estado de todas las mesas.
    Returns:
        dict: Un diccionario con el conteo de mesas por estado (ej. {'libre': 5, 'ocupada': 2}),
              o None si hay un error.
    """
    if not db:
        print("Error en table_model: Módulo db no disponible.")
        return None
    query_string = "SELECT estado, COUNT(*) as cantidad FROM Mesa GROUP BY estado"
    results = db.fetch_all(query_string)
    if results:
        summary = {row['estado']: row['cantidad'] for row in results}
        # Asegurar que todos los estados posibles estén presentes, incluso si son 0
        all_statuses = ['libre', 'ocupada', 'reservada', 'mantenimiento']
        for status_key in all_statuses:
            if status_key not in summary:
                summary[status_key] = 0
        return summary
    elif results == []: # No hay mesas
        return {'libre': 0, 'ocupada': 0, 'reservada': 0, 'mantenimiento': 0}
    return None # Error en la consulta

def get_table_by_id(table_id_value):
    """
    Obtiene una mesa por su ID.

    Args:
        table_id_value (str): El ID de la mesa a buscar.

    Returns:
        dict: Los datos de la mesa si se encuentra, None en caso contrario.
    """
    if not db: return None
    query_string = "SELECT id_mesa, capacidad, estado, ubicacion, pos_x, pos_y FROM Mesa WHERE id_mesa = %s"
    return db.fetch_one(query_string, (table_id_value,))

def get_all_tables_list():
    """
    Obtiene una lista de todas las mesas.

    Returns:
        list: Una lista de diccionarios, cada uno representando una mesa.
              Devuelve una lista vacía si no hay mesas.
              None si hay un error en la consulta.
    """
    if not db: return None
    query_string = "SELECT id_mesa, capacidad, estado, ubicacion, pos_x, pos_y FROM Mesa ORDER BY id_mesa"
    return db.fetch_all(query_string)

def update_table_details(table_id_value, data_to_update_dict):
    """
    Actualiza la información de una mesa existente.

    Args:
        table_id_value (str): El ID de la mesa a actualizar.
        data_to_update_dict (dict): Un diccionario con los campos a actualizar y sus nuevos valores.
                                   Campos permitidos: 'capacidad', 'ubicacion', 'pos_x', 'pos_y', 'estado'.
    Returns:
        int: El número de filas afectadas, o None si hay un error. 0 si no hay datos válidos.
    """
    if not db: return None
    if not data_to_update_dict:
        print("Modelo: No se proporcionaron datos para actualizar la mesa.")
        return 0

    allowed_fields_for_update = {'capacidad', 'estado', 'ubicacion', 'pos_x', 'pos_y'}
    
    set_clauses_list = []
    parameters_list = []

    for key, value in data_to_update_dict.items():
        if key in allowed_fields_for_update:
            set_clauses_list.append(f"`{key}` = %s")
            parameters_list.append(value)
        else:
            print(f"Advertencia en el modelo (mesas): El campo '{key}' no es actualizable por esta función.")

    if not set_clauses_list:
        print("Modelo (mesas): Ningún campo válido para actualizar fue proporcionado.")
        return 0

    query_string = f"UPDATE Mesa SET {', '.join(set_clauses_list)} WHERE id_mesa = %s"
    parameters_list.append(table_id_value)
    
    return db.execute_query(query_string, tuple(parameters_list))

def update_table_status(table_id_value, new_status_value):
    """
    Actualiza únicamente el estado de una mesa.

    Args:
        table_id_value (str): El ID de la mesa.
        new_status_value (str): El nuevo estado ('libre', 'ocupada', 'reservada', 'mantenimiento').

    Returns:
        int: El número de filas afectadas, o None si hay un error o el estado no es válido.
    """
    if not db: return None
    valid_statuses = ['libre', 'ocupada', 'reservada', 'mantenimiento']
    if new_status_value not in valid_statuses:
        print(f"Error en el modelo (mesas): Estado '{new_status_value}' no es válido.")
        return None
        
    query_string = "UPDATE Mesa SET estado = %s WHERE id_mesa = %s"
    return db.execute_query(query_string, (new_status_value, table_id_value))

def delete_table_by_id(table_id_value):
    """
    Elimina una mesa de la base de datos de forma permanente.

    Args:
        table_id_value (str): El ID de la mesa a eliminar.

    Returns:
        int: El número de filas afectadas, o None si hay un error.
    """
    if not db: return None
    # Considerar si hay comandas abiertas para esta mesa antes de permitir la eliminación.
    # Esta lógica podría estar aquí o en una capa de servicio si la aplicación crece.
    # Por ahora, se permite la eliminación directa.
    query_string = "DELETE FROM Mesa WHERE id_mesa = %s"
    return db.execute_query(query_string, (table_id_value,))

# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    if not db:
        print("No se pueden ejecutar las pruebas del modelo de mesas: módulo db no cargado.")
    else:
        print("Probando el Modelo de Mesas (table_model.py)...")

        test_table_id1 = "M01_PYTEST_TABLE" # ID específico para pruebas
        test_table_id2 = "M02_PYTEST_TABLE"

        # 0. Limpieza previa (opcional, para asegurar un estado limpio para las pruebas)
        print(f"\n--- Limpiando mesas de prueba {test_table_id1}, {test_table_id2} si existen ---")
        delete_table_by_id(test_table_id1)
        delete_table_by_id(test_table_id2)

        # 1. Crear nuevas mesas
        print(f"\n--- Creando mesa {test_table_id1} ---")
        table1_data = {
            'id_mesa': test_table_id1,
            'capacidad': 4,
            'ubicacion': 'Ventana Izquierda (Prueba)',
            'pos_x': 100,
            'pos_y': 100
        }
        result1 = create_table(table1_data)
        if result1 is not None:
            print(f"Mesa {test_table_id1} procesada (resultado: {result1}).")
            created_table1 = get_table_by_id(test_table_id1)
            print(f"Verificación: {created_table1}")
        else:
            print(f"Fallo al crear mesa {test_table_id1}.")

        print(f"\n--- Creando mesa {test_table_id2} ---")
        table2_data = {
            'id_mesa': test_table_id2,
            'capacidad': 2,
            'estado': 'reservada', 
            'pos_x': 200,
            'pos_y': 150,
            'ubicacion': 'Terraza (Prueba)'
        }
        result2 = create_table(table2_data)
        if result2 is not None:
            print(f"Mesa {test_table_id2} procesada (resultado: {result2}).")
            created_table2 = get_table_by_id(test_table_id2)
            print(f"Verificación: {created_table2}")
        else:
            print(f"Fallo al crear mesa {test_table_id2}.")

        # 2. Listar todas las mesas
        print("\n--- Listando todas las mesas ---")
        all_tables = get_all_tables_list()
        if all_tables is not None:
            if all_tables:
                for tbl in all_tables:
                    print(tbl)
            else:
                print("No hay mesas para listar.")
        else:
            print("Error al listar mesas.")

        # 3. Obtener una mesa específica
        print(f"\n--- Obteniendo mesa {test_table_id1} ---")
        table_details = get_table_by_id(test_table_id1)
        if table_details:
            print(f"Detalles encontrados: {table_details}")
        else:
            print(f"Mesa {test_table_id1} no encontrada o error.")

        # 4. Actualizar detalles de una mesa
        if table_details: 
            print(f"\n--- Actualizando mesa {test_table_id1} ---")
            update_payload = {
                'capacidad': 5,
                'ubicacion': 'Ventana Principal (Actualizada Prueba)',
                'pos_x': 110,
                'pos_y': 105,
                'estado': 'ocupada'
            }
            update_count = update_table_details(test_table_id1, update_payload)
            if update_count is not None:
                print(f"Resultado de la actualización (filas afectadas): {update_count}")
                if update_count > 0:
                    updated_table_check = get_table_by_id(test_table_id1)
                    print(f"Datos después de actualizar: {updated_table_check}")
            else:
                print(f"Error al actualizar mesa {test_table_id1}.")
        
        # 5. Actualizar solo el estado de una mesa
        if get_table_by_id(test_table_id2): 
            print(f"\n--- Actualizando estado de {test_table_id2} a 'libre' ---")
            status_update_count = update_table_status(test_table_id2, 'libre')
            if status_update_count is not None:
                print(f"Resultado del cambio de estado (filas afectadas): {status_update_count}")
                if status_update_count > 0:
                    status_check_table = get_table_by_id(test_table_id2)
                    print(f"Datos después de cambiar estado: {status_check_table}")
            else:
                print(f"Error al actualizar estado de {test_table_id2}.")

        # 6. Eliminar una mesa (opcional, descomentar para probar)
        # if get_table_by_id(test_table_id1):
        #     print(f"\n--- Eliminando mesa {test_table_id1} ---")
        #     deleted_count = delete_table_by_id(test_table_id1)
        #     if deleted_count is not None:
        #         print(f"Resultado de la eliminación (filas afectadas): {deleted_count}")
        #         if deleted_count > 0:
        #             deleted_table_check = get_table_by_id(test_table_id1)
        #             if not deleted_table_check:
        #                 print(f"Mesa {test_table_id1} eliminada correctamente.")
        #             else:
        #                 print(f"Error: Mesa {test_table_id1} aún encontrada después del intento de eliminación.")
        #     else:
        #         print(f"Error al eliminar mesa {test_table_id1}.")
        
        print("\nPruebas del Modelo de Mesas completadas.")

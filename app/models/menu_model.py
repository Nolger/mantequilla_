# app/models/menu_model.py
import datetime

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from .. import db # Si db.py está en app/
except ImportError:
    try:
        import db # Si está en el mismo nivel o app está en PYTHONPATH
    except ImportError:
        print("Error: No se pudo importar el módulo db.py en menu_model.py.")
        db = None

def create_dish(dish_data_dict):
    """
    Crea un nuevo plato en el menú.
    La receta se manejará por separado usando recipe_model.
    Args:
        dish_data_dict (dict): Datos del plato. Debe incluir:
            'id_plato', 'nombre_plato', 'categoria', 'precio_venta'.
            Opcional: 'descripcion', 'tiempo_preparacion_min', 'activo' (defecto True).
    Returns:
        Resultado de db.execute_query o None.
    """
    if not db:
        print("Error: Módulo db no disponible en menu_model.")
        return None
    
    required_fields = ['id_plato', 'nombre_plato', 'categoria', 'precio_venta']
    for field in required_fields:
        if field not in dish_data_dict or not dish_data_dict[field]:
            print(f"Error de validación: Falta el campo '{field}' para el plato.")
            return None
    
    query_string = """
    INSERT INTO Plato (id_plato, nombre_plato, descripcion, categoria, 
                       tiempo_preparacion_min, activo, precio_venta, imagen_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        dish_data_dict['id_plato'],
        dish_data_dict['nombre_plato'],
        dish_data_dict.get('descripcion', ''), # Descripción por defecto vacía
        dish_data_dict['categoria'],
        dish_data_dict.get('tiempo_preparacion_min'), # Puede ser None si no se especifica
        dish_data_dict.get('activo', True), # Activo por defecto
        dish_data_dict['precio_venta'],
        dish_data_dict.get('imagen_url') # Puede ser None
    )
    return db.execute_query(query_string, params)

def get_dish_by_id(dish_id_value):
    """
    Obtiene un plato específico por su ID.
    Args:
        dish_id_value (str): El ID del plato a buscar.
    Returns:
        dict: Los datos completos del plato si se encuentra, None en caso contrario.
    """
    if not db:
        print("Error: Módulo db no disponible en menu_model.")
        return None
    
    query_string = "SELECT * FROM Plato WHERE id_plato = %s"
    return db.fetch_one(query_string, (dish_id_value,))

def get_all_dishes_list():
    """
    Obtiene una lista de todos los platos, activos e inactivos.
    Returns:
        list: Lista de diccionarios, cada uno representando un plato.
    """
    if not db: return None
    query_string = "SELECT * FROM Plato ORDER BY categoria, nombre_plato"
    return db.fetch_all(query_string)


def get_active_dishes():
    """
    Obtiene una lista de todos los platos activos del menú.
    Returns:
        list: Una lista de diccionarios, cada uno representando un plato activo
              (id_plato, nombre_plato, precio_venta, categoria).
              Devuelve una lista vacía si no hay platos activos.
              None si hay un error en la consulta.
    """
    if not db:
        print("Error: Módulo db no disponible en menu_model.")
        return None
    
    query_string = """
        SELECT id_plato, nombre_plato, precio_venta, categoria 
        FROM Plato 
        WHERE activo = TRUE 
        ORDER BY categoria, nombre_plato
    """
    return db.fetch_all(query_string)

def update_dish_details(dish_id_value, data_to_update_dict):
    """
    Actualiza la información de un plato existente.
    Args:
        dish_id_value (str): El ID del plato a actualizar.
        data_to_update_dict (dict): Campos a actualizar.
            Campos permitidos: 'nombre_plato', 'descripcion', 'categoria', 
                               'tiempo_preparacion_min', 'activo', 'precio_venta', 'imagen_url'.
    Returns:
        int: Número de filas afectadas o None.
    """
    if not db: return None
    if not data_to_update_dict:
        print("Modelo: No se proporcionaron datos para actualizar el plato.")
        return 0

    allowed_fields = {'nombre_plato', 'descripcion', 'categoria', 
                      'tiempo_preparacion_min', 'activo', 'precio_venta', 'imagen_url'}
    
    set_clauses_list = []
    parameters_list = []

    for key, value in data_to_update_dict.items():
        if key in allowed_fields:
            set_clauses_list.append(f"`{key}` = %s")
            parameters_list.append(value)
        else:
            print(f"Advertencia en menu_model: El campo '{key}' no es actualizable para platos.")

    if not set_clauses_list:
        print("Modelo (menu): Ningún campo válido para actualizar fue proporcionado.")
        return 0

    query_string = f"UPDATE Plato SET {', '.join(set_clauses_list)} WHERE id_plato = %s"
    parameters_list.append(dish_id_value)
    
    return db.execute_query(query_string, tuple(parameters_list))

def delete_dish_by_id(dish_id_value):
    """
    Elimina un plato del menú.
    PRECAUCIÓN: Considerar dependencias (recetas, detalles de comanda).
    La BD debería tener ON DELETE RESTRICT o SET NULL en DetalleComanda.id_plato
    y ON DELETE CASCADE en Receta.id_plato si se desea eliminar recetas asociadas.
    Actualmente, setup_db.py tiene ON DELETE RESTRICT para DetalleComanda y CASCADE para Receta.
    Args:
        dish_id_value (str): El ID del plato a eliminar.
    Returns:
        int: Número de filas afectadas o None.
    """
    if not db: return None
    # Primero, podrías querer eliminar las entradas de receta asociadas si no hay ON DELETE CASCADE
    # O manejar el error si la eliminación del plato falla debido a restricciones FK.
    # Por ahora, se asume que la BD maneja las cascadas o restricciones.
    
    # Ejemplo de eliminación de recetas primero (si no hay ON DELETE CASCADE en Receta.id_plato):
    # from . import recipe_model # Importación local para evitar circular si no es necesario globalmente
    # recipe_items = recipe_model.get_recipe_for_dish(dish_id_value)
    # if recipe_items:
    #     for item in recipe_items:
    #         recipe_model.remove_ingredient_from_recipe(item['id_receta'])
    # print(f"Recetas asociadas al plato {dish_id_value} eliminadas (si existían).")

    query_string = "DELETE FROM Plato WHERE id_plato = %s"
    return db.execute_query(query_string, (dish_id_value,))


# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    if not db:
        print("No se pueden ejecutar las pruebas del modelo de menú: módulo db no cargado.")
    else:
        print("Probando el Modelo de Menú (menu_model.py)...")

        test_dish_id_crud = "PLATO_CRUD_01"

        # 0. Limpieza previa
        print(f"\n--- Limpiando plato de prueba {test_dish_id_crud} si existe ---")
        # Para que delete funcione, primero se deberían eliminar las recetas si no hay ON DELETE CASCADE
        # O la BD debe estar configurada para permitirlo.
        # Por ahora, intentamos eliminar directamente. Si falla por FK, la prueba lo indicará.
        delete_dish_by_id(test_dish_id_crud)


        # 1. Crear un nuevo plato
        print(f"\n--- Creando plato {test_dish_id_crud} ---")
        dish_data = {
            'id_plato': test_dish_id_crud,
            'nombre_plato': 'Hamburguesa Clásica (Prueba CRUD)',
            'categoria': 'principal',
            'precio_venta': 12.99,
            'descripcion': 'Carne de res, lechuga, tomate, queso.',
            'tiempo_preparacion_min': 15,
            'activo': True
        }
        creation_result = create_dish(dish_data)
        if creation_result is not None:
            print(f"Plato {test_dish_id_crud} creado/procesado (resultado: {creation_result}).")
            created_dish = get_dish_by_id(test_dish_id_crud)
            print(f"Verificación: {created_dish}")
        else:
            print(f"Fallo al crear plato {test_dish_id_crud}.")

        # 2. Listar todos los platos (incluyendo el nuevo)
        print("\n--- Listando todos los platos ---")
        all_dishes = get_all_dishes_list()
        if all_dishes is not None:
            if all_dishes:
                for d in all_dishes:
                    print(f"- {d['id_plato']}: {d['nombre_plato']} ({d['categoria']}), Activo: {d['activo']}, Precio: ${d.get('precio_venta', 0):.2f}")
            else:
                print("No hay platos para listar.")
        else:
            print("Error al listar platos.")

        # 3. Actualizar el plato
        if get_dish_by_id(test_dish_id_crud): # Solo si se creó
            print(f"\n--- Actualizando plato {test_dish_id_crud} ---")
            update_data = {
                'nombre_plato': 'Hamburguesa Clásica DELUXE (CRUD)',
                'precio_venta': 14.50,
                'activo': False
            }
            update_count = update_dish_details(test_dish_id_crud, update_data)
            if update_count is not None:
                print(f"Plato actualizado (filas afectadas: {update_count}).")
                updated_dish_check = get_dish_by_id(test_dish_id_crud)
                print(f"Datos después de actualizar: {updated_dish_check}")
            else:
                print(f"Fallo al actualizar plato {test_dish_id_crud}.")

        # 4. Listar platos activos (el de prueba debería estar inactivo ahora)
        print("\n--- Listando platos activos (después de inactivar el de prueba) ---")
        active_dishes = get_active_dishes()
        if active_dishes is not None:
            found_test_dish_active = any(d['id_plato'] == test_dish_id_crud for d in active_dishes)
            if not found_test_dish_active:
                print(f"Correcto: Plato {test_dish_id_crud} no encontrado en activos.")
            else:
                print(f"ERROR: Plato {test_dish_id_crud} aún está activo.")
            for dish in active_dishes:
                print(f"- {dish['nombre_plato']} ({dish['categoria']}): ${dish['precio_venta']:.2f}")
        else:
            print("Error al listar platos activos.")
        
        # 5. Eliminar el plato de prueba
        if get_dish_by_id(test_dish_id_crud):
            print(f"\n--- Eliminando plato {test_dish_id_crud} ---")
            # Nota: Si este plato tiene recetas asociadas y la FK Receta.id_plato no tiene ON DELETE CASCADE,
            # esta eliminación fallará si no se eliminan las recetas primero.
            # setup_db.py SÍ tiene ON DELETE CASCADE para Receta.id_plato.
            delete_count = delete_dish_by_id(test_dish_id_crud)
            if delete_count is not None:
                print(f"Plato eliminado (filas afectadas: {delete_count}).")
                deleted_dish_check = get_dish_by_id(test_dish_id_crud)
                if not deleted_dish_check:
                    print(f"Plato {test_dish_id_crud} eliminado correctamente.")
                else:
                    print(f"Error: Plato {test_dish_id_crud} aún encontrado después de eliminar.")
            else:
                print(f"Fallo al eliminar plato {test_dish_id_crud}. Puede ser por restricciones FK si tiene comandas asociadas y no hay SET NULL/CASCADE.")


        print("\nPruebas del Modelo de Menú (CRUD) completadas.")

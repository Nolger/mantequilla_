# app/models/recipe_model.py
import datetime

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from .. import db
    # No necesitamos menu_model o stock_model directamente aquí si solo manejamos la tabla Receta
    # y asumimos que los IDs de plato e ingrediente son válidos y existen.
    # Las validaciones de existencia de plato/ingrediente se harían antes de llamar a estas funciones.
except ImportError:
    try:
        import db
    except ImportError:
        print("Error: No se pudo importar el módulo db.py en recipe_model.py.")
        db = None

def add_ingredient_to_recipe(dish_id_value, ingredient_id_value, quantity_needed, unit_of_measure, instructions=""):
    """
    Añade un ingrediente a la receta de un plato.
    Args:
        dish_id_value (str): ID del plato.
        ingredient_id_value (str): ID del ingrediente (de la tabla Ingrediente).
        quantity_needed (float): Cantidad del ingrediente necesaria.
        unit_of_measure (str): Unidad de medida para esta cantidad en la receta (ej. 'g', 'ml', 'unidad').
        instructions (str, optional): Instrucciones específicas para este ingrediente en la receta.
    Returns:
        int: El ID de la entrada de receta creada (id_receta), o None si falla.
    """
    if not db: return None
    if quantity_needed <= 0:
        print("Error: La cantidad necesaria para la receta debe ser mayor que cero.")
        return None

    # Verificar si ya existe este ingrediente para este plato (UNIQUE (id_plato, id_ingrediente))
    # Esto se maneja mejor con una restricción UNIQUE en la BD, y aquí se captura el error si ocurre.
    
    query = """
    INSERT INTO Receta (id_plato, id_ingrediente, cantidad_necesaria, unidad_medida_receta, instrucciones_paso)
    VALUES (%s, %s, %s, %s, %s)
    """
    params = (dish_id_value, ingredient_id_value, quantity_needed, unit_of_measure, instructions)
    
    # db.execute_query devuelve el lastrowid para INSERTs, que es id_receta
    return db.execute_query(query, params)

def get_recipe_for_dish(dish_id_value):
    """
    Obtiene la lista de ingredientes y cantidades para la receta de un plato.
    Args:
        dish_id_value (str): El ID del plato.
    Returns:
        list: Lista de diccionarios, cada uno representando un ingrediente de la receta.
              Incluye id_receta, id_ingrediente, nombre_ingrediente (del producto), 
              cantidad_necesaria, unidad_medida_receta, instrucciones_paso.
              None si hay un error o no se encuentra la receta.
    """
    if not db: return None
    query = """
    SELECT r.id_receta, r.id_ingrediente, p.nombre AS nombre_ingrediente, 
           r.cantidad_necesaria, r.unidad_medida_receta, r.instrucciones_paso
    FROM Receta r
    JOIN Ingrediente i ON r.id_ingrediente = i.id_ingrediente
    JOIN Producto p ON i.id_producto = p.id_producto 
    WHERE r.id_plato = %s
    ORDER BY r.id_receta 
    """ 
    # OJO: El JOIN con Producto asume que Ingrediente.id_ingrediente es igual a Producto.id_producto
    # O que Ingrediente.id_producto es la FK correcta.
    # En nuestro setup_db, Ingrediente.id_producto es la FK, e id_ingrediente es la PK de Ingrediente.
    # Si id_ingrediente != id_producto, el JOIN debe ser cuidadoso.
    # Por simplicidad, en stock_model asumimos id_ingrediente = id_producto.
    # Si son diferentes, necesitarías un JOIN adicional o cambiar el campo 'nombre_ingrediente'.
    # Asumiendo que en stock_model.get_ingredient_by_id usamos p.nombre, aquí también es consistente.
    
    return db.fetch_all(query, (dish_id_value,))

def update_recipe_ingredient(recipe_entry_id, new_quantity=None, new_unit=None, new_instructions=None):
    """
    Actualiza un ingrediente específico en una receta.
    Args:
        recipe_entry_id (int): El ID de la entrada de receta (id_receta).
        new_quantity (float, optional): Nueva cantidad.
        new_unit (str, optional): Nueva unidad de medida.
        new_instructions (str, optional): Nuevas instrucciones.
    Returns:
        int: Número de filas afectadas o None si hay error.
    """
    if not db: return None
    
    fields_to_update = {}
    if new_quantity is not None:
        if new_quantity <= 0:
            print("Error: La nueva cantidad debe ser mayor que cero.")
            return None
        fields_to_update['cantidad_necesaria'] = new_quantity
    if new_unit is not None:
        fields_to_update['unidad_medida_receta'] = new_unit
    if new_instructions is not None: # Permite string vacío para borrar instrucciones
        fields_to_update['instrucciones_paso'] = new_instructions

    if not fields_to_update:
        print("No se proporcionaron campos para actualizar en la receta.")
        return 0

    set_clauses = [f"`{key}` = %s" for key in fields_to_update]
    params = list(fields_to_update.values())
    params.append(recipe_entry_id)

    query = f"UPDATE Receta SET {', '.join(set_clauses)} WHERE id_receta = %s"
    return db.execute_query(query, tuple(params))

def remove_ingredient_from_recipe(recipe_entry_id):
    """
    Elimina un ingrediente de una receta.
    Args:
        recipe_entry_id (int): El ID de la entrada de receta (id_receta) a eliminar.
    Returns:
        int: Número de filas afectadas o None si hay error.
    """
    if not db: return None
    query = "DELETE FROM Receta WHERE id_receta = %s"
    return db.execute_query(query, (recipe_entry_id,))

# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    if not db:
        print("No se pueden ejecutar las pruebas del modelo de recetas: módulo db no cargado.")
    else:
        print("Probando el Modelo de Recetas (recipe_model.py)...")

        # IDs de prueba (Asegúrate de que existan en tus tablas Plato e Ingrediente)
        # Para que esto funcione, necesitas:
        # 1. Un plato: ej. id_plato = 'PLATO_RECETA_01'
        # 2. Ingredientes (que también son productos): 
        #    ej. id_ingrediente = 'INGR_RECETA_A' (que es un id_producto)
        #    ej. id_ingrediente = 'INGR_RECETA_B'
        
        test_dish_id = "PLATO_RECETA_01"
        test_ingredient_id_A = "INGR_RECETA_A" # Debe existir en Producto y en Ingrediente
        test_ingredient_id_B = "INGR_RECETA_B" # Debe existir en Producto y en Ingrediente
        
        # --- Preparación (simulada, en un test real crearías estos datos si no existen) ---
        print(f"\n--- Asegurando existencia de plato '{test_dish_id}' e ingredientes '{test_ingredient_id_A}', '{test_ingredient_id_B}' ---")
        # db.execute_query("INSERT IGNORE INTO Plato (id_plato, nombre_plato, categoria, activo, precio_venta) VALUES (%s, %s, %s, TRUE, %s)",
        #                  (test_dish_id, 'Plato de Prueba Receta', 'principal', 15.0))
        # db.execute_query("INSERT IGNORE INTO Producto (id_producto, nombre, unidad_medida, costo_unitario, perecedero) VALUES (%s, %s, %s, %s, FALSE)",
        #                  (test_ingredient_id_A, 'Ingrediente A Receta', 'g', 0.1, False))
        # db.execute_query("INSERT IGNORE INTO Ingrediente (id_ingrediente, id_producto, cantidad_disponible) VALUES (%s, %s, %s)",
        #                  (test_ingredient_id_A, test_ingredient_id_A, 1000)) # Asume id_ingrediente = id_producto
        # db.execute_query("INSERT IGNORE INTO Producto (id_producto, nombre, unidad_medida, costo_unitario, perecedero) VALUES (%s, %s, %s, %s, FALSE)",
        #                  (test_ingredient_id_B, 'Ingrediente B Receta', 'ml', 0.05, False))
        # db.execute_query("INSERT IGNORE INTO Ingrediente (id_ingrediente, id_producto, cantidad_disponible) VALUES (%s, %s, %s)",
        #                  (test_ingredient_id_B, test_ingredient_id_B, 500))
        
        # Limpiar recetas previas para este plato de prueba
        print(f"Limpiando recetas antiguas para el plato {test_dish_id}...")
        old_recipe = get_recipe_for_dish(test_dish_id)
        if old_recipe:
            for item in old_recipe:
                remove_ingredient_from_recipe(item['id_receta'])
        
        # 1. Añadir ingredientes a la receta
        print(f"\n--- Añadiendo ingredientes a la receta del plato {test_dish_id} ---")
        # Verificar si los ingredientes existen antes de añadir a la receta
        # (Esto lo haría la lógica de la vista/controlador antes de llamar a add_ingredient_to_recipe)
        
        # Asumiendo que los IDs de ingredientes son válidos:
        recipe_entry_id1 = add_ingredient_to_recipe(test_dish_id, test_ingredient_id_A, 150, "g", "Mezclar bien")
        if recipe_entry_id1:
            print(f"Ingrediente {test_ingredient_id_A} añadido a la receta. ID Entrada Receta: {recipe_entry_id1}")
        else:
            print(f"Fallo al añadir {test_ingredient_id_A}. Asegúrate que el plato y el ingrediente existan y no haya duplicados en la receta.")

        recipe_entry_id2 = add_ingredient_to_recipe(test_dish_id, test_ingredient_id_B, 50, "ml")
        if recipe_entry_id2:
            print(f"Ingrediente {test_ingredient_id_B} añadido a la receta. ID Entrada Receta: {recipe_entry_id2}")
        else:
            print(f"Fallo al añadir {test_ingredient_id_B}.")

        # 2. Obtener la receta del plato
        print(f"\n--- Obteniendo receta del plato {test_dish_id} ---")
        recipe_details = get_recipe_for_dish(test_dish_id)
        if recipe_details:
            print(f"Receta para '{test_dish_id}':")
            for item in recipe_details:
                print(f"  - ID_Receta: {item['id_receta']}, Ingrediente: {item['nombre_ingrediente']} (ID: {item['id_ingrediente']}), "
                      f"Cant: {item['cantidad_necesaria']} {item['unidad_medida_receta']}, Instr: {item['instrucciones_paso']}")
        elif recipe_details == []: # Lista vacía significa que no tiene ingredientes asignados
             print(f"El plato {test_dish_id} no tiene ingredientes en su receta o no existe.")
        else: # None indica un error de consulta
            print(f"Error al obtener la receta para {test_dish_id}.")

        # 3. Actualizar un ingrediente de la receta
        if recipe_entry_id1: # Si el primer ingrediente se añadió
            print(f"\n--- Actualizando ingrediente de la receta (ID Entrada: {recipe_entry_id1}) ---")
            update_count = update_recipe_ingredient(recipe_entry_id1, new_quantity=175.5, new_instructions="Mezclar suavemente")
            if update_count is not None:
                print(f"Entrada de receta {recipe_entry_id1} actualizada (filas afectadas: {update_count}).")
                updated_recipe = get_recipe_for_dish(test_dish_id)
                if updated_recipe:
                    for item in updated_recipe:
                        if item['id_receta'] == recipe_entry_id1:
                            print(f"  Detalle actualizado: Cant: {item['cantidad_necesaria']}, Instr: {item['instrucciones_paso']}")
            else:
                print(f"Fallo al actualizar entrada de receta {recipe_entry_id1}.")
        
        # 4. Eliminar un ingrediente de la receta
        if recipe_entry_id2: # Si el segundo ingrediente se añadió
            print(f"\n--- Eliminando ingrediente de la receta (ID Entrada: {recipe_entry_id2}) ---")
            delete_count = remove_ingredient_from_recipe(recipe_entry_id2)
            if delete_count is not None:
                 print(f"Entrada de receta {recipe_entry_id2} eliminada (filas afectadas: {delete_count}).")
                 recipe_after_delete = get_recipe_for_dish(test_dish_id)
                 print("Receta después de eliminar:")
                 if recipe_after_delete:
                     for item in recipe_after_delete:
                         print(f"  - {item['nombre_ingrediente']}: {item['cantidad_necesaria']} {item['unidad_medida_receta']}")
                 else:
                     print("La receta está vacía o hubo un error.")
            else:
                print(f"Fallo al eliminar entrada de receta {recipe_entry_id2}.")
                
        print("\nPruebas del Modelo de Recetas completadas.")


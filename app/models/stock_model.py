# app/models/stock_model.py
import datetime

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from .. import db # Si db.py está en app/
except ImportError:
    try:
        import db # Si está en el mismo nivel o app está en PYTHONPATH
    except ImportError:
        print("Error: No se pudo importar el módulo db.py en stock_model.py.")
        db = None

# --- Funciones para Productos (insumos generales) ---

def create_product(product_data_dict):
    """
    Crea un nuevo producto en el inventario general.
    Args:
        product_data_dict (dict): Datos del producto. Debe incluir:
            'id_producto', 'nombre', 'unidad_medida', 'costo_unitario', 'perecedero'.
            Opcional: 'descripcion', 'stock_minimo', 'proveedor_principal_ref', 'fecha_caducidad'.
    Returns:
        Resultado de db.execute_query o None.
    """
    if not db: return None
    required_fields = ['id_producto', 'nombre', 'unidad_medida', 'costo_unitario', 'perecedero']
    for field in required_fields:
        if field not in product_data_dict:
            print(f"Error de validación: Falta el campo '{field}' para el producto.")
            return None

    query = """
    INSERT INTO Producto (id_producto, nombre, descripcion, unidad_medida, stock_minimo, 
                          proveedor_principal_ref, costo_unitario, perecedero, fecha_caducidad)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        product_data_dict['id_producto'],
        product_data_dict['nombre'],
        product_data_dict.get('descripcion'),
        product_data_dict['unidad_medida'],
        product_data_dict.get('stock_minimo', 0.0),
        product_data_dict.get('proveedor_principal_ref'),
        product_data_dict['costo_unitario'],
        bool(product_data_dict['perecedero']),
        product_data_dict.get('fecha_caducidad') # Puede ser None
    )
    return db.execute_query(query, params)

def get_product_by_id(product_id_value):
    if not db: return None
    query = "SELECT * FROM Producto WHERE id_producto = %s"
    return db.fetch_one(query, (product_id_value,))

def get_all_products_list():
    if not db: return None
    query = "SELECT * FROM Producto ORDER BY nombre"
    return db.fetch_all(query)

def update_product_details(product_id_value, data_to_update_dict):
    # ... (similar a update_employee_details, actualizando campos de Producto)
    if not db: return None
    if not data_to_update_dict: return 0
    
    allowed_fields = {'nombre', 'descripcion', 'unidad_medida', 'stock_minimo', 
                      'proveedor_principal_ref', 'costo_unitario', 'perecedero', 'fecha_caducidad'}
    
    set_clauses = [f"`{key}` = %s" for key in data_to_update_dict if key in allowed_fields]
    if not set_clauses: return 0
    
    params = [data_to_update_dict[key] for key in data_to_update_dict if key in allowed_fields]
    params.append(product_id_value)
    
    query = f"UPDATE Producto SET {', '.join(set_clauses)} WHERE id_producto = %s"
    return db.execute_query(query, tuple(params))

def delete_product_by_id(product_id_value):
    # ¡Precaución! Considerar si un producto se puede eliminar si es un ingrediente activo.
    # Las restricciones FK (ON DELETE RESTRICT en Ingrediente.id_producto) deberían manejar esto.
    if not db: return None
    query = "DELETE FROM Producto WHERE id_producto = %s"
    return db.execute_query(query, (product_id_value,))


# --- Funciones para Ingredientes (stock específico para cocina) ---

def add_or_update_ingredient_as_product(id_producto, initial_quantity=0.0):
    """
    Añade un Producto existente a la tabla Ingrediente o crea una nueva entrada si no existe.
    Si ya existe como ingrediente, esta función podría usarse para establecer una cantidad inicial
    (aunque las recepciones de stock deberían usar update_ingredient_stock).
    El id_ingrediente será el mismo que id_producto.
    Args:
        id_producto (str): El ID del producto que también es un ingrediente.
        initial_quantity (float): Cantidad inicial disponible de este ingrediente.
    Returns:
        Resultado de db.execute_query o None.
    """
    if not db: return None

    # Verificar que el producto exista en la tabla Producto
    if not get_product_by_id(id_producto):
        print(f"Error: Producto con ID '{id_producto}' no existe. No se puede añadir como ingrediente.")
        return None

    # Usar el mismo ID para id_ingrediente y id_producto para simplificar
    id_ingrediente = id_producto

    # Intentar insertar. Si falla por clave duplicada (UNIQUE en id_producto), entonces ya existe.
    # MySQL: INSERT ... ON DUPLICATE KEY UPDATE se podría usar, o manejar el error.
    # Por ahora, haremos una verificación previa.
    
    existing_ingredient = get_ingredient_by_id(id_ingrediente)
    if existing_ingredient:
        print(f"Ingrediente '{id_ingrediente}' ya existe. Para actualizar stock, use update_ingredient_stock.")
        # Podríamos actualizar la cantidad aquí si la lógica lo permite,
        # pero es mejor tener funciones separadas para claridad.
        # return update_ingredient_stock(id_ingrediente, initial_quantity, is_addition=True, action_type="AJUSTE INICIAL")
        return None # O el ID del ingrediente existente

    query = """
    INSERT INTO Ingrediente (id_ingrediente, id_producto, cantidad_disponible, ultima_actualizacion)
    VALUES (%s, %s, %s, %s)
    """
    params = (id_ingrediente, id_producto, initial_quantity, datetime.datetime.now())
    return db.execute_query(query, params)


def get_stock_movements_history(ingredient_id=None, start_date=None, end_date=None, movement_type=None, limit=100):
    """
    Obtiene el historial de movimientos de stock, con filtros opcionales.
    # ... (cuerpo de la función como te la di) ...
    """
    if not db: return None
    
    query_base = """
    SELECT ms.*, p.nombre as nombre_ingrediente, e.nombre as nombre_empleado, e.apellido as apellido_empleado
    FROM MovimientoStock ms
    JOIN Ingrediente i ON ms.id_ingrediente = i.id_ingrediente
    JOIN Producto p ON i.id_producto = p.id_producto
    LEFT JOIN Empleados e ON ms.id_empleado_responsable = e.id_empleado
    """
    
    conditions = []
    params = []

    if ingredient_id:
        conditions.append("ms.id_ingrediente = %s")
        params.append(ingredient_id)
    if start_date:
        conditions.append("ms.fecha_hora >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("ms.fecha_hora <= %s")
        params.append(end_date)
    if movement_type:
        conditions.append("ms.tipo_movimiento = %s")
        params.append(movement_type)
        
    if conditions:
        query_base += " WHERE " + " AND ".join(conditions)
        
    query_base += " ORDER BY ms.fecha_hora DESC, ms.id_movimiento DESC"
    if limit:
        query_base += " LIMIT %s"
        params.append(limit)
        
    return db.fetch_all(query_base, tuple(params))

def get_low_stock_ingredients_summary(limit=5):
    """
    Obtiene un resumen de los ingredientes con stock bajo o igual al mínimo.
    Args:
        limit (int): Número máximo de ingredientes a devolver en el resumen.
    Returns:
        dict: Un diccionario con 'count' (total de ingredientes bajos) y 
              'items' (lista de hasta 'limit' ingredientes bajos),
              o None si hay un error.
    """
    if not db:
        print("Error en stock_model: Módulo db no disponible.")
        return None
    
    query_string = """
    SELECT i.id_ingrediente, p.nombre as nombre_producto, i.cantidad_disponible, p.stock_minimo, p.unidad_medida
    FROM Ingrediente i
    JOIN Producto p ON i.id_producto = p.id_producto
    WHERE i.cantidad_disponible <= p.stock_minimo AND p.stock_minimo > 0
    ORDER BY (i.cantidad_disponible / p.stock_minimo) ASC, p.nombre ASC
    """
    # El stock_minimo > 0 es para evitar mostrar items que tienen stock_minimo = 0 como "bajos" si su cantidad_disponible es 0.
    
    all_low_stock_items = db.fetch_all(query_string)
    
    if all_low_stock_items is not None:
        summary = {
            'count': len(all_low_stock_items),
            'items': all_low_stock_items[:limit] # Tomar solo los 'limit' primeros para el display
        }
        return summary
    return None # Error en la consulta
    
def get_ingredient_by_id(ingredient_id_value):
    """
    Obtiene un ingrediente por su ID (que es el mismo que el id_producto).
    """
    if not db: return None
    # Hacemos JOIN con Producto para obtener también el nombre del producto
    query = """
    SELECT i.id_ingrediente, i.id_producto, p.nombre as nombre_producto, i.cantidad_disponible, p.unidad_medida, i.ultima_actualizacion
    FROM Ingrediente i
    JOIN Producto p ON i.id_producto = p.id_producto
    WHERE i.id_ingrediente = %s
    """
    return db.fetch_one(query, (ingredient_id_value,))

def get_recent_stock_movements_summary(limit=5):
    """
    Obtiene un resumen de los movimientos de stock más recientes.
    Args:
        limit (int): Número máximo de movimientos a devolver.
    Returns:
        list: Lista de diccionarios con los movimientos recientes, o None si hay error.
    """
    # Simplemente llama a la función de historial con un límite y sin otros filtros
    return get_stock_movements_history(limit=limit)

def get_todays_stock_movements_count():
    """
    Cuenta los movimientos de stock realizados hoy.
    Returns:
        int: Número de movimientos de hoy, o None si hay error.
    """
    if not db: return None
    today_start = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
    today_end = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')
    
    query = """
    SELECT COUNT(*) as count 
    FROM MovimientoStock 
    WHERE fecha_hora BETWEEN %s AND %s
    """
    result = db.fetch_one(query, (today_start, today_end))
    if result:
        return result.get('count', 0)
    return None

def get_all_ingredients_list():
    """
    Obtiene todos los ingredientes con sus detalles de producto.
    """
    if not db: return None
    query = """
    SELECT i.id_ingrediente, i.id_producto, p.nombre as nombre_producto, i.cantidad_disponible, p.unidad_medida, i.ultima_actualizacion
    FROM Ingrediente i
    JOIN Producto p ON i.id_producto = p.id_producto
    ORDER BY p.nombre
    """
    return db.fetch_all(query)

def update_ingredient_stock(ingredient_id_value, quantity_change, is_deduction=True, reason="Consumo por Comanda"):
    """
    Actualiza la cantidad disponible de un ingrediente.
    Args:
        ingredient_id_value (str): ID del ingrediente.
        quantity_change (float): La cantidad a añadir o deducir. Siempre positivo.
        is_deduction (bool): True si es una deducción, False si es una adición (ej. recepción de stock).
        reason (str): Motivo del cambio (para futuro log).
    Returns:
        int: Número de filas afectadas (debería ser 1) o None si falla o el stock es insuficiente.
    """
    if not db: return None
    if quantity_change < 0: # La cantidad de cambio siempre debe ser positiva
        print("Error: La cantidad de cambio de stock debe ser un valor positivo.")
        return None

    current_ingredient = get_ingredient_by_id(ingredient_id_value)
    if not current_ingredient:
        print(f"Error: Ingrediente '{ingredient_id_value}' no encontrado para actualizar stock.")
        return None

    current_stock = float(current_ingredient.get('cantidad_disponible', 0.0))
    
    if is_deduction:
        if current_stock < quantity_change:
            print(f"Error: Stock insuficiente para el ingrediente '{ingredient_id_value}'. Disponible: {current_stock}, Requerido: {quantity_change}")
            return None # Stock insuficiente
        new_stock = current_stock - quantity_change
    else: # Es una adición
        new_stock = current_stock + quantity_change

    query = "UPDATE Ingrediente SET cantidad_disponible = %s, ultima_actualizacion = %s WHERE id_ingrediente = %s"
    params = (new_stock, datetime.datetime.now(), ingredient_id_value)
    
    result = db.execute_query(query, params)
    if result is not None and result > 0:
        print(f"Stock para ingrediente '{ingredient_id_value}' actualizado a {new_stock}. Razón: {reason}")
        # Aquí podrías añadir un log de movimiento de inventario si tuvieras una tabla para ello.
    return result

# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    if not db:
        print("No se pueden ejecutar las pruebas del modelo de stock: módulo db no cargado.")
    else:
        print("Probando el Modelo de Stock (stock_model.py)...")
        
        # IDs de prueba
        test_prod_id1 = "PROD_STOCK_01"
        test_prod_id2 = "PROD_STOCK_02" # Para un producto que no se convertirá en ingrediente
        test_ingr_id1 = test_prod_id1 # Usaremos el mismo ID para el ingrediente

        # Limpieza previa
        print("\n--- Limpieza previa de datos de prueba ---")
        # Intentar eliminar ingrediente (fallará si no existe, está bien)
        db.execute_query("DELETE FROM Ingrediente WHERE id_ingrediente = %s", (test_ingr_id1,))
        delete_product_by_id(test_prod_id1)
        delete_product_by_id(test_prod_id2)

        # 1. Crear productos
        print(f"\n--- Creando producto {test_prod_id1} ---")
        prod1_data = {'id_producto': test_prod_id1, 'nombre': 'Tomates Frescos (Stock)', 
                        'unidad_medida': 'kg', 'costo_unitario': 1.50, 'perecedero': True}
        create_product(prod1_data)
        print(f"Producto {test_prod_id1} creado. Detalles: {get_product_by_id(test_prod_id1)}")

        print(f"\n--- Creando producto {test_prod_id2} ---")
        prod2_data = {'id_producto': test_prod_id2, 'nombre': 'Servilletas (Stock)', 
                        'unidad_medida': 'unidades', 'costo_unitario': 0.05, 'perecedero': False}
        create_product(prod2_data)

        # 2. Convertir un producto en ingrediente (y establecer stock inicial)
        print(f"\n--- Añadiendo/Actualizando {test_prod_id1} como ingrediente con stock inicial ---")
        add_or_update_ingredient_as_product(test_ingr_id1, initial_quantity=10.0)
        ingredient_details = get_ingredient_by_id(test_ingr_id1)
        if ingredient_details:
            print(f"Ingrediente '{ingredient_details['nombre_producto']}' (ID: {test_ingr_id1}) "
                  f"disponible: {ingredient_details['cantidad_disponible']} {ingredient_details['unidad_medida']}")
        else:
            print(f"Fallo al añadir o encontrar ingrediente {test_ingr_id1}")

        # 3. Actualizar stock de ingrediente (añadir)
        print(f"\n--- Añadiendo 5kg más al ingrediente {test_ingr_id1} ---")
        update_ingredient_stock(test_ingr_id1, 5.0, is_deduction=False, reason="Recepción de Proveedor")
        ingredient_details_after_add = get_ingredient_by_id(test_ingr_id1)
        if ingredient_details_after_add:
             print(f"Nuevo stock de '{ingredient_details_after_add['nombre_producto']}': "
                   f"{ingredient_details_after_add['cantidad_disponible']} {ingredient_details_after_add['unidad_medida']}")

        # 4. Actualizar stock de ingrediente (deducir)
        print(f"\n--- Deduciendo 2.5kg del ingrediente {test_ingr_id1} ---")
        update_ingredient_stock(test_ingr_id1, 2.5, is_deduction=True, reason="Consumo Receta X")
        ingredient_details_after_deduct = get_ingredient_by_id(test_ingr_id1)
        if ingredient_details_after_deduct:
             print(f"Nuevo stock de '{ingredient_details_after_deduct['nombre_producto']}': "
                   f"{ingredient_details_after_deduct['cantidad_disponible']} {ingredient_details_after_deduct['unidad_medida']}")

        # 5. Intentar deducir más stock del disponible
        print(f"\n--- Intentando deducir 20kg del ingrediente {test_ingr_id1} (debería fallar) ---")
        result_overdraft = update_ingredient_stock(test_ingr_id1, 20.0, is_deduction=True)
        if result_overdraft is None:
            print("Correcto: Falló la deducción por stock insuficiente.")
        else:
            print(f"Error: La deducción por stock insuficiente no falló como se esperaba (resultado: {result_overdraft}).")
        
        print("\n--- Listando todos los ingredientes ---")
        all_ingredients = get_all_ingredients_list()
        if all_ingredients:
            for ingr in all_ingredients:
                print(f"- {ingr['nombre_producto']} (ID: {ingr['id_ingrediente']}): {ingr['cantidad_disponible']} {ingr['unidad_medida']}")
        else:
            print("No hay ingredientes para listar o hubo un error.")

        print("\nPruebas del Modelo de Stock completadas.")

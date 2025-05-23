# app/models/stock_model.py
import datetime
import uuid 
import random 
import string 
import os
import traceback

# Ajusta la ruta de importación para db.py y supplier_model.py según tu estructura
try:
    from app import db
    from app.models import supplier_model # Necesario para validar proveedor en create/update product
    from . import recipe_model # Si está en el mismo paquete (app/models)
except ImportError:
    # Fallback si la estructura es diferente o se ejecuta directamente
    print("Advertencia: Falló la importación principal en stock_model.py. Intentando fallback...")
    try:
        from .. import db # Si este archivo está en app/models/ y db.py en app/
        from . import supplier_model # Si supplier_model está en el mismo directorio (app/models)
        from . import recipe_model # Si recipe_model está en el mismo directorio (app/models)
    except ImportError:
        try:
            import db
            import supplier_model # Si están en una ruta accesible por PYTHONPATH
        except ImportError as e:
            print(f"Error CRÍTICO: No se pudo importar db.py o supplier_model.py en stock_model.py: {e}")
            db = supplier_model = None

def check_stock_for_dish(id_plato, quantity_to_prepare):
    """
    Verifica si hay suficiente stock de todos los ingredientes para preparar una cantidad dada de un plato.
    Args:
        id_plato (str): El ID del plato a verificar.
        quantity_to_prepare (int): La cantidad de platos a preparar.
    Returns:
        dict: {
                  'can_prepare': bool, 
                  'missing_items': list of dicts [{'nombre_ingrediente', 'id_ingrediente', 'needed', 'available', 'unit'}]
              }
              Retorna None si hay un error crítico (ej. modelo de receta no disponible).
    """
    if not db or not recipe_model:
        print("Error en check_stock_for_dish: db o recipe_model no disponibles.")
        return None # Error crítico

    if quantity_to_prepare <= 0:
        return {'can_prepare': True, 'missing_items': []} # No se necesita nada

    dish_recipe = recipe_model.get_recipe_for_dish(id_plato)
    if dish_recipe is None: # Error al obtener la receta
        print(f"Error: No se pudo obtener la receta para el plato {id_plato} al verificar stock.")
        return {'can_prepare': False, 'missing_items': [{'nombre_ingrediente': 'Error de Receta', 'needed': 0, 'available': 0, 'unit': ''}]}
    if not dish_recipe: # Receta vacía
        print(f"Info: El plato {id_plato} no tiene ingredientes definidos en su receta. Se asume que se puede preparar.")
        return {'can_prepare': True, 'missing_items': []}

    missing_or_insufficient_items = []
    can_prepare_all = True

    for item_receta in dish_recipe:
        id_ingrediente = item_receta.get('id_ingrediente')
        nombre_ingrediente = item_receta.get('nombre_ingrediente', id_ingrediente) # Usar nombre si está disponible
        cantidad_necesaria_por_unidad = float(item_receta.get('cantidad_necesaria', 0))
        unidad_receta = item_receta.get('unidad_medida_receta', '')

        total_needed_for_order = cantidad_necesaria_por_unidad * quantity_to_prepare

        # Obtener stock actual del ingrediente
        # get_ingredient_by_id devuelve más info, incluyendo unidad_medida del stock
        ingredient_stock_info = get_ingredient_by_id(id_ingrediente) 

        if not ingredient_stock_info:
            print(f"Advertencia: Ingrediente '{nombre_ingrediente}' (ID: {id_ingrediente}) de la receta no encontrado en la tabla Ingrediente.")
            missing_or_insufficient_items.append({
                'nombre_ingrediente': nombre_ingrediente,
                'id_ingrediente': id_ingrediente,
                'needed': total_needed_for_order,
                'available': 0, # No se encontró, así que disponible es 0
                'unit': unidad_receta # Usar unidad de receta para el mensaje
            })
            can_prepare_all = False
            continue

        available_stock = float(ingredient_stock_info.get('cantidad_disponible', 0))
        unit_stock = ingredient_stock_info.get('unidad_medida', '') # Unidad en la que se mide el stock

        # IMPORTANTE: Conversión de Unidades
        # Aquí es donde necesitarías lógica de conversión si unidad_receta != unit_stock
        # Ejemplo simple: si receta es 'g' y stock es 'kg', convertir needed a kg.
        # Esta parte puede volverse compleja y requiere un sistema de conversión de unidades.
        # Por ahora, asumiremos que las unidades son compatibles o que la cantidad_necesaria
        # en la receta ya está en la unidad base del stock.
        # Si no son compatibles, esta verificación podría dar falsos positivos/negativos.
        if unidad_receta.lower() != unit_stock.lower():
            print(f"ADVERTENCIA DE UNIDADES: Para '{nombre_ingrediente}', la receta usa '{unidad_receta}' y el stock está en '{unit_stock}'. "
                  "La verificación de stock puede ser incorrecta sin conversión de unidades.")
            # Aquí podrías añadir lógica de conversión o marcarlo como un problema.
            # Por ahora, si las unidades son diferentes, podríamos considerarlo un riesgo y añadirlo a faltantes.
            # O simplemente proceder y esperar que las cantidades sean relativas a la misma base.

        if available_stock < total_needed_for_order:
            missing_or_insufficient_items.append({
                'nombre_ingrediente': nombre_ingrediente,
                'id_ingrediente': id_ingrediente,
                'needed': total_needed_for_order,
                'available': available_stock,
                'unit': unit_stock # Mostrar la unidad del stock disponible
            })
            can_prepare_all = False

    return {'can_prepare': can_prepare_all, 'missing_items': missing_or_insufficient_items}


def generate_product_id(length=10):
    """Genera un ID único para un nuevo producto. Ejemplo: PROD-ABC12"""
    chars_to_generate = length - 5 # Para "PROD-"
    if chars_to_generate < 1: chars_to_generate = 5 
    characters = string.ascii_uppercase + string.digits
    random_id_part = ''.join(random.choice(characters) for _ in range(chars_to_generate))
    return f"PROD-{random_id_part}"

def _log_stock_movement(cursor, id_ingrediente, tipo_movimiento, cantidad_cambio,
                       cantidad_anterior, cantidad_nueva, id_referencia_origen=None,
                       descripcion_motivo="", id_empleado_responsable=None):
    """Función helper para insertar en MovimientoStock. Asume que el cursor ya está abierto."""
    log_query = """
    INSERT INTO MovimientoStock 
        (id_ingrediente, tipo_movimiento, cantidad_cambio, cantidad_anterior, cantidad_nueva,
         id_referencia_origen, descripcion_motivo, id_empleado_responsable, fecha_hora)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    current_timestamp = datetime.datetime.now()
    log_params = (
        id_ingrediente, tipo_movimiento, cantidad_cambio, cantidad_anterior, cantidad_nueva,
        id_referencia_origen, descripcion_motivo, id_empleado_responsable, current_timestamp
    )
    try:
        cursor.execute(log_query, log_params)
        print(f"INFO: Movimiento de stock para '{id_ingrediente}' registrado: {tipo_movimiento}, Cant: {cantidad_cambio}")
    except Exception as e: 
        print(f"ERROR al registrar movimiento de stock para '{id_ingrediente}': {e}")
        traceback.print_exc() # Imprimir traceback para más detalles del error de logueo


# --- Funciones para Productos (insumos generales) ---
def create_product(product_data_dict):
    if not db:
        print("Error en stock_model: Módulo db no disponible.")
        return None

    generated_id = generate_product_id()
    
    nombre_producto = product_data_dict.get('nombre')
    unidad_medida = product_data_dict.get('unidad_medida')
    costo_unitario = product_data_dict.get('costo_unitario')
    perecedero = product_data_dict.get('perecedero') # Debería ser un booleano

    if not nombre_producto or not unidad_medida or costo_unitario is None or perecedero is None:
        print(f"Error de validación: Faltan campos obligatorios para el producto (nombre, unidad_medida, costo_unitario, perecedero).")
        return None
    
    proveedor_ref = product_data_dict.get('proveedor_principal_ref')
    if proveedor_ref: # Si se proporciona un proveedor_ref, verificar que exista
        if not supplier_model:
            print("ERROR: Modelo de proveedor no disponible para validación.")
            return None
        if not supplier_model.get_supplier_by_id(proveedor_ref):
            print(f"ERROR: El proveedor_principal_ref '{proveedor_ref}' no existe. No se creará el producto.")
            return None

    query = """
    INSERT INTO Producto (id_producto, nombre, descripcion, unidad_medida, stock_minimo, 
                          proveedor_principal_ref, costo_unitario, perecedero, fecha_caducidad)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        generated_id, # Usar el ID generado
        nombre_producto,
        product_data_dict.get('descripcion'),
        unidad_medida,
        product_data_dict.get('stock_minimo', 0.0),
        proveedor_ref, 
        costo_unitario,
        bool(perecedero), # Asegurar que sea booleano
        product_data_dict.get('fecha_caducidad')
    )
    
    try:
        result_db = db.execute_query(query, params)
        if result_db is not None:
            print(f"Producto '{generated_id}' ('{nombre_producto}') creado exitosamente.")
            return generated_id
        else:
            print(f"No se pudo crear el producto '{nombre_producto}' (ID intentado: {generated_id}).")
            return None
    except Exception as e:
        print(f"Excepción al crear producto '{nombre_producto}': {e}")
        traceback.print_exc()
        return None

def get_product_by_id(product_id_value):
    if not db: return None
    query = "SELECT * FROM Producto WHERE id_producto = %s"
    return db.fetch_one(query, (product_id_value,))

def get_all_products_list():
    if not db: return None
    query = "SELECT * FROM Producto ORDER BY nombre"
    return db.fetch_all(query)

def update_product_details(product_id_value, data_to_update_dict):
    if not db: return None
    if not product_id_value:
        print("Error: Se requiere ID de producto para actualizar.")
        return None
    if not data_to_update_dict: return 0
    
    proveedor_ref = data_to_update_dict.get('proveedor_principal_ref')
    if 'proveedor_principal_ref' in data_to_update_dict and proveedor_ref:
        if not supplier_model:
            print("ERROR: Modelo de proveedor no disponible para validación en actualización.")
            return None
        if not supplier_model.get_supplier_by_id(proveedor_ref):
            print(f"ERROR: El proveedor_principal_ref '{proveedor_ref}' no existe. No se actualizará el producto con este proveedor.")
            return None

    allowed_fields = {'nombre', 'descripcion', 'unidad_medida', 'stock_minimo', 
                      'proveedor_principal_ref', 'costo_unitario', 'perecedero', 'fecha_caducidad'}
    
    set_clauses = []
    params_values = []
    for key, value in data_to_update_dict.items():
        if key in allowed_fields:
            set_clauses.append(f"`{key}` = %s")
            if key == 'proveedor_principal_ref' and isinstance(value, str) and not value.strip():
                params_values.append(None)
            elif key == 'perecedero':
                params_values.append(bool(value))
            else:
                params_values.append(value)

    if not set_clauses: return 0
    
    params_values.append(product_id_value)
    query = f"UPDATE Producto SET {', '.join(set_clauses)} WHERE id_producto = %s"
    
    try:
        return db.execute_query(query, tuple(params_values))
    except Exception as e:
        print(f"Excepción al actualizar producto '{product_id_value}': {e}")
        traceback.print_exc()
        return None


def delete_product_by_id(product_id_value):
    if not db: return None
    # Considerar verificar si el producto es un ingrediente activo antes de borrar
    # o confiar en las restricciones FK de la BD (Ingrediente.id_producto ON DELETE CASCADE)
    # Si es CASCADE, al borrar el producto se borrará el ingrediente y sus movimientos de stock.
    query = "DELETE FROM Producto WHERE id_producto = %s"
    return db.execute_query(query, (product_id_value,))


# --- Funciones para Ingredientes (stock específico para cocina) ---
def add_or_update_ingredient_as_product(id_producto, initial_quantity=0.0, id_empleado=None):
    if not db: return None

    product_info = get_product_by_id(id_producto)
    if not product_info:
        print(f"Error: Producto con ID '{id_producto}' no existe. No se puede añadir como ingrediente.")
        return None

    id_ingrediente = id_producto
    
    conn = db.get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id_ingrediente FROM Ingrediente WHERE id_ingrediente = %s", (id_ingrediente,))
        existing_ingredient_row = cursor.fetchone()

        if existing_ingredient_row:
            print(f"INFO: Ingrediente '{id_ingrediente}' ({product_info.get('nombre', '')}) ya existe.")
            conn.commit() 
            return id_ingrediente 
        else:
            insert_query = """
            INSERT INTO Ingrediente (id_ingrediente, id_producto, cantidad_disponible, ultima_actualizacion)
            VALUES (%s, %s, %s, %s)
            """
            current_time = datetime.datetime.now()
            cursor.execute(insert_query, (id_ingrediente, id_producto, initial_quantity, current_time))
            
            _log_stock_movement(cursor, id_ingrediente, "INVENTARIO_INICIAL", initial_quantity,
                                0.0, initial_quantity,
                                descripcion_motivo=f"Ingrediente '{product_info.get('nombre', id_ingrediente)}' creado con stock inicial.",
                                id_empleado_responsable=id_empleado)
            conn.commit()
            print(f"INFO: Ingrediente '{id_ingrediente}' creado y movimiento inicial registrado.")
            return id_ingrediente
            
    except Exception as e:
        print(f"Excepción en add_or_update_ingredient_as_product para '{id_producto}': {e}")
        traceback.print_exc()
        if conn: conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_ingredient_by_id(ingredient_id_value):
    if not db: return None
    query = """
    SELECT i.id_ingrediente, i.id_producto, p.nombre as nombre_producto, 
           i.cantidad_disponible, p.unidad_medida, i.ultima_actualizacion
    FROM Ingrediente i
    JOIN Producto p ON i.id_producto = p.id_producto
    WHERE i.id_ingrediente = %s
    """
    return db.fetch_one(query, (ingredient_id_value,))

def get_all_ingredients_list():
    if not db: return None
    query = """
    SELECT i.id_ingrediente, i.id_producto, p.nombre as nombre_producto, 
           i.cantidad_disponible, p.unidad_medida, i.ultima_actualizacion
    FROM Ingrediente i
    JOIN Producto p ON i.id_producto = p.id_producto
    ORDER BY p.nombre
    """
    return db.fetch_all(query)

def update_ingredient_stock(ingredient_id_value, quantity_change, is_deduction=True, 
                            reason_type="CONSUMO_COMANDA", custom_reason_desc="", 
                            id_reference=None, id_employee=None):
    if not db: return None
    if quantity_change < 0:
        print("Error: La cantidad de cambio de stock (quantity_change) debe ser un valor positivo.")
        return None

    conn = db.get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT cantidad_disponible, p.nombre as nombre_producto FROM Ingrediente i JOIN Producto p ON i.id_producto = p.id_producto WHERE i.id_ingrediente = %s FOR UPDATE", (ingredient_id_value,))
        current_ingredient_data = cursor.fetchone()

        if not current_ingredient_data:
            print(f"Error: Ingrediente '{ingredient_id_value}' no encontrado para actualizar stock.")
            conn.rollback() # Liberar el FOR UPDATE si existe
            return None

        current_stock = float(current_ingredient_data.get('cantidad_disponible', 0.0))
        ingredient_name = current_ingredient_data.get('nombre_producto', ingredient_id_value)
        
        actual_qty_to_log = quantity_change
        
        if is_deduction:
            if current_stock < quantity_change:
                print(f"Error: Stock insuficiente para '{ingredient_name}'. Disponible: {current_stock}, Requerido: {quantity_change}")
                conn.rollback()
                return None 
            new_stock = current_stock - quantity_change
            actual_qty_to_log = -quantity_change
        else: 
            new_stock = current_stock + quantity_change

        update_query = "UPDATE Ingrediente SET cantidad_disponible = %s, ultima_actualizacion = %s WHERE id_ingrediente = %s"
        cursor.execute(update_query, (new_stock, datetime.datetime.now(), ingredient_id_value))
        rows_affected_ingredient = cursor.rowcount

        final_reason_desc = f"{reason_type}: {custom_reason_desc}".strip() if custom_reason_desc else reason_type
        if id_reference:
             final_reason_desc += f" (Ref: {id_reference})"
        
        _log_stock_movement(cursor, ingredient_id_value, reason_type, actual_qty_to_log,
                           current_stock, new_stock,
                           id_referencia_origen=id_reference,
                           descripcion_motivo=final_reason_desc,
                           id_empleado_responsable=id_employee)
        
        conn.commit()
        print(f"INFO: Stock para '{ingredient_name}' actualizado a {new_stock}. Razón: {final_reason_desc}")
        return rows_affected_ingredient

    except Exception as e:
        print(f"Excepción en update_ingredient_stock para '{ingredient_id_value}': {e}")
        traceback.print_exc()
        if conn: conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_stock_movements_history(ingredient_id=None, start_date=None, end_date=None, movement_type=None, limit=100):
    if not db: return None
    
    query_base = """
    SELECT ms.id_movimiento, ms.fecha_hora, ms.id_ingrediente, 
           p.nombre as nombre_ingrediente, ms.tipo_movimiento, 
           ms.cantidad_cambio, ms.cantidad_nueva, ms.descripcion_motivo,
           e.nombre as nombre_empleado, e.apellido as apellido_empleado,
           ms.id_referencia_origen, ms.id_empleado_responsable
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
        conditions.append("DATE(ms.fecha_hora) >= %s") # Comparar solo fecha
        params.append(start_date)
    if end_date:
        conditions.append("DATE(ms.fecha_hora) <= %s") # Comparar solo fecha
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
    if not db: return None
    query_string = """
    SELECT i.id_ingrediente, p.nombre as nombre_producto, i.cantidad_disponible, 
           p.stock_minimo, p.unidad_medida
    FROM Ingrediente i
    JOIN Producto p ON i.id_producto = p.id_producto
    WHERE i.cantidad_disponible <= p.stock_minimo AND p.stock_minimo > 0
    ORDER BY (i.cantidad_disponible / NULLIF(p.stock_minimo, 0)) ASC, p.nombre ASC 
    """ # Usar NULLIF para evitar división por cero si stock_minimo es 0
    
    all_low_stock_items = db.fetch_all(query_string)
    
    if all_low_stock_items is not None:
        summary = {
            'count': len(all_low_stock_items),
            'items': all_low_stock_items[:limit]
        }
        return summary
    return None

def get_recent_stock_movements_summary(limit=5):
    return get_stock_movements_history(limit=limit)

def get_todays_stock_movements_count():
    if not db: return None
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    
    query = """
    SELECT COUNT(*) as count 
    FROM MovimientoStock 
    WHERE DATE(fecha_hora) = %s
    """
    result = db.fetch_one(query, (today_date,))
    if result:
        return result.get('count', 0)
    return None

# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    # ... (Tu bloque de pruebas existente, asegúrate que sea compatible con los cambios)
    # ... (Por ejemplo, al crear productos, ya no pasarás el ID)
    print("Ejecutando pruebas de stock_model.py...")
    # Ejemplo de prueba para create_product
    if db and supplier_model:
        print("\n--- Probando create_product (ID autogenerado) ---")
        # Crear un proveedor de prueba si no existe para la FK
        test_prov_id = "PROV_STOCKTEST"
        if not supplier_model.get_supplier_by_id(test_prov_id):
            supplier_model.create_supplier({
                'id_proveedor': test_prov_id,
                'nombre': 'Proveedor para Pruebas de Stock'
            })

        prod_data_test = {
            'nombre': 'Producto Test AutoID', 
            'unidad_medida': 'unidades', 
            'costo_unitario': 10.0, 
            'perecedero': False,
            'proveedor_principal_ref': test_prov_id # Usar un ID de proveedor válido
        }
        new_prod_id = create_product(prod_data_test)
        if new_prod_id:
            print(f"Producto de prueba creado con ID: {new_prod_id}")
            # Aquí podrías añadir más pruebas para marcarlo como ingrediente, etc.
            # Y luego limpiarlo
            # delete_product_by_id(new_prod_id)
            # supplier_model.delete_supplier_by_id(test_prov_id) # Limpiar proveedor de prueba
        else:
            print("Fallo al crear producto de prueba.")
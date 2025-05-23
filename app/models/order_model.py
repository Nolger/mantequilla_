# app/models/order_model.py
import datetime
import sys
import traceback

try:
    from app import db
    from app.models import table_model
    from app.models import menu_model
    from app.models import stock_model as app_stock_model
    from app.models import recipe_model as app_recipe_model
except ImportError:
    print("ADVERTENCIA DE IMPORTACIÓN en order_model.py: No se pudieron cargar módulos desde 'app.' Intentando fallback relativo...")
    try:
        from .. import db
        from . import table_model
        from . import menu_model
        from . import stock_model as app_stock_model
        from . import recipe_model as app_recipe_model
    except ImportError:
        print("ADVERTENCIA DE IMPORTACIÓN en order_model.py: Falló fallback relativo. Intentando importación directa...")
        try:
            import db
            import table_model
            import menu_model
            import stock_model as app_stock_model
            import recipe_model as app_recipe_model
        except ImportError as e:
            print(f"Error CRÍTICO: No se pudieron importar módulos esenciales en order_model.py: {e}")
            db = table_model = menu_model = app_stock_model = app_recipe_model = None


def generate_order_id():
    now = datetime.datetime.now()
    unique_suffix = now.strftime("%f")[:4]
    return f"COM-{now.strftime('%Y%m%d-%H%M%S')}-{unique_suffix}"

def create_new_order(table_id_value, employee_id_value, customer_id_value=None, num_people=1):
    if not db or not table_model:
        print("Error: Módulos db o table_model no disponibles en order_model (create_new_order).")
        return None

    current_table_info = table_model.get_table_by_id(table_id_value)
    if not current_table_info:
        print(f"Error: Mesa '{table_id_value}' no encontrada.")
        return None
    if current_table_info.get('estado') not in ('libre', 'reservada'):
        print(f"Error: Mesa '{table_id_value}' no está libre o reservada (estado actual: {current_table_info.get('estado')}).")
        return None

    order_id = generate_order_id()
    default_order_status = 'abierta'
    order_query = """
    INSERT INTO Comanda (id_comanda, id_mesa, id_empleado_mesero, id_cliente, cantidad_personas, estado_comanda, fecha_hora_apertura)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    current_timestamp = datetime.datetime.now()
    order_params = (
        order_id, table_id_value, employee_id_value, customer_id_value,
        num_people, default_order_status, current_timestamp
    )

    conn = None
    cursor = None
    try:
        conn = db.get_db_connection()
        if not conn:
            print("ERROR: No se pudo obtener conexión a BD en create_new_order.")
            return None
        cursor = conn.cursor()

        cursor.execute(order_query, order_params)

        # Actualizar el estado de la mesa dentro de la misma transacción de la comanda
        cursor.execute("UPDATE Mesa SET estado = %s WHERE id_mesa = %s", ('ocupada', table_id_value))
        update_table_rows_affected = cursor.rowcount # Usamos cursor.rowcount para la mesa

        if update_table_rows_affected == 0:
             print(f"ADVERTENCIA: Comanda '{order_id}' creada, PERO la mesa '{table_id_value}' ya estaba 'ocupada' o no se pudo actualizar.")
        else:
             print(f"INFO: Mesa '{table_id_value}' actualizada a 'ocupada'. (Filas afectadas: {update_table_rows_affected})")

        conn.commit()
        print(f"INFO: Comanda '{order_id}' creada. Mesa '{table_id_value}' debería estar 'ocupada'.")
        return order_id

    except Exception as e:
        print(f"Excepción al crear comanda o actualizar mesa: {e}")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected():
            conn.close()

def add_dish_to_order(order_id_value, dish_id_value, quantity_value, observations_value=""):
    if not db or not menu_model:
        print("Error: Módulos db o menu_model no disponibles en order_model (add_dish_to_order).")
        return None
    if not isinstance(quantity_value, int) or quantity_value <= 0:
        print("Error: La cantidad debe ser un entero mayor que cero.")
        return None

    dish_info = menu_model.get_dish_by_id(dish_id_value)
    if not dish_info or not dish_info.get('activo', False):
        print(f"Error: Plato con ID '{dish_id_value}' no encontrado o no está activo.")
        return None

    price_at_moment = dish_info.get('precio_venta')
    if price_at_moment is None:
        print(f"Error: No se pudo obtener el precio para el plato '{dish_id_value}'.")
        return None

    order_status_info = db.fetch_one("SELECT estado_comanda FROM Comanda WHERE id_comanda = %s", (order_id_value,))
    if not order_status_info or order_status_info.get('estado_comanda') != 'abierta':
        print(f"Error: No se pueden añadir platos. La comanda '{order_id_value}' no está abierta (estado: {order_status_info.get('estado_comanda', 'DESCONOCIDO')}).")
        return None

    default_dish_status_in_order = 'pendiente'
    detail_query = """
    INSERT INTO DetalleComanda
        (id_comanda, id_plato, cantidad, precio_unitario_momento, estado_plato, observaciones_plato, hora_pedido)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    current_timestamp = datetime.datetime.now()
    detail_params = (
        order_id_value, dish_id_value, quantity_value, price_at_moment,
        default_dish_status_in_order, observations_value, current_timestamp
    )
    return db.execute_query(detail_query, detail_params)

def get_order_by_id(order_id_value):
    if not db: return None
    order_info_query = "SELECT * FROM Comanda WHERE id_comanda = %s"
    order_data = db.fetch_one(order_info_query, (order_id_value,))

    if not order_data: return None

    order_details_query = """
    SELECT dc.id_detalle_comanda, dc.id_plato, p.nombre_plato, dc.cantidad,
           dc.precio_unitario_momento, dc.subtotal_detalle, dc.estado_plato, dc.observaciones_plato,
           dc.hora_pedido
    FROM DetalleComanda dc
    JOIN Plato p ON dc.id_plato = p.id_plato
    WHERE dc.id_comanda = %s
    ORDER BY dc.id_detalle_comanda ASC
    """
    details_data = db.fetch_all(order_details_query, (order_id_value,))
    order_data['detalles'] = details_data if details_data is not None else []
    return order_data

def get_active_orders_for_table(table_id_value):
    if not db: return None
    query = """
    SELECT * FROM Comanda
    WHERE id_mesa = %s
    AND estado_comanda NOT IN ('facturada', 'cancelada')
    ORDER BY fecha_hora_apertura DESC
    """
    return db.fetch_all(query, (table_id_value,))

def get_active_orders_for_waiter(employee_id_mesero):
    if not db: return None
    query = """
    SELECT c.id_comanda, c.fecha_hora_apertura, c.estado_comanda, c.cantidad_personas,
           m.id_mesa as nombre_mesa
    FROM Comanda c
    JOIN Mesa m ON c.id_mesa = m.id_mesa
    WHERE c.id_empleado_mesero = %s
    AND c.estado_comanda NOT IN ('facturada', 'cancelada')
    ORDER BY c.fecha_hora_apertura DESC
    """
    return db.fetch_all(query, (employee_id_mesero,))

def update_order_status(order_id_value, new_status_value):
    if not db or not table_model: return None

    valid_statuses = ['abierta', 'en preparacion', 'lista para servir', 'servida', 'facturada', 'cancelada']
    if new_status_value not in valid_statuses:
        print(f"Error: Estado de comanda '{new_status_value}' no es válido.")
        return None

    conn = None
    cursor = None
    try:
        conn = db.get_db_connection()
        if not conn:
            print("Error: No se pudo obtener conexión a BD en update_order_status.")
            return None
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id_mesa, estado_comanda, fecha_hora_cierre FROM Comanda WHERE id_comanda = %s", (order_id_value,))
        order_info = cursor.fetchone()

        if not order_info:
            print(f"Error: Comanda '{order_id_value}' no encontrada para actualizar estado.")
            return None

        table_id_associated = order_info.get('id_mesa')
        current_order_status = order_info.get('estado_comanda')

        if current_order_status in ['facturada', 'cancelada'] and new_status_value not in ['facturada', 'cancelada']:
            print(f"Advertencia: La comanda '{order_id_value}' ya está finalizada ({current_order_status}). No se puede cambiar su estado a '{new_status_value}'.")
            return 0

        query = "UPDATE Comanda SET estado_comanda = %s, fecha_hora_cierre = %s WHERE id_comanda = %s"
        fecha_cierre = datetime.datetime.now() if new_status_value in ['facturada', 'cancelada'] else order_info.get('fecha_hora_cierre')

        cursor.execute(query, (new_status_value, fecha_cierre, order_id_value))
        rows_affected = cursor.rowcount

        if rows_affected > 0:
            print(f"INFO: Comanda '{order_id_value}' actualizada a '{new_status_value}'.")
            if new_status_value in ['facturada', 'cancelada'] and table_id_associated:
                # Actualizar el estado de la mesa dentro de la misma transacción de la comanda
                cursor.execute("UPDATE Mesa SET estado = %s WHERE id_mesa = %s", ('libre', table_id_associated))
                update_mesa_rows_affected = cursor.rowcount

                if update_mesa_rows_affected == 0:
                    print(f"ADVERTENCIA: Comanda '{order_id_value}' finalizada, PERO la mesa '{table_id_associated}' ya estaba 'libre' o no se pudo actualizar.")
                else:
                    print(f"INFO: Mesa '{table_id_associated}' actualizada a 'libre'. (Filas afectadas: {update_mesa_rows_affected})")
            conn.commit()
            return rows_affected
        else:
            print(f"INFO: No se pudo actualizar el estado de la comanda '{order_id_value}' o ya estaba en ese estado.")
            conn.rollback()
            return 0

    except Exception as e:
        print(f"Excepción en update_order_status: {e}")
        traceback.print_exc()
        if conn: conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

def update_order_item_status(order_detail_id_value, new_item_status_value, id_employee_responsible=None):
    print(f"\nDEBUG: update_order_item_status - DetalleID: {order_detail_id_value}, NuevoEstado: {new_item_status_value}, EmpleadoResp: {id_employee_responsible}")

    if not db or not app_stock_model or not app_recipe_model:
        print("ERROR CRÍTICO: Módulos db, stock_model o recipe_model no están disponibles en update_order_item_status.")
        return None

    valid_statuses = ['pendiente', 'en preparacion', 'listo', 'entregado', 'cancelado']
    if new_item_status_value not in valid_statuses:
        print(f"ERROR: Estado de ítem de comanda '{new_item_status_value}' no es válido.")
        return None

    conn = db.get_db_connection()
    if not conn:
        print("ERROR: No se pudo obtener conexión a la BD en update_order_item_status.")
        return None
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id_plato, cantidad, estado_plato, id_comanda FROM DetalleComanda WHERE id_detalle_comanda = %s FOR UPDATE", (order_detail_id_value,))
        item_info = cursor.fetchone()

        if not item_info:
            print(f"ERROR: Detalle de comanda ID {order_detail_id_value} no encontrado.")
            conn.rollback()
            return False

        current_status = item_info['estado_plato']
        id_plato = item_info['id_plato']
        cantidad_pedida = int(item_info['cantidad'])
        id_comanda_ref = item_info['id_comanda']
        print(f"DEBUG: Info del ítem: PlatoID={id_plato}, CantPedida={cantidad_pedida}, EstadoActual={current_status}, ComandaRef={id_comanda_ref}")

        if current_status == new_item_status_value:
            print(f"INFO: Plato {order_detail_id_value} ya está en estado '{new_item_status_value}'. No se requiere actualización.")
            conn.commit() # Si no hay cambio, igualmente se confirma el "no cambio"
            return True # Consideramos que ya está en el estado deseado, así que es un "éxito"


        if new_item_status_value == 'en preparacion' and current_status == 'pendiente':
            print(f"INFO: Plato ID {id_plato} (Detalle: {order_detail_id_value}) pasando a 'en preparacion'. Intentando descontar stock.")

            cursor.execute("""
                SELECT r.id_ingrediente, r.cantidad_necesaria, p.nombre AS nombre_ingrediente, p.unidad_medida as unidad_stock
                FROM Receta r
                JOIN Ingrediente i ON r.id_ingrediente = i.id_ingrediente
                JOIN Producto p ON i.id_producto = p.id_producto
                WHERE r.id_plato = %s
            """, (id_plato,))
            recipe_items = cursor.fetchall()

            if not recipe_items:
                print(f"ADVERTENCIA: No se encontró receta para el plato ID {id_plato}. No se descontará stock.")
            else:
                for ingrediente_receta in recipe_items:
                    id_ingrediente_a_descontar = ingrediente_receta['id_ingrediente']
                    cantidad_necesaria_por_plato = float(ingrediente_receta['cantidad_necesaria'])
                    nombre_ingrediente_log = ingrediente_receta['nombre_ingrediente']
                    unidad_stock_ingrediente = ingrediente_receta['unidad_stock']

                    cantidad_total_a_descontar = cantidad_necesaria_por_plato * cantidad_pedida

                    cursor.execute("SELECT cantidad_disponible FROM Ingrediente WHERE id_ingrediente = %s FOR UPDATE", (id_ingrediente_a_descontar,))
                    ing_stock_info = cursor.fetchone()
                    if not ing_stock_info:
                        print(f"ERROR CRÍTICO: Ingrediente '{nombre_ingrediente_log}' (ID: {id_ingrediente_a_descontar}) no encontrado en la tabla Ingrediente para descuento.")
                        conn.rollback()
                        return False # Retornar False para indicar que la operación no pudo completarse

                    stock_actual_ing = float(ing_stock_info['cantidad_disponible'])

                    if stock_actual_ing < cantidad_total_a_descontar:
                        print(f"ERROR: Stock insuficiente para '{nombre_ingrediente_log}' (ID: {id_ingrediente_a_descontar}). "
                              f"Disponible: {stock_actual_ing}, Requerido: {cantidad_total_a_descontar} {unidad_stock_ingrediente}")
                        conn.rollback()
                        return False # Retornar False para indicar que la operación no pudo completarse

                    nuevo_stock_ing = stock_actual_ing - cantidad_total_a_descontar

                    cursor.execute("UPDATE Ingrediente SET cantidad_disponible = %s, ultima_actualizacion = %s WHERE id_ingrediente = %s",
                                   (nuevo_stock_ing, datetime.datetime.now(), id_ingrediente_a_descontar))
                    print(f"  UPDATE Ingrediente ejecutado para '{id_ingrediente_a_descontar}'. Filas afectadas: {cursor.rowcount}")

                    log_desc = f"Consumo por Comanda {id_comanda_ref}, Plato: {id_plato}, Detalle: {order_detail_id_value}"
                    if hasattr(app_stock_model, '_log_stock_movement'):
                         app_stock_model._log_stock_movement(
                            cursor, id_ingrediente_a_descontar, "CONSUMO_COMANDA",
                            -cantidad_total_a_descontar,
                            stock_actual_ing, nuevo_stock_ing,
                            id_referencia_origen=str(order_detail_id_value),
                            descripcion_motivo=log_desc,
                            id_empleado_responsable=id_employee_responsible
                        )
                    else:
                        print(f"ADVERTENCIA: _stock_model._log_stock_movement no encontrado. No se pudo loguear el movimiento para {id_ingrediente_a_descontar}.")
                    print(f"  Stock de '{nombre_ingrediente_log}' actualizado a {nuevo_stock_ing}.")

        elif new_item_status_value == 'cancelado' and current_status == 'en preparacion':
            print(f"INFO: Plato ID {id_plato} (Detalle: {order_detail_id_value}) pasando a 'cancelado' desde 'en preparacion'.")
            print("ADVERTENCIA: Se necesitaría lógica para REINGRESAR stock de ingredientes si el plato se cancela DESPUÉS de estar 'en preparacion'.")

        print(f"DEBUG: Actualizando estado del plato DetalleID {order_detail_id_value} a '{new_item_status_value}'")
        query_update_status = "UPDATE DetalleComanda SET estado_plato = %s WHERE id_detalle_comanda = %s"
        cursor.execute(query_update_status, (new_item_status_value, order_detail_id_value))
        rows_affected_detail = cursor.rowcount
        print(f"DEBUG: UPDATE DetalleComanda ejecutado. Filas afectadas: {rows_affected_detail}")

        if rows_affected_detail > 0:
            print("DEBUG: Realizando commit porque el estado del plato cambió y stock se gestionó.")
            conn.commit()
            print("DEBUG: Commit realizado.")
            return True
        else:
            print(f"ADVERTENCIA: No se pudo actualizar el estado de DetalleComanda {order_detail_id_value} a '{new_item_status_value}', pero no hubo error de DB.")
            conn.rollback() # Si no se afectaron filas, deshacer cualquier cambio previo (ej. stock)
            return False

    except Exception as e:
        print(f"EXCEPCIÓN en update_order_item_status: {e}")
        traceback.print_exc()
        if conn:
            print("DEBUG: Realizando rollback debido a excepción...")
            conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
        print(f"DEBUG: Conexión cerrada en update_order_item_status para DetalleID: {order_detail_id_value}")

def get_active_orders_summary():
    if not db:
        print("Error en order_model: Módulo db no disponible.")
        return None

    active_states_tuple = ('abierta', 'en preparacion', 'lista para servir')
    placeholders = ', '.join(['%s'] * len(active_states_tuple))
    query_string = f"SELECT estado_comanda, COUNT(*) as cantidad FROM Comanda WHERE estado_comanda IN ({placeholders}) GROUP BY estado_comanda"

    results = db.fetch_all(query_string, active_states_tuple)
    summary = {state: 0 for state in active_states_tuple}

    if results:
        for row in results:
            summary[row['estado_comanda']] = row['cantidad']
        return summary
    elif results == []:
        return summary
    return None

def get_orders_history(start_date=None, end_date=None, table_id=None,
                       employee_id=None, customer_id=None, order_status=None, limit=100):
    if not db: return None

    query_base = """
    SELECT c.id_comanda, c.fecha_hora_apertura, c.fecha_hora_cierre,
           m.id_mesa, m.ubicacion as ubicacion_mesa,
           e.nombre as nombre_mesero, e.apellido as apellido_mesero,
           cl.nombre as nombre_cliente,
           c.cantidad_personas, c.estado_comanda, c.observaciones
    FROM Comanda c
    JOIN Mesa m ON c.id_mesa = m.id_mesa
    JOIN Empleados e ON c.id_empleado_mesero = e.id_empleado
    LEFT JOIN Cliente cl ON c.id_cliente = cl.id_cliente
    """

    conditions = []
    params = []

    if start_date:
        conditions.append("DATE(c.fecha_hora_apertura) >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("DATE(c.fecha_hora_apertura) <= %s")
        params.append(end_date)
    if table_id:
        conditions.append("c.id_mesa = %s")
        params.append(table_id)
    if employee_id:
        conditions.append("c.id_empleado_mesero = %s")
        params.append(employee_id)
    if customer_id:
        conditions.append("c.id_cliente = %s")
        params.append(customer_id)
    if order_status:
        conditions.append("c.estado_comanda = %s")
        params.append(order_status)

    if conditions:
        query_base += " WHERE " + " AND ".join(conditions)

    query_base += " ORDER BY c.fecha_hora_apertura DESC, c.id_comanda DESC"
    if limit:
        query_base += " LIMIT %s"
        params.append(limit)

    return db.fetch_all(query_base, tuple(params))

def get_dishes_for_kitchen_view():
    if not db: return None
    query = """
    SELECT
        dc.id_detalle_comanda,
        dc.id_comanda,
        dc.id_plato,
        p.nombre_plato,
        dc.cantidad,
        dc.estado_plato,
        dc.observaciones_plato,
        dc.hora_pedido,
        co.id_mesa
    FROM DetalleComanda dc
    JOIN Plato p ON dc.id_plato = p.id_plato
    JOIN Comanda co ON dc.id_comanda = co.id_comanda
    WHERE dc.estado_plato IN ('pendiente', 'en preparacion')
    ORDER BY dc.hora_pedido ASC, dc.id_comanda ASC, dc.id_detalle_comanda ASC;
    """
    return db.fetch_all(query)

if __name__ == '__main__':
    if not all([db, table_model, menu_model, app_stock_model, app_recipe_model]):
        print("No se pueden ejecutar las pruebas del modelo de comandas: módulos esenciales no cargados.")
    else:
        print("Probando el Modelo de Comandas (order_model.py)...")

        test_table_id = "M01_ORD_TEST"
        test_employee_id = "MESERO01"
        test_cook_id = "COCINA01"

        test_dish_id_con_receta1 = "PLATO_CENA01"
        test_dish_id_con_receta2 = "PLATO_ALMU01"

        print(f"\n--- Asegurando datos de prueba (mesa: {test_table_id}, empleados, platos con recetas y stock) ---")

        if table_model.get_table_by_id(test_table_id):
            table_model.update_table_status(test_table_id, 'libre')
            print(f"Mesa {test_table_id} establecida a 'libre'.")
        else:
            print(f"ADVERTENCIA: Mesa de prueba {test_table_id} no existe. Creándola...")
            table_model.create_table({'id_mesa': test_table_id, 'capacidad': 2})
            print(f"Mesa {test_table_id} creada.")

        print(f"\n--- 1. Creando nueva comanda para mesa {test_table_id} por empleado {test_employee_id} ---")
        new_order_id = create_new_order(test_table_id, test_employee_id, num_people=2)
        if new_order_id:
            print(f"Nueva comanda creada con ID: {new_order_id}")
        else:
            print(f"Fallo al crear la nueva comanda para {test_table_id}.")
            sys.exit("Prueba de comanda fallida: no se pudo crear la comanda.")

        print(f"\n--- 2. Añadiendo platos a la comanda {new_order_id} ---")
        detail1_id = add_dish_to_order(new_order_id, test_dish_id_con_receta1, 1, "Bien cocido")
        if detail1_id: print(f"Plato '{test_dish_id_con_receta1}' añadido. ID Detalle: {detail1_id}")
        else: print(f"Fallo al añadir plato '{test_dish_id_con_receta1}'.")

        detail2_id = add_dish_to_order(new_order_id, test_dish_id_con_receta2, 2)
        if detail2_id: print(f"Plato '{test_dish_id_con_receta2}' añadido. ID Detalle: {detail2_id}")
        else: print(f"Fallo al añadir plato '{test_dish_id_con_receta2}'.")

        print(f"\n--- 3. Obteniendo detalles de la comanda {new_order_id} ---")
        order_details_before_kitchen = get_order_by_id(new_order_id)
        if order_details_before_kitchen and order_details_before_kitchen.get('detalles'):
            for detail in order_details_before_kitchen['detalles']:
                print(f"  Antes de cocina - DetalleID: {detail['id_detalle_comanda']}, Plato: {detail['nombre_plato']}, Estado: {detail['estado_plato']}")

        print(f"\n--- 4. Actualizando ítems a 'en preparacion' (descontará stock) ---")
        if detail1_id:
            print(f"  Procesando ítem {detail1_id} ({test_dish_id_con_receta1})...")
            update_item_result1 = update_order_item_status(detail1_id, 'en preparacion', id_employee_responsible=test_cook_id)
            if update_item_result1: print(f"  Ítem {detail1_id} actualizado a 'en preparacion'.")
            else: print(f"  FALLO al actualizar ítem {detail1_id} a 'en preparacion'. ¿Stock suficiente? ¿Receta?")

        if detail2_id:
            print(f"  Procesando ítem {detail2_id} ({test_dish_id_con_receta2})...")
            update_item_result2 = update_order_item_status(detail2_id, 'en preparacion', id_employee_responsible=test_cook_id)
            if update_item_result2: print(f"  Ítem {detail2_id} actualizado a 'en preparacion'.")
            else: print(f"  FALLO al actualizar ítem {detail2_id} a 'en preparacion'. ¿Stock suficiente? ¿Receta?")

        print(f"\n--- Detalles de la comanda {new_order_id} DESPUÉS de enviar a cocina ---")
        final_order_details = get_order_by_id(new_order_id)
        if final_order_details:
            print(f"Estado Comanda General: {final_order_details['estado_comanda']}")
            if final_order_details.get('detalles'):
                for detail in final_order_details['detalles']:
                    print(f"  Después de cocina - DetalleID: {detail['id_detalle_comanda']}, Plato: {detail['nombre_plato']}, Estado Plato: {detail['estado_plato']}")

        print("\nPruebas del Modelo de Comandas completadas.")
# app/models/order_model.py
import datetime
import sys # Para depuración si los problemas persisten

# Estructura de importación preferida para la organización de paquetes.
# Asume que este archivo (order_model.py) está en app/models/
# y que db.py está en app/ (un nivel arriba)
# y que table_model.py y menu_model.py están en app/models/ (mismo nivel)
from .. import db          # '..' Sube un nivel a la carpeta 'app' para encontrar db.py
from . import table_model  # '.' Se refiere al paquete actual ('models')
from . import menu_model   # '.' Se refiere al paquete actual ('models')

# --- Resto del código de order_model.py ---
# PEGA AQUÍ EL CONTENIDO COMPLETO DE LAS FUNCIONES DE order_model.py 
# que te proporcioné en la respuesta anterior.
# Solo se muestra el esqueleto de las funciones para brevedad, pero necesitas el cuerpo completo.

def generate_order_id():
    # ... (código de la función)
    now = datetime.datetime.now()
    unique_suffix = now.strftime("%f")[:4] 
    return f"COM-{now.strftime('%Y%m%d-%H%M%S')}-{unique_suffix}"

def create_new_order(table_id_value, employee_id_value, customer_id_value=None, num_people=1):
    # ... (código de la función)
    if not db or not table_model:
        print("Error: Módulos db o table_model no disponibles en order_model (create_new_order).")
        return None
    # ... resto de la lógica ...
    current_table_info = table_model.get_table_by_id(table_id_value)
    if not current_table_info:
        print(f"Error: Mesa '{table_id_value}' no encontrada.")
        return None
    if current_table_info.get('estado') != 'libre' and current_table_info.get('estado') != 'reservada':
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
    try:
        result = db.execute_query(order_query, order_params)
        if result is not None:
            update_table_status_result = table_model.update_table_status(table_id_value, 'ocupada')
            if update_table_status_result is not None and update_table_status_result > 0:
                print(f"Comanda '{order_id}' creada y mesa '{table_id_value}' actualizada a 'ocupada'.")
                return order_id
            else:
                print(f"Error: Comanda '{order_id}' creada, PERO falló al actualizar estado de la mesa '{table_id_value}'.")
                # Considerar rollback aquí si se implementan transacciones explícitas
                return None 
        else:
            print(f"Error al crear la nueva comanda para la mesa '{table_id_value}'.")
            return None
    except Exception as e:
        print(f"Excepción al crear comanda: {e}")
        return None


def add_dish_to_order(order_id_value, dish_id_value, quantity_value, observations_value=""):
    # ... (código de la función)
    if not db or not menu_model:
        print("Error: Módulos db o menu_model no disponibles en order_model (add_dish_to_order).")
        return None
    if quantity_value <= 0:
        print("Error: La cantidad debe ser mayor que cero.")
        return None

    dish_info = menu_model.get_dish_by_id(dish_id_value)
    if not dish_info:
        print(f"Error: Plato con ID '{dish_id_value}' no encontrado o no activo.")
        return None
    
    price_at_moment = dish_info.get('precio_venta')
    if price_at_moment is None:
        print(f"Error: No se pudo obtener el precio para el plato '{dish_id_value}'.")
        return None

    default_dish_status_in_order = 'pendiente'
    detail_query = """
    INSERT INTO DetalleComanda (id_comanda, id_plato, cantidad, precio_unitario_momento, estado_plato, observaciones_plato, hora_pedido)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    current_timestamp = datetime.datetime.now()
    detail_params = (
        order_id_value, dish_id_value, quantity_value, price_at_moment,
        default_dish_status_in_order, observations_value, current_timestamp
    )
    return db.execute_query(detail_query, detail_params)

def get_order_by_id(order_id_value):
    # ... (código de la función)
    if not db: return None
    order_info_query = "SELECT * FROM Comanda WHERE id_comanda = %s"
    order_data = db.fetch_one(order_info_query, (order_id_value,))
    if not order_data: return None

    order_details_query = """
    SELECT dc.id_detalle_comanda, dc.id_plato, p.nombre_plato, dc.cantidad, 
           dc.precio_unitario_momento, dc.subtotal_detalle, dc.estado_plato, dc.observaciones_plato
    FROM DetalleComanda dc
    JOIN Plato p ON dc.id_plato = p.id_plato
    WHERE dc.id_comanda = %s
    ORDER BY dc.id_detalle_comanda
    """
    details_data = db.fetch_all(order_details_query, (order_id_value,))
    order_data['detalles'] = details_data if details_data is not None else []
    return order_data

def get_active_orders_for_table(table_id_value):
    # ... (código de la función)
    if not db: return None
    query = """
    SELECT * FROM Comanda 
    WHERE id_mesa = %s 
    AND estado_comanda NOT IN ('facturada', 'cancelada')
    ORDER BY fecha_hora_apertura DESC
    """
    return db.fetch_all(query, (table_id_value,))

def update_order_status(order_id_value, new_status_value):
    # ... (código de la función)
    if not db or not table_model: return None
    valid_statuses = ['abierta', 'en preparacion', 'lista para servir', 'servida', 'facturada', 'cancelada']
    if new_status_value not in valid_statuses:
        print(f"Error: Estado de comanda '{new_status_value}' no es válido.")
        return None

    order_info = db.fetch_one("SELECT id_mesa FROM Comanda WHERE id_comanda = %s", (order_id_value,))
    if not order_info:
        print(f"Error: Comanda '{order_id_value}' no encontrada para actualizar estado.")
        return None
    table_id_associated = order_info.get('id_mesa')

    query = "UPDATE Comanda SET estado_comanda = %s WHERE id_comanda = %s"
    result = db.execute_query(query, (new_status_value, order_id_value))

    if result is not None and result > 0:
        if new_status_value in ['facturada', 'cancelada'] and table_id_associated:
            table_model.update_table_status(table_id_associated, 'libre')
            print(f"Comanda '{order_id_value}' actualizada a '{new_status_value}' y mesa '{table_id_associated}' marcada como 'libre'.")
        else:
            print(f"Comanda '{order_id_value}' actualizada a '{new_status_value}'.")
        return result
    print(f"No se pudo actualizar el estado de la comanda '{order_id_value}'.")
    return None

def get_active_orders_summary():
    """
    Obtiene un resumen de las comandas activas (abiertas, en preparación).
    Returns:
        dict: Un diccionario con el conteo de comandas por estado activo,
              o None si hay un error.
    """
    if not db:
        print("Error en order_model: Módulo db no disponible.")
        return None
    
    # Estados que consideramos 'activos' para el resumen del dashboard
    active_states_tuple = ('abierta', 'en preparacion', 'lista para servir')
    
    # Crear placeholders para la consulta IN
    placeholders = ', '.join(['%s'] * len(active_states_tuple))
    query_string = f"SELECT estado_comanda, COUNT(*) as cantidad FROM Comanda WHERE estado_comanda IN ({placeholders}) GROUP BY estado_comanda"
    
    results = db.fetch_all(query_string, active_states_tuple)
    
    summary = {state: 0 for state in active_states_tuple} # Inicializar todos los estados activos a 0

    if results:
        for row in results:
            summary[row['estado_comanda']] = row['cantidad']
        return summary
    elif results == []: # No hay comandas activas
        return summary # Devuelve el diccionario con ceros
    return None # Error en la consulta

def update_order_item_status(order_detail_id_value, new_item_status_value):
    # ... (código de la función)
    if not db: return None
    valid_statuses = ['pendiente', 'en preparacion', 'listo', 'entregado', 'cancelado']
    if new_item_status_value not in valid_statuses:
        print(f"Error: Estado de ítem de comanda '{new_item_status_value}' no es válido.")
        return None
    query = "UPDATE DetalleComanda SET estado_plato = %s WHERE id_detalle_comanda = %s"
    return db.execute_query(query, (new_item_status_value, order_detail_id_value))

# --- Bloque if __name__ == '__main__': para pruebas ---
# Asegúrate de pegar aquí el bloque de pruebas completo de order_model.py que te di antes.
if __name__ == '__main__':
    if not db or not table_model or not menu_model:
        print("No se pueden ejecutar las pruebas del modelo de comandas: módulos db, table_model o menu_model no cargados.")
    else:
        print("Probando el Modelo de Comandas (order_model.py)...")
        test_table_id = "M01_TEST" 
        test_employee_id = "ADMIN_TEST" 
        test_dish_id1 = "P001" 
        test_dish_id2 = "P002" 

        print(f"\n--- Asegurando que la mesa {test_table_id} esté libre ---")
        # Primero, intenta crear la mesa si no existe, para que las pruebas sean más autocontenidas
        if not table_model.get_table_by_id(test_table_id):
            print(f"Mesa de prueba {test_table_id} no encontrada, intentando crearla...")
            table_model.create_table({'id_mesa': test_table_id, 'capacidad': 2, 'pos_x': 10, 'pos_y': 10})
        
        table_model.update_table_status(test_table_id, 'libre')
        current_table_state = table_model.get_table_by_id(test_table_id)
        if current_table_state:
            print(f"Estado actual de la mesa {test_table_id}: {current_table_state.get('estado')}")
        else:
            print(f"ADVERTENCIA: La mesa de prueba {test_table_id} no se encontró o no se pudo crear. Las pruebas pueden fallar.")


        print(f"\n--- Creando nueva comanda para mesa {test_table_id} por empleado {test_employee_id} ---")
        new_order_id = create_new_order(test_table_id, test_employee_id, num_people=2)
        if new_order_id:
            print(f"Nueva comanda creada con ID: {new_order_id}")
            table_after_order = table_model.get_table_by_id(test_table_id)
            if table_after_order:
                print(f"Estado de la mesa {test_table_id} después de crear comanda: {table_after_order.get('estado')}")
        else:
            print("Fallo al crear la nueva comanda.")

        if new_order_id:
            print(f"\n--- Añadiendo platos a la comanda {new_order_id} ---")
            detail1_id = None
            detail2_id = None
            
            # Asumimos que los platos de prueba existen y están activos.
            # En un entorno de prueba real, también deberías asegurar su existencia.
            if menu_model.get_dish_by_id(test_dish_id1):
                detail1_id = add_dish_to_order(new_order_id, test_dish_id1, 2, "Sin cebolla")
                print(f"Plato {test_dish_id1} añadido. ID Detalle: {detail1_id}")
            else:
                 print(f"ADVERTENCIA: Plato de prueba {test_dish_id1} no encontrado. No se añadió.")

            if menu_model.get_dish_by_id(test_dish_id2):
                detail2_id = add_dish_to_order(new_order_id, test_dish_id2, 1)
                print(f"Plato {test_dish_id2} añadido. ID Detalle: {detail2_id}")
            else:
                print(f"ADVERTENCIA: Plato de prueba {test_dish_id2} no encontrado. No se añadió.")

            print(f"\n--- Obteniendo detalles de la comanda {new_order_id} ---")
            full_order_details = get_order_by_id(new_order_id)
            if full_order_details:
                print(f"Comanda ID: {full_order_details['id_comanda']}, Mesa: {full_order_details['id_mesa']}, Estado: {full_order_details['estado_comanda']}")
                for detail in full_order_details.get('detalles', []):
                    print(f"  - Plato: {detail['nombre_plato']} (ID: {detail['id_plato']}), Cant: {detail['cantidad']}, "
                          f"Precio: ${detail['precio_unitario_momento']:.2f}, Subtotal: ${detail['subtotal_detalle']:.2f}, "
                          f"Estado Plato: {detail['estado_plato']}")
            else:
                print(f"No se pudo obtener la comanda {new_order_id}.")

            if detail1_id: 
                print(f"\n--- Actualizando estado del ítem de detalle {detail1_id} a 'en preparacion' ---")
                update_item_result = update_order_item_status(detail1_id, 'en preparacion')
                if update_item_result:
                    print(f"Ítem {detail1_id} actualizado.")
                    updated_order_check = get_order_by_id(new_order_id) 
                    if updated_order_check and updated_order_check['detalles']:
                         for det in updated_order_check['detalles']:
                             if det['id_detalle_comanda'] == detail1_id:
                                 print(f"Nuevo estado del ítem {detail1_id}: {det['estado_plato']}")
                                 break
                else:
                    print(f"Fallo al actualizar ítem {detail1_id}.")
            
            print(f"\n--- Actualizando estado de la comanda {new_order_id} a 'en preparacion' ---")
            update_order_result = update_order_status(new_order_id, 'en preparacion')
            if update_order_result:
                print(f"Comanda {new_order_id} actualizada.")
                updated_order_status_check = get_order_by_id(new_order_id)
                if updated_order_status_check:
                    print(f"Nuevo estado de la comanda {new_order_id}: {updated_order_status_check['estado_comanda']}")
            else:
                print(f"Fallo al actualizar comanda {new_order_id}.")

            print(f"\n--- Actualizando estado de la comanda {new_order_id} a 'facturada' (libera la mesa) ---")
            final_status_result = update_order_status(new_order_id, 'facturada')
            if final_status_result:
                print(f"Comanda {new_order_id} marcada como 'facturada'.")
                table_after_billing = table_model.get_table_by_id(test_table_id)
                if table_after_billing:
                    print(f"Estado de la mesa {test_table_id} después de facturar: {table_after_billing.get('estado')}")
            else:
                print(f"Fallo al marcar comanda {new_order_id} como 'facturada'.")

        print(f"\n--- Obteniendo comandas activas para la mesa {test_table_id} ---")
        active_orders = get_active_orders_for_table(test_table_id)
        if active_orders is not None:
            if active_orders:
                print(f"Comandas activas encontradas para la mesa {test_table_id}:")
                for order in active_orders:
                    print(f"  ID: {order['id_comanda']}, Estado: {order['estado_comanda']}")
            else:
                print(f"No hay comandas activas para la mesa {test_table_id}.")
        else:
            print(f"Error al obtener comandas activas para la mesa {test_table_id}.")

        print("\nPruebas del Modelo de Comandas completadas.")


# app/models/supplier_model.py
import datetime # Aunque no se usa directamente aquí, es bueno tenerlo por si se añaden timestamps

# Ajusta las rutas de importación según tu estructura de proyecto.
try:
    from .. import db # Si db.py está en la carpeta 'app' (un nivel arriba de 'models')
except ImportError:
    # Fallback si la estructura es diferente o se ejecuta directamente
    # y 'app' está en PYTHONPATH o db.py está en el mismo nivel que 'models' (menos común)
    try:
        import db
    except ImportError:
        print("Error CRÍTICO: No se pudo importar el módulo db.py en supplier_model.py.")
        print("Asegúrate de que db.py esté en la carpeta 'app' y que los __init__.py estén en su lugar.")
        db = None

def create_supplier(supplier_data_dict):
    """
    Crea un nuevo proveedor en la base de datos.

    Args:
        supplier_data_dict (dict): Un diccionario con los datos del proveedor.
            Campos requeridos: 'id_proveedor', 'nombre'.
            Campos opcionales: 'telefono', 'correo', 'producto_suministra'.
    Returns:
        El resultado de db.execute_query (ej. contador de filas afectadas o ID si aplica)
        o None si hay un error o el módulo db no está disponible.
    """
    if not db:
        print("Error en el modelo (supplier_model): Módulo db no disponible.")
        return None

    required_fields = ['id_proveedor', 'nombre']
    for field in required_fields:
        if field not in supplier_data_dict or not supplier_data_dict[field]:
            print(f"Error de validación en el modelo: El campo '{field}' es obligatorio para crear un proveedor.")
            return None
            
    query_string = """
    INSERT INTO Proveedores (id_proveedor, nombre, telefono, correo, producto_suministra)
    VALUES (%s, %s, %s, %s, %s)
    """
    params = (
        supplier_data_dict['id_proveedor'],
        supplier_data_dict['nombre'],
        supplier_data_dict.get('telefono'), # .get() para campos opcionales, devuelve None si no están
        supplier_data_dict.get('correo'),
        supplier_data_dict.get('producto_suministra')
    )
    
    try:
        result = db.execute_query(query_string, params)
        if result is not None:
            print(f"Proveedor '{supplier_data_dict['id_proveedor']}' creado/procesado exitosamente.")
        else:
            # Esto podría ocurrir si db.execute_query devuelve None en un error no capturado por excepción MySQL
            print(f"No se pudo crear el proveedor '{supplier_data_dict['id_proveedor']}' (db.execute_query devolvió None).")
        return result
    except Exception as e: # Captura cualquier excepción de la BD o de db.execute_query
        print(f"Excepción al crear proveedor '{supplier_data_dict['id_proveedor']}': {e}")
        # Podrías querer registrar 'e' más detalladamente en un log de la aplicación.
        return None


def get_supplier_by_id(supplier_id_value):
    """
    Obtiene un proveedor por su ID.

    Args:
        supplier_id_value (str): El ID del proveedor a buscar.

    Returns:
        dict: Los datos del proveedor si se encuentra, None en caso contrario o si hay error.
    """
    if not db:
        print("Error en el modelo (supplier_model): Módulo db no disponible.")
        return None
    query_string = "SELECT id_proveedor, nombre, telefono, correo, producto_suministra FROM Proveedores WHERE id_proveedor = %s"
    return db.fetch_one(query_string, (supplier_id_value,))

def get_all_suppliers_list():
    """
    Obtiene una lista de todos los proveedores.

    Returns:
        list: Una lista de diccionarios, cada uno representando un proveedor.
              Devuelve una lista vacía si no hay proveedores.
              None si hay un error en la consulta o el módulo db no está disponible.
    """
    if not db:
        print("Error en el modelo (supplier_model): Módulo db no disponible.")
        return None
    query_string = "SELECT id_proveedor, nombre, telefono, correo, producto_suministra FROM Proveedores ORDER BY nombre"
    return db.fetch_all(query_string)

def update_supplier_details(supplier_id_value, data_to_update_dict):
    """
    Actualiza la información de un proveedor existente.

    Args:
        supplier_id_value (str): El ID del proveedor a actualizar.
        data_to_update_dict (dict): Un diccionario con los campos a actualizar y sus nuevos valores.
                                   Campos permitidos: 'nombre', 'telefono', 'correo', 'producto_suministra'.
    Returns:
        int: El número de filas afectadas, o None si hay un error. 0 si no hay datos válidos para actualizar.
    """
    if not db:
        print("Error en el modelo (supplier_model): Módulo db no disponible.")
        return None
    if not data_to_update_dict:
        print("Modelo (supplier_model): No se proporcionaron datos para actualizar.")
        return 0 

    # Campos permitidos para actualización directa (nombres de columnas en la BD)
    allowed_fields_for_update = {'nombre', 'telefono', 'correo', 'producto_suministra'} 
    
    set_clauses_list = []
    parameters_list = []

    for key, value in data_to_update_dict.items():
        if key in allowed_fields_for_update:
            set_clauses_list.append(f"`{key}` = %s") 
            parameters_list.append(value)
        else:
            print(f"Advertencia en el modelo (supplier_model): El campo '{key}' no se puede actualizar o no es permitido.")

    if not set_clauses_list:
        print("Modelo (supplier_model): Ningún campo válido para actualizar fue proporcionado.")
        return 0

    query_string = f"UPDATE Proveedores SET {', '.join(set_clauses_list)} WHERE id_proveedor = %s"
    parameters_list.append(supplier_id_value)
    
    return db.execute_query(query_string, tuple(parameters_list))

def delete_supplier_by_id(supplier_id_value):
    """
    Elimina un proveedor de la base de datos.
    PRECAUCIÓN: Considerar si hay productos o órdenes de compra asociadas.
    La base de datos debería tener restricciones FK (ON DELETE RESTRICT o SET NULL)
    en tablas como Producto (proveedor_principal_ref) u OrdenCompra.

    Args:
        supplier_id_value (str): El ID del proveedor a eliminar.

    Returns:
        int: El número de filas afectadas, o None si hay un error.
    """
    if not db:
        print("Error en el modelo (supplier_model): Módulo db no disponible.")
        return None
    
    # Antes de eliminar, podrías querer verificar si este proveedor está referenciado
    # en otras tablas (ej. Producto.proveedor_principal_ref, OrdenCompra.id_proveedor).
    # Si las FK tienen ON DELETE RESTRICT, la BD impedirá la eliminación si hay referencias.
    # Si tienen ON DELETE SET NULL, las referencias se anularán.

    query_string = "DELETE FROM Proveedores WHERE id_proveedor = %s"
    return db.execute_query(query_string, (supplier_id_value,))

# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    if not db:
        print("No se pueden ejecutar las pruebas del modelo de proveedores: módulo db no cargado.")
    else:
        print("Probando el Modelo de Proveedores (supplier_model.py)...")

        test_supplier_id = "PROV_TEST_001"
        test_supplier_id2 = "PROV_TEST_002"

        # 0. Limpieza previa de datos de prueba
        print(f"\n--- Limpiando proveedores de prueba {test_supplier_id} y {test_supplier_id2} si existen ---")
        delete_supplier_by_id(test_supplier_id)
        delete_supplier_by_id(test_supplier_id2)

        # 1. Crear un nuevo proveedor
        print(f"\n--- Creando proveedor: {test_supplier_id} ---")
        supplier1_data = {
            'id_proveedor': test_supplier_id,
            'nombre': 'Proveedor de Frutas Frescas XYZ',
            'telefono': '3001234567',
            'correo': 'frutasxyz@example.com',
            'producto_suministra': 'Manzanas, Bananos, Naranjas'
        }
        creation_result1 = create_supplier(supplier1_data)
        if creation_result1 is not None:
            print(f"Proveedor {test_supplier_id} procesado (resultado: {creation_result1}).")
            created_supplier1 = get_supplier_by_id(test_supplier_id)
            print(f"Verificación: {created_supplier1}")
        else:
            print(f"Fallo al crear proveedor {test_supplier_id}.")

        # Crear otro proveedor para la lista
        supplier2_data = {
            'id_proveedor': test_supplier_id2,
            'nombre': 'Carnes La Finca SAS',
            'telefono': '3109876543',
            'correo': 'carneslafinca@example.com',
            'producto_suministra': 'Res, Pollo, Cerdo'
        }
        create_supplier(supplier2_data)

        # 2. Listar todos los proveedores
        print("\n--- Listando todos los proveedores ---")
        all_suppliers = get_all_suppliers_list()
        if all_suppliers is not None:
            if all_suppliers:
                for sup in all_suppliers:
                    print(f"  ID: {sup['id_proveedor']}, Nombre: {sup['nombre']}, Productos: {sup.get('producto_suministra', 'N/A')}")
            else:
                print("No hay proveedores para listar.")
        else:
            print("Error al listar proveedores.")

        # 3. Obtener el proveedor creado
        print(f"\n--- Obteniendo proveedor: {test_supplier_id} ---")
        supplier_details = get_supplier_by_id(test_supplier_id)
        if supplier_details:
            print(f"Detalles encontrados: {supplier_details}")
        else:
            print(f"Proveedor {test_supplier_id} no encontrado (o hubo un error en la obtención, o no se creó).")

        # 4. Actualizar información del proveedor
        if supplier_details: # Solo intentar actualizar si el proveedor existe
            print(f"\n--- Actualizando proveedor: {test_supplier_id} ---")
            update_payload = {
                'nombre': 'Proveedor de Frutas Frescas XYZ (Actualizado)',
                'correo': 'ventas@frutasxyz.com',
                'producto_suministra': 'Manzanas Gala, Bananos Criollos, Naranjas Valencia, Fresas'
            }
            updated_count = update_supplier_details(test_supplier_id, update_payload)
            if updated_count is not None:
                print(f"Resultado de la actualización (filas afectadas): {updated_count}")
                if updated_count > 0:
                    updated_supplier_check = get_supplier_by_id(test_supplier_id)
                    print(f"Datos después de actualizar: {updated_supplier_check}")
                elif updated_count == 0:
                     print(f"Ninguna fila fue actualizada para {test_supplier_id}. ¿El ID es correcto y los datos son diferentes?")
            else:
                print(f"Error al actualizar proveedor {test_supplier_id} (el modelo devolvió None).")

        # 5. Eliminar un proveedor (el segundo creado)
        if get_supplier_by_id(test_supplier_id2):
            print(f"\n--- Eliminando proveedor: {test_supplier_id2} ---")
            deleted_count = delete_supplier_by_id(test_supplier_id2)
            if deleted_count is not None:
                print(f"Resultado de la eliminación (filas afectadas): {deleted_count}")
                if deleted_count > 0:
                    deleted_supplier_check = get_supplier_by_id(test_supplier_id2)
                    if not deleted_supplier_check:
                        print(f"Proveedor {test_supplier_id2} eliminado correctamente.")
                    else:
                        print(f"Error: Proveedor {test_supplier_id2} aún encontrado después del intento de eliminación.")
            else:
                print(f"Error al eliminar proveedor {test_supplier_id2} (el modelo devolvió None).")
        
        print("\nPruebas del Modelo de Proveedores completadas.")

# app/models/supplier_model.py
import datetime
import uuid 
import random 
import string 
import os # Necesario si usas os.path para algo, o si db.py lo necesita indirectamente
import traceback # Para imprimir tracebacks completos

# Ajusta la ruta de importación para db.py según tu estructura
try:
    from app import db # Si db.py está en la carpeta app/
except ImportError:
    try:
        from .. import db # Si este archivo está en app/models/ y db.py en app/
    except ImportError:
        try:
            import db # Si db.py está en una ruta accesible por PYTHONPATH
        except ImportError as e:
            print(f"Error CRÍTICO: No se pudo importar db.py en supplier_model.py: {e}")
            db = None


def generate_supplier_id(length=10):
    """Genera un ID único para un nuevo proveedor. Ejemplo: PROV-ABC12"""
    # Usaremos "PROV-" como prefijo, que son 5 caracteres.
    # Los caracteres restantes serán aleatorios.
    chars_to_generate = length - 5
    if chars_to_generate < 1: # Asegurar que haya espacio para caracteres aleatorios
        chars_to_generate = 5 # Default a 5 caracteres aleatorios si length es muy pequeño
        
    characters = string.ascii_uppercase + string.digits
    random_id_part = ''.join(random.choice(characters) for i in range(chars_to_generate))
    return f"PROV-{random_id_part}"


def create_supplier(supplier_data_dict):
    """
    Crea un nuevo proveedor en la base de datos.
    El ID del proveedor siempre se genera aquí.
    Devuelve el ID del proveedor creado o None si falla.
    """
    if not db:
        print("Error en el modelo (supplier_model): Módulo db no disponible.")
        return None

    generated_id = generate_supplier_id()
    # Asegurarse de que el diccionario que se usa para los parámetros tenga el ID generado
    # No modificamos el diccionario original si se pasa por referencia, creamos uno nuevo para params.
    
    nombre_proveedor = supplier_data_dict.get('nombre')
    if not nombre_proveedor: # El nombre es el único campo realmente obligatorio desde la vista ahora
        print(f"Error de validación en el modelo: El campo 'nombre' es obligatorio para crear un proveedor.")
        return None
            
    query_string = """
    INSERT INTO Proveedores (id_proveedor, nombre, telefono, correo, producto_suministra)
    VALUES (%s, %s, %s, %s, %s)
    """
    params = (
        generated_id, # Usar el ID generado
        nombre_proveedor,
        supplier_data_dict.get('telefono'),
        supplier_data_dict.get('correo'),
        supplier_data_dict.get('producto_suministra')
    )
    
    try:
        # db.execute_query debería devolver el lastrowid o rowcount.
        # Para INSERTs sin AUTO_INCREMENT PK, rowcount (1 si es exitoso) es más útil.
        # O simplemente verificar que no devuelva None.
        result_from_db = db.execute_query(query_string, params)
        
        if result_from_db is not None: # Asumimos que None indica fallo
            print(f"Proveedor '{generated_id}' ('{nombre_proveedor}') creado exitosamente.")
            return generated_id # Devolver el ID generado
        else:
            print(f"No se pudo crear el proveedor '{nombre_proveedor}' (ID intentado: {generated_id}). db.execute_query devolvió None.")
            return None
    except Exception as e:
        print(f"Excepción al crear proveedor '{nombre_proveedor}' (ID intentado: {generated_id}): {e}")
        traceback.print_exc()
        return None

def get_supplier_by_id(supplier_id_value):
    """ Obtiene un proveedor por su ID. """
    if not db: return None
    query_string = "SELECT id_proveedor, nombre, telefono, correo, producto_suministra FROM Proveedores WHERE id_proveedor = %s"
    return db.fetch_one(query_string, (supplier_id_value,))

def get_all_suppliers_list():
    """ Obtiene una lista de todos los proveedores. """
    if not db: return None
    query_string = "SELECT id_proveedor, nombre, telefono, correo, producto_suministra FROM Proveedores ORDER BY nombre"
    return db.fetch_all(query_string)

def update_supplier_details(supplier_id_value, data_to_update_dict):
    """ Actualiza la información de un proveedor existente. """
    if not db:
        print("Error en el modelo (supplier_model): Módulo db no disponible.")
        return None
    if not supplier_id_value:
        print("Error en el modelo (supplier_model): Se requiere ID de proveedor para actualizar.")
        return None # O 0 si prefieres indicar 0 filas afectadas
    if not data_to_update_dict:
        print("Modelo (supplier_model): No se proporcionaron datos para actualizar.")
        return 0 

    allowed_fields_for_update = {'nombre', 'telefono', 'correo', 'producto_suministra'} 
    set_clauses_list = []
    parameters_list = []

    for key, value in data_to_update_dict.items():
        if key in allowed_fields_for_update:
            set_clauses_list.append(f"`{key}` = %s") 
            parameters_list.append(value)

    if not set_clauses_list:
        print("Modelo (supplier_model): Ningún campo válido para actualizar fue proporcionado.")
        return 0

    query_string = f"UPDATE Proveedores SET {', '.join(set_clauses_list)} WHERE id_proveedor = %s"
    parameters_list.append(supplier_id_value)
    
    return db.execute_query(query_string, tuple(parameters_list))

def delete_supplier_by_id(supplier_id_value):
    """ Elimina un proveedor de la base de datos. """
    if not db: return None
    query_string = "DELETE FROM Proveedores WHERE id_proveedor = %s"
    return db.execute_query(query_string, (supplier_id_value,))

# --- Ejemplo de uso y pruebas ---
if __name__ == '__main__':
    if not db:
        print("No se pueden ejecutar las pruebas del modelo de proveedores: módulo db no cargado.")
    else:
        print("Probando el Modelo de Proveedores (supplier_model.py)...")

        # Prueba de generación de ID
        print(f"ID de proveedor generado de ejemplo: {generate_supplier_id()}")
        print(f"ID de proveedor generado de ejemplo (largo 12): {generate_supplier_id(12)}")


        test_supplier_nombre = "Proveedor de Prueba AutoID"
        test_supplier_id_creado = None

        # 1. Crear un nuevo proveedor (ID se autogenerará)
        print(f"\n--- Creando proveedor: {test_supplier_nombre} ---")
        supplier_data = {
            'nombre': test_supplier_nombre,
            'telefono': '123000111',
            'correo': 'prueba.autoid@example.com',
            'producto_suministra': 'Artículos de prueba con ID automático'
        }
        test_supplier_id_creado = create_supplier(supplier_data)
        if test_supplier_id_creado:
            print(f"Proveedor '{test_supplier_nombre}' creado con ID: {test_supplier_id_creado}.")
            created_supplier = get_supplier_by_id(test_supplier_id_creado)
            print(f"Verificación: {created_supplier}")
        else:
            print(f"Fallo al crear proveedor '{test_supplier_nombre}'.")

        # 2. Listar todos los proveedores
        print("\n--- Listando todos los proveedores ---")
        all_suppliers = get_all_suppliers_list()
        if all_suppliers is not None:
            if all_suppliers:
                for sup in all_suppliers:
                    print(f"  ID: {sup['id_proveedor']}, Nombre: {sup['nombre']}")
            else:
                print("No hay proveedores para listar.")
        else:
            print("Error al listar proveedores.")

        # 3. Actualizar información del proveedor (si se creó)
        if test_supplier_id_creado:
            print(f"\n--- Actualizando proveedor: {test_supplier_id_creado} ---")
            update_payload = {
                'nombre': f"{test_supplier_nombre} (Actualizado)",
                'correo': 'ventas.prueba.autoid@example.com'
            }
            updated_count = update_supplier_details(test_supplier_id_creado, update_payload)
            if updated_count is not None:
                print(f"Resultado de la actualización (filas afectadas): {updated_count}")
                if updated_count > 0:
                    updated_supplier_check = get_supplier_by_id(test_supplier_id_creado)
                    print(f"Datos después de actualizar: {updated_supplier_check}")
            else:
                print(f"Error al actualizar proveedor {test_supplier_id_creado}.")

        # 4. Eliminar el proveedor de prueba (si se creó)
        if test_supplier_id_creado:
            print(f"\n--- Eliminando proveedor: {test_supplier_id_creado} ---")
            deleted_count = delete_supplier_by_id(test_supplier_id_creado)
            if deleted_count is not None:
                print(f"Resultado de la eliminación (filas afectadas): {deleted_count}")
                if deleted_count > 0:
                    deleted_supplier_check = get_supplier_by_id(test_supplier_id_creado)
                    if not deleted_supplier_check:
                        print(f"Proveedor {test_supplier_id_creado} eliminado correctamente.")
            else:
                print(f"Error al eliminar proveedor {test_supplier_id_creado}.")
        
        print("\nPruebas del Modelo de Proveedores completadas.")